from state import OpsAgentState
from settings import TROUBLE_KEYWORDS, DEFAULT_TROUBLESHOOT_PLAN

# ====================== React 思考逻辑 ======================
def react_node(state: OpsAgentState) -> OpsAgentState:
    """React模式：思考分析问题，做出决策"""
    user_input = state["user_input"].lower()
    thought = ""
    decision = "qa"

    # 判断故障排查
    if any(k in user_input for k in TROUBLE_KEYWORDS):
        thought = f"【思考】用户问题：{user_input} → 判断为【服务器故障排查】，需要生成分步执行计划处理"
        decision = "troubleshoot"
    else:
        thought = f"【思考】用户问题：{user_input} → 判断为【运维知识问答】，直接检索RAG知识库"
        decision = "qa"

    state["thought"] = thought
    state["decision"] = decision
    return state

# ====================== Planner 规划逻辑 ======================
def plan_node(state: OpsAgentState) -> OpsAgentState:
    """生成故障排查执行计划"""
    state["plan"] = DEFAULT_TROUBLESHOOT_PLAN
    state["current_step"] = 0
    state["execution_results"] = []
    state["is_plan_completed"] = False
    return state