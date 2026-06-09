from master_agent import build_master_agent

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

    # 执行流程
    result = ops_agent.invoke(TEST_ALARM)

    # 输出结果
    print(f"\n✅ 流程状态：{result['process_stage']}")
    print(f"🔍 故障根因：{result['root_cause']}")
    print(f"🛠️ 修复方案：{result['fix_actions']}")

    print("\n📜 全流程审计日志：")
    for log in result["audit_logs"]:
        print(f"- {log}")