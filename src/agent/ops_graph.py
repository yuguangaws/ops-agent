from langgraph.graph import StateGraph, END
from state import OpsAgentState
from pe import react_node, plan_node
from tools import execute_node
from qa_graph import qa_node

# ====================== 报告生成节点 ======================
def generate_report_node(state: OpsAgentState) -> OpsAgentState:
    """生成故障排查最终报告"""
    exec_results = "\n".join([f"✅ {res['tool']}：{res['result']}" for res in state["execution_results"]])
    plan_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(state["plan"])])
    
    final = (
        f"{state['thought']}\n\n"
        f"📋 排查计划：\n{plan_str}\n\n"
        f"🔧 执行结果：\n{exec_results}\n\n"
        f"💡 解决方案：杀死死循环进程，清理日志，修复代码逻辑"
    )
    state["final_answer"] = final
    return state

# ====================== 构建 LangGraph 工作流 ======================
def build_ops_agent():
    workflow = StateGraph(OpsAgentState)

    # 注册节点
    workflow.add_node("react", react_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("qa", qa_node)
    workflow.add_node("generate_report", generate_report_node)

    # 入口
    workflow.set_entry_point("react")

    # 路由1：React后分支
    def route_after_react(state: OpsAgentState):
        return "qa" if state["decision"] == "qa" else "plan"

    workflow.add_conditional_edges(
        "react", route_after_react,
        {"qa": "qa", "plan": "plan"}
    )

    # 路由2：执行循环
    def route_execute(state: OpsAgentState):
        return "execute" if not state["is_plan_completed"] else "generate_report"

    workflow.add_conditional_edges(
        "execute", route_execute,
        {"execute": "execute", "generate_report": "generate_report"}
    )

    # 固定流程
    workflow.add_edge("plan", "execute")
    workflow.add_edge("qa", END)
    workflow.add_edge("generate_report", END)

    return workflow.compile()

# ====================== 测试运行 ======================
if __name__ == "__main__":
    agent = build_ops_agent()
    
    print("="*60)
    print("🎯 场景1：简单运维问答")
    res1 = agent.invoke({
        "user_input": "nginx默认端口是多少",
        "thought": "", "decision": "qa", "plan": [],
        "current_step": 0, "execution_results": [], "is_plan_completed": False
    })
    print(res1["final_answer"])

    print("\n" + "="*60)
    print("🎯 场景2：服务器故障排查")
    res2 = agent.invoke({
        "user_input": "服务器特别卡，接口报502",
        "thought": "", "decision": "qa", "plan": [],
        "current_step": 0, "execution_results": [], "is_plan_completed": False
    })
    print(res2["final_answer"])