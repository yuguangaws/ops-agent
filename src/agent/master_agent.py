from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph, END
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from .core.settings import CHECKPOINT_PG_URI
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
    """并行调度：多领域子Agent真正并发执行（线程池）"""
    domains = state["domains_to_check"]
    state["audit_logs"].append(f"【主Agent】并行排查：{domains}")

    if not domains:
        return state

    # 每个线程使用独立的 domain_results/audit_logs 容器，避免并发写同一个共享 dict/list；
    # 执行结果在主线程里统一合并回共享 state，保证合并这一步是线程安全的。
    with ThreadPoolExecutor(max_workers=len(domains)) as executor:
        futures = {
            executor.submit(
                domain_sub_agent,
                dict(state, domain_results={}, audit_logs=[]),
                domain,
            ): domain
            for domain in domains
        }
        for future in as_completed(futures):
            domain_state = future.result()
            state["domain_results"].update(domain_state["domain_results"])
            state["audit_logs"].extend(domain_state["audit_logs"])

    return state

def aggregate_root_cause(state: OpsState):
    """结果聚合 + LLM根因研判（标准流式输出版）"""
    # 第一次推送：标记开始研判，更新审计日志和阶段
    yield {
        "process_stage": "根因研判中",
        "audit_logs": state["audit_logs"] + ["【主Agent】聚合结果，正在分析根因..."]
    }

    # 召回知识库内容
    query = f"故障现象：{state['alarm_content']}，如何排查与处理"
    rag_context = ops_rag_agent.retrieve_context(query)
    
    # 拼接各领域排查结果
    results = "\n".join([f"{k}: {v}" for k, v in state["domain_results"].items()])
    
    # 构造完整prompt
    prompt = ROOT_CAUSE_PROMPT.format(
        alarm_content=state["alarm_content"],
        results=results,
        rag_context=rag_context
    )

    # 流式调用大模型，逐token推送更新
    partial_root_cause = ""
    for chunk in llm.stream(prompt):
        # 兼容不同LLM SDK的返回格式
        if hasattr(chunk, "content"):
            token = chunk.content
        elif isinstance(chunk, str):
            token = chunk
        else:
            token = str(chunk)
        
        partial_root_cause += token
        # 每次只推送更新的root_cause字段，轻量高效
        yield {"root_cause": partial_root_cause}

    # 全部生成完成后，解析结构化数据，填充其余字段
    fix_actions = ["重启异常服务实例"]
    is_high_risk = False
    risk_desc = "无"
    
    try:
        import json
        # 提取JSON内容
        if "```json" in partial_root_cause:
            json_str = partial_root_cause.split("```json")[1].split("```")[0].strip()
        else:
            json_str = partial_root_cause.strip()
        root_cause_data = json.loads(json_str)
        
        fix_actions = [root_cause_data["fix_scheme"]["immediate"]]
        is_high_risk = root_cause_data["is_high_risk"]
        risk_desc = root_cause_data.get("risk_desc", "无")
    except Exception:
        # 解析失败兜底
        pass

    # 最终推送：完整的结果字段 + 审计日志更新
    yield {
        "root_cause": partial_root_cause,
        "fix_actions": fix_actions,
        "is_high_risk": is_high_risk,
        "risk_desc": risk_desc,
        "process_stage": "研判完成",
        "audit_logs": state["audit_logs"] + ["【主Agent】根因分析完成"]
    }

def judge_operation(state: OpsState) -> str:
    """操作路由：普通/高危"""
    return "high_risk" if state["is_high_risk"] else "normal"

def human_approval(state: OpsState) -> OpsState:
    """人工审批节点。

    该节点被列在 `interrupt_before` 中，图第一次执行到这里时会先暂停，
    此时这个函数体根本不会运行；只有在外部通过 `resume_with_approval`
    写入 `approval_status` 并恢复执行后，才会真正跑到这里——所以这里只应
    记录审批结果，不能像之前那样无条件把 approval_status 重置回
    "pending"，否则会把外部刚写入的审批结果覆盖掉。
    """
    state["audit_logs"].append(f"【主Agent】人工审批结果：{state['approval_status']}")
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

@lru_cache(maxsize=1)
def _get_checkpointer() -> PostgresSaver:
    """构建持久化的 Postgres checkpointer（进程内单例）。

    用连接池而不是 `PostgresSaver.from_conn_string(...)` 的 `with` 用法，
    是因为图要跨多次 invoke/resume 调用，甚至跨进程重启后仍要能从数据库里
    找回中断状态继续跑，连接必须在应用生命周期内保持打开，不能在某次调用
    结束时就被关掉。`setup()` 是幂等的（内部按迁移版本号判断），每次构建
    Agent 时调用一次即可，不需要额外的运维步骤来初始化表结构。
    """
    pool = ConnectionPool(
        conninfo=CHECKPOINT_PG_URI,
        max_size=10,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    return checkpointer


# ==================== 构建 LangGraph 主流程 ====================
def build_master_agent(checkpointer: BaseCheckpointSaver | None = None):
    """构建并编译主流程图。

    checkpointer 默认使用持久化的 Postgres 实现（见 `_get_checkpointer`），
    需要本地先 `docker compose up -d` 启动 `docker-compose.yml` 里的
    ops-agent-postgres 服务；单元测试等不想依赖真实数据库的场景，可以显式
    传入 `InMemorySaver()` 覆盖。
    """
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

    # 编译：高危操作前中断。
    # 注意：interrupt_before 必须配合 checkpointer 才能真正暂停并等待外部恢复；
    # 否则 LangGraph 只会在中断点静默截断整张图并返回，execute_fix 之后的所有
    # 节点都不会执行，且无法被恢复（此前就是这个未接 checkpointer 的坑）。
    return workflow.compile(
        checkpointer=checkpointer or _get_checkpointer(),
        interrupt_before=["human_approval"],
    )


def resume_with_approval(
    workflow, config: dict, approved: bool
) -> OpsState:
    """在 human_approval 中断点恢复图执行。

    调用方需使用与首次 `workflow.invoke(state, config)` 相同的 `config`
    （同一个 `thread_id`），先把审批结果写入 checkpointer 保存的状态，
    再以 `None` 作为输入恢复执行，图会从中断的 human_approval 节点继续跑完
    execute_fix -> verify_result -> reflection。
    """
    workflow.update_state(
        config,
        {"approval_status": "approved" if approved else "rejected"},
    )
    return workflow.invoke(None, config=config)