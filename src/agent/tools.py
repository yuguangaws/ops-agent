from typing import Dict

# ====================== Mock 运维工具 ======================
def mock_check_cpu() -> Dict:
    return {"tool": "CPU检查", "result": "CPU使用率：96%，存在异常占用进程"}

def mock_check_disk() -> Dict:
    return {"tool": "磁盘检查", "result": "磁盘使用率：98%，/var/log目录爆满"}

def mock_check_log() -> Dict:
    return {"tool": "应用日志检查", "result": "ERROR：Python进程死循环，502网关错误"}

def mock_diagnosis() -> Dict:
    return {"tool": "根因诊断", "result": "死循环进程导致CPU/磁盘爆满，服务不可用"}

# ====================== 工具映射 ======================
TOOL_MAP = {
    "检查CPU使用率": mock_check_cpu,
    "检查磁盘使用率": mock_check_disk,
    "检查应用错误日志": mock_check_log,
    "根因定位与诊断": mock_diagnosis
}

# ====================== 执行节点 ======================
from state import OpsAgentState
def execute_node(state: OpsAgentState) -> OpsAgentState:
    """按计划分步执行工具"""
    current_step = state["current_step"]
    plan = state["plan"]

    step_name = plan[current_step]
    tool_func = TOOL_MAP[step_name]
    result = tool_func()
    state["execution_results"].append(result)

    # 判断是否完成
    if current_step + 1 >= len(plan):
        state["is_plan_completed"] = True
    else:
        state["current_step"] = current_step + 1

    return state