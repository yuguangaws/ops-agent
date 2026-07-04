import os
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# 修正：导入构建函数，而非不存在的MasterAgent类
from src.agent.master_agent import build_master_agent
from src.agent.core.state import OpsState


def test_master_agent():
    print("=" * 70)
    print("【Master Agent 全链路端到端测试】")
    print("=" * 70)

    try:
        # 1. 构建主Agent工作流
        master_workflow = build_master_agent()
        print("✅ 主Agent工作流构建成功")

        # 2. 构造完整初始状态（所有用到的字段必须初始化，避免KeyError）
        init_state = OpsState(
            alarm_id="ALARM-20260617-001",
            alarm_content="服务器CPU使用率持续超过90%，应用接口响应变慢",
            affected_assets=["test-node-01"],
            domains_to_check=[],
            domain_results={},
            audit_logs=[],
            process_stage="待处理",
            root_cause="",
            fix_actions=[],
            is_high_risk=False,  # 设为False走普通修复分支，无需人工中断
            approval_status="pending"
        )
        print("✅ 初始状态构造完成")

        # 3. 执行全链路流程
        # checkpointer 需要一个 thread_id 来定位/持久化本次执行状态
        config = {"configurable": {"thread_id": init_state["alarm_id"]}}
        print("\n▶ 开始执行故障排查全流程...")
        final_state = master_workflow.invoke(init_state, config=config)

        # 4. 打印执行结果
        print("\n" + "=" * 70)
        print("【执行结果汇总】")
        print("=" * 70)
        print(f"处理阶段：{final_state['process_stage']}")
        print(f"排查领域：{final_state['domains_to_check']}")

        print("\n【审计日志】")
        for log in final_state["audit_logs"]:
            print(f"  - {log}")

        print("\n【根因分析结果】")
        print(f"  {final_state['root_cause'][:200]}...")

        print("\n【修复动作】")
        print(f"  {final_state['fix_actions']}")

        print("\n✅ 全链路测试执行通过")
        return True

    except Exception as e:
        print(f"\n❌ 全链路测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_master_agent()