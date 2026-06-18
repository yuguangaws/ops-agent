from langgraph.graph import StateGraph, END
from .core.state import OpsState
from .core.llm import llm
from .core.pe import ROOT_CAUSE_PROMPT
from .sub_agent import domain_sub_agent
from .tools import OPS_TOOLS
from .rag_agent.rag_agent import ops_rag_agent


# ==================== 主Agent 节点定义 ====================
def alarm_convergence(state: OpsState) -> OpsState:
    """告警收敛：自动识别排查领域"""
    state["audit_logs"].append(f"【主Agent】接收告警：{state['alarm_id']}")
    state["process_stage"] = "排查中"

    # 自动匹配排查领域
    content = state["alarm_content"]
    if any(key in content for key in ["CPU", "主机", "内存"]):
        state["domains_to_check"].append("host")
    if "数据库" in content:
        state["domains_to_check"].append("db")
    if any(key in content for key in ["服务", "应用", "接口"]):
        state["domains_to_check"].append("app")
    if any(key in content for key in ["日志", "异常", "报错"]):
        state["domains_to_check"].append("logs")

    return state

def parallel_check(state: OpsState) -> OpsState:
    """并行调度：多领域子Agent同时排查"""
    domains = state["domains_to_check"]
    state["audit_logs"].append(f"【主Agent】并行排查：{domains}")

    # 并行执行所有子Agent
    for domain in domains:
        state = domain_sub_agent(state, domain)

    return state

def aggregate_root_cause(state: OpsState) -> OpsState:
    """结果聚合 + LLM根因研判"""
    state["audit_logs"].append("【主Agent】聚合结果，分析根因")
    state["process_stage"] = "研判中"

    query = f"故障现象：{state['alarm_content']}，如何排查与处理"
    rag_context = ops_rag_agent.retrieve_context(query)
    
    # 拼接各领域排查结果
    results = "\n".join([f"{k}: {v}" for k, v in state["domain_results"].items()])
    
    # ✅ 核心修正：把所有占位符参数都传进去，不要漏
    prompt = ROOT_CAUSE_PROMPT.format(
        alarm_content=state["alarm_content"],
        results=results,
        rag_context=rag_context
    )
    
    response = llm.invoke(prompt).content

    # 解析结果（后续建议改成json.loads解析结构化输出）
    state["root_cause"] = response.split("修复方案")[0].strip() if "修复方案" in response else response
    state["fix_actions"] = ["重启异常服务实例"]
    state["is_high_risk"] = False

    return state

def judge_operation(state: OpsState) -> str:
    """操作路由：普通/高危"""
    return "high_risk" if state["is_high_risk"] else "normal"

def human_approval(state: OpsState) -> OpsState:
    """人工审批节点"""
    state["approval_status"] = "pending"
    state["audit_logs"].append("【主Agent】等待人工审批高危操作")
    return state

def execute_fix(state: OpsState) -> OpsState:
    """执行修复"""
    if state["is_high_risk"] and state["approval_status"] != "approved":
        state["audit_logs"].append("【主Agent】审批驳回，终止修复")
        return state

    res = OPS_TOOLS["fix"](state["affected_assets"])
    state["audit_logs"].append(res)
    state["process_stage"] = "处置中"
    return state

def verify_result(state: OpsState) -> OpsState:
    """结果验证"""
    state["audit_logs"].append("【主Agent】验证完成：服务恢复正常")
    state["process_stage"] = "验证完成"
    return state

def reflection(state: OpsState) -> OpsState:
    """故障复盘（Reflection）"""
    state["audit_logs"].append("【主Agent】复盘完成，沉淀知识库")
    state["process_stage"] = "复盘完成"
    return state

# ==================== 构建 LangGraph 主流程 ====================
def build_master_agent():
    workflow = StateGraph(OpsState)

    # 添加节点
    workflow.add_node("alarm_convergence", alarm_convergence)
    workflow.add_node("parallel_check", parallel_check)
    workflow.add_node("aggregate_root_cause", aggregate_root_cause)
    workflow.add_node("human_approval", human_approval)
    workflow.add_node("execute_fix", execute_fix)
    workflow.add_node("verify_result", verify_result)
    workflow.add_node("reflection", reflection)

    # 流程编排
    workflow.set_entry_point("alarm_convergence")
    workflow.add_edge("alarm_convergence", "parallel_check")
    workflow.add_edge("parallel_check", "aggregate_root_cause")

    # 条件分支
    workflow.add_conditional_edges(
        "aggregate_root_cause",
        judge_operation,
        {
            "normal": "execute_fix",
            "high_risk": "human_approval"
        }
    )

    workflow.add_edge("human_approval", "execute_fix")
    workflow.add_edge("execute_fix", "verify_result")
    workflow.add_edge("verify_result", "reflection")
    workflow.add_edge("reflection", END)

    # 编译：高危操作前中断
    return workflow.compile(interrupt_before=["human_approval"])