from typing import TypedDict, List, Dict

class OpsState(TypedDict):
    """
    智能运维Agent 全局状态
    贯穿：告警→排查→研判→修复→验证→复盘 全流程
    """
    # 告警基础信息
    alarm_id: str
    alarm_content: str
    alarm_level: str
    affected_assets: List[str]

    # 任务配置
    domains_to_check: List[str]  # 需要排查的领域：host/db/app/logs

    # 排查结果
    domain_results: Dict[str, str]  # 各领域排查结果
    root_cause: str  # 故障根因
    fix_actions: List[str]  # 修复方案

    # 人机协同
    approval_status: str  # pending/approved/rejected
    is_high_risk: bool  # 是否高危操作

    # 流程状态
    process_stage: str
    audit_logs: List[str]  # 全流程审计日志