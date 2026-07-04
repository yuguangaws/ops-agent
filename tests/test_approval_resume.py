"""验证 master_agent 的高危操作中断/恢复机制。

背景：修复前 `workflow.compile(interrupt_before=["human_approval"])` 没有配
checkpointer，LangGraph 在无 checkpointer 时只会在中断点静默截断整张图并返回，
execute_fix / verify_result / reflection 永远不会执行，也没有任何办法恢复。
这里用可控的假 LLM 替换真实的智谱调用，构造一条必然判定为高危的告警，验证：
  1. 高危告警会在 human_approval 节点前真正中断（而不是无声跑完/丢弃后续节点）；
  2. 中断状态可以通过 get_state(config).next 观测到；
  3. 写入 approval_status 并调用 resume_with_approval 恢复后，
     execute_fix -> verify_result -> reflection 能完整跑完。
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.agent import master_agent
from src.agent.core.state import OpsState


class _FakeLLM:
    """伪造 LLM：不发真实网络请求，行为完全可控，保证测试确定性。"""

    def invoke(self, prompt):
        # 对应 sub_agent.py 里 ReAct Think 阶段的 llm.invoke 调用，返回值当前未被使用
        return type("Msg", (), {"content": ""})()

    def stream(self, prompt):
        # 对应 aggregate_root_cause 里的 llm.stream，一次性 yield 一段固定的高危根因 JSON
        payload = (
            "```json\n"
            "{"
            '"root_cause": "数据库主库磁盘写满导致连接被拒绝",'
            '"phenomenon_summary": "订单服务大量5xx，数据库拒绝新连接",'
            '"impact_scope": {"level": "P1", "description": "订单服务不可用"},'
            '"fix_scheme": {'
            '"immediate": "清理磁盘并重启数据库实例",'
            '"permanent": "扩容磁盘并接入容量告警",'
            '"rollback": "回滚清理脚本"'
            "},"
            '"verify_method": "观察数据库连接数与订单服务5xx率恢复",'
            '"is_high_risk": true,'
            '"risk_desc": "重启数据库实例属于高危操作",'
            '"knowledge_reference": [],'
            '"supplement_check": "无"'
            "}\n```"
        )
        yield type("Chunk", (), {"content": payload})()


def _init_state(alarm_id: str) -> OpsState:
    return OpsState(
        alarm_id=alarm_id,
        alarm_content="生产环境订单数据库磁盘写满，服务5xx报错",
        alarm_level="P1",
        affected_assets=["db-01"],
        domains_to_check=[],
        domain_results={},
        root_cause="",
        fix_actions=[],
        approval_status="pending",
        is_high_risk=False,
        process_stage="初始化",
        audit_logs=[],
    )


@patch(
    "src.agent.master_agent.ops_rag_agent.retrieve_context",
    return_value="【参考文档1】来源：disk_high_usage.md\n内容：磁盘写满优先清理日志并扩容",
)
@patch("src.agent.sub_agent.llm", new=_FakeLLM())
@patch("src.agent.master_agent.llm", new=_FakeLLM())
def test_high_risk_alarm_interrupts_then_resumes_after_approval(mock_rag):
    workflow = master_agent.build_master_agent()
    config = {"configurable": {"thread_id": "ALARM-TEST-APPROVAL-001"}}

    # ---- 第一次 invoke：应在 human_approval 前中断，execute_fix 之后的节点都不该跑 ----
    first_result = workflow.invoke(_init_state("ALARM-TEST-APPROVAL-001"), config=config)

    assert first_result["is_high_risk"] is True
    assert workflow.get_state(config).next == ("human_approval",), (
        "高危告警应停在 human_approval 节点前等待审批，而不是无声跑完整张图"
    )
    joined_logs = "\n".join(first_result["audit_logs"])
    assert "验证完成" not in joined_logs
    assert "复盘完成" not in joined_logs
    assert first_result["process_stage"] == "研判完成"

    # ---- 人工审批通过后恢复执行 ----
    final_result = master_agent.resume_with_approval(workflow, config, approved=True)

    assert workflow.get_state(config).next == (), "审批通过后图应跑完，不应再有待执行节点"
    assert final_result["approval_status"] == "approved"
    assert final_result["process_stage"] == "复盘完成"
    final_logs = "\n".join(final_result["audit_logs"])
    assert "验证完成" in final_logs
    assert "复盘完成" in final_logs
    assert "审批驳回" not in final_logs

    # ---- parallel_check 真并行修复的副作用验证：db/app/logs 三个领域都应有独立排查结果 ----
    assert set(final_result["domain_results"].keys()) == {"db", "app", "logs"}
    for domain, result in final_result["domain_results"].items():
        assert result, f"{domain} 领域排查结果不应为空"


@patch(
    "src.agent.master_agent.ops_rag_agent.retrieve_context",
    return_value="暂无相关运维知识库内容",
)
@patch("src.agent.sub_agent.llm", new=_FakeLLM())
@patch("src.agent.master_agent.llm", new=_FakeLLM())
def test_high_risk_alarm_stops_fix_when_rejected(mock_rag):
    """驳回分支：execute_fix 应识别 approval_status != approved 并终止修复，不应再执行 mock_fix_service。"""
    workflow = master_agent.build_master_agent()
    config = {"configurable": {"thread_id": "ALARM-TEST-APPROVAL-002"}}

    workflow.invoke(_init_state("ALARM-TEST-APPROVAL-002"), config=config)
    final_result = master_agent.resume_with_approval(workflow, config, approved=False)

    assert final_result["approval_status"] == "rejected"
    assert any("审批驳回，终止修复" in log for log in final_result["audit_logs"])
    assert not any("修复执行" in log for log in final_result["audit_logs"])
    # 驳回也应继续跑完 verify_result / reflection（当前流程设计如此，只是不执行真正的修复动作）
    assert final_result["process_stage"] == "复盘完成"
