from .master_agent import build_master_agent, resume_with_approval
import warnings
warnings.filterwarnings("ignore", module="jwt")

# ==================== 初始化Agent ====================
ops_agent = build_master_agent()

# ==================== 模拟生产告警 ====================
TEST_ALARM = {
    "alarm_id": "OPS20250520001",
    "alarm_content": "生产环境订单服务异常，CPU95%，服务无响应",
    "alarm_level": "P1",
    "affected_assets": ["order-01", "order-02"],
    "domains_to_check": [],
    "domain_results": {},
    "root_cause": "",
    "fix_actions": [],
    "approval_status": "pending",
    "is_high_risk": False,
    "process_stage": "初始化",
    "audit_logs": []
}

# ==================== 启动运行 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("🔥 中大型智能运维Agent 启动成功")
    print("=" * 60)

    # 执行流程。checkpointer 需要一个 thread_id 来定位/持久化本次告警的执行状态，
    # 后续如需在 human_approval 中断处恢复，也要用同一个 config。
    config = {"configurable": {"thread_id": TEST_ALARM["alarm_id"]}}
    result = ops_agent.invoke(TEST_ALARM, config=config)

    # 高危操作会在 human_approval 节点前中断，此时图还没跑完（execute_fix 及之后
    # 的节点均未执行），需要人工审批后显式恢复
    if ops_agent.get_state(config).next:
        print("\n⚠️ 检测到高危操作，等待人工审批...")
        approved = True  # CLI 演示：模拟审批通过；真实场景应接入人工审批入口
        print(f"👤 审批结果：{'通过' if approved else '驳回'}")
        result = resume_with_approval(ops_agent, config, approved=approved)

    # 输出结果
    print(f"\n✅ 流程状态：{result['process_stage']}")
    print(f"🔍 故障根因：{result['root_cause']}")
    print(f"🛠️ 修复方案：{result['fix_actions']}")

    print("\n📜 全流程审计日志：")
    for log in result["audit_logs"]:
        print(f"- {log}")