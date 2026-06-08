from typing import TypedDict, Literal, List, Dict

class OpsAgentState(TypedDict):
    """IT运维Agent全局状态（React + Plan&Execute）"""
    # 基础输入
    user_input: str
    # React 思考过程
    thought: str
    # 决策类型
    decision: Literal["qa", "troubleshoot"]
    # Plan 执行计划
    plan: List[str]
    # Execute 执行状态
    current_step: int
    execution_results: List[Dict]
    is_plan_completed: bool
    # 最终输出
    final_answer: str