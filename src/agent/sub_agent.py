from state import OpsState
from tools import OPS_TOOLS
from llm import llm
from pe import REACT_THINK_PROMPT

# ==================== 通用 ReAct 子Agent（所有领域复用） ====================
def domain_sub_agent(state: OpsState, domain: str) -> OpsState:
    """
    领域子Agent：标准 ReAct 流程
    Think(思考) → Act(执行工具) → Observe(观察结果)
    """
    # 1. ReAct Think：LLM决策排查逻辑
    state["audit_logs"].append(f"【{domain}子Agent】开始排查")
    prompt = REACT_THINK_PROMPT.format(
        domain=domain,
        assets=state["affected_assets"],
        alarm=state["alarm_content"]
    )
    llm.invoke(prompt)

    # 2. ReAct Act：调用对应领域工具
    tool_func = OPS_TOOLS[domain]
    result = tool_func(state["affected_assets"])
    state["domain_results"][domain] = result

    # 3. ReAct Observe：记录结果
    state["audit_logs"].append(f"【{domain}子Agent】{result}")

    return state