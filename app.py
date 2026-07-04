import sys
import json
import warnings
from pathlib import Path

import streamlit as st

# ===================== 路径与环境初始化 =====================
# 项目根目录加入Python路径，确保能导入src下的模块
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 过滤无关警告
warnings.filterwarnings("ignore", module="jwt")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 导入Agent核心模块
from src.agent.master_agent import build_master_agent, resume_with_approval


# ===================== 缓存Agent实例 =====================
# 只初始化一次Agent，避免重复连接Milvus、重复构建工作流
@st.cache_resource(show_spinner=False)
def init_agent():
    return build_master_agent()


# ===================== 工具函数 =====================
def parse_llm_json(text: str):
    """解析大模型返回的带```json包裹的文本，提取结构化JSON"""
    try:
        # 去除markdown代码块标记
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            json_str = text.split("```")[1].strip()
        else:
            json_str = text.strip()
        return json.loads(json_str)
    except Exception:
        # 解析失败返回原始文本
        return None


def init_alarm_state(alarm_id: str, alarm_content: str, assets_list: list):
    """构造符合OpsState规范的初始状态，和你main.py里的字段完全对齐"""
    return {
        "alarm_id": alarm_id,
        "alarm_content": alarm_content,
        "affected_assets": assets_list,
        "domains_to_check": [],
        "domain_results": {},
        "audit_logs": [],
        "process_stage": "待处理",
        "root_cause": "",
        "fix_actions": [],
        "approval_status": "pending",
        "is_high_risk": False,
    }


# ===================== 页面配置 =====================
st.set_page_config(
    page_title="智能运维故障排查Agent",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("🔧 智能运维故障排查 Agent")
st.caption("基于 LangGraph + RAG 知识库的自动化故障排查闭环系统")

# 初始化Agent
with st.spinner("正在初始化运维Agent..."):
    workflow = init_agent()


# ===================== 侧边栏：告警输入 =====================
with st.sidebar:
    st.header("📥 告警信息输入")
    st.divider()

    alarm_id = st.text_input("告警ID", value="ALARM-20260619-001")
    alarm_content = st.text_area(
        "告警详情",
        value="生产环境订单服务异常，CPU使用率95%，服务无响应",
        height=100
    )
    assets_input = st.text_input(
        "影响资产（多个用逗号分隔）",
        value="order-01,order-02"
    )

    st.divider()
    run_btn = st.button("🚀 开始排查", type="primary", use_container_width=True)
    clear_btn = st.button("🔄 清空结果", use_container_width=True)


# ===================== 主区域：执行与结果展示 =====================
# 清空结果
if clear_btn:
    st.session_state.clear()
    st.rerun()

# 执行排查
if run_btn:
    # 处理资产列表
    assets_list = [x.strip() for x in assets_input.split(",") if x.strip()]

    # 构造初始状态
    init_state = init_alarm_state(alarm_id, alarm_content, assets_list)
    # 前端维护完整状态，每次收到片段就合并
    current_state = init_state.copy()

    # checkpointer 需要 thread_id 才能定位/持久化本次告警的执行状态；
    # 高危操作会在 human_approval 前中断，之后要用同一个 config 才能恢复执行
    config = {"configurable": {"thread_id": alarm_id}}
    st.session_state["mcp_config"] = config
    st.session_state["awaiting_approval"] = False

    # 流式输出容器
    st.subheader("📊 实时排查进度")
    status_container = st.status("🚨 已接收告警，开始排查...", expanded=True)

    # 根因分析专属流式容器
    st.subheader("🔍 根因分析（实时生成中）")
    root_cause_placeholder = st.empty()

    audit_logs = []
    last_log_count = 0
    is_root_cause_generating = False

    try:
        # ===================== 核心：流式遍历所有事件，自动合并状态 =====================
        for step_event in workflow.stream(init_state, config=config):
            # 兼容step_event是元组的异常情况
            if isinstance(step_event, tuple):
                step_event = step_event[0] if step_event else {}

            for node_name, node_output in step_event.items():
                # 命中 interrupt_before 时，LangGraph 会额外推送一个
                # "__interrupt__" 事件，value 是一个空元组（不携带状态），
                # 不是某个节点的输出，直接跳过；是否真的中断由循环结束后的
                # get_state(config).next 判断
                if node_name == "__interrupt__":
                    continue

                # 兼容node_output是元组的情况，取第一个元素（状态）
                if isinstance(node_output, tuple):
                    if not node_output:
                        continue
                    node_output = node_output[0]

                # 合并本次输出到完整状态中（支持部分状态片段）
                if isinstance(node_output, dict):
                    current_state.update(node_output)
                else:
                    # 如果输出不是字典，跳过不处理
                    continue

                # 1. 更新审计日志（只追加新增的部分）
                current_logs = current_state.get("audit_logs", [])
                new_logs = current_logs[last_log_count:]
                for log in new_logs:
                    audit_logs.append(log)
                    with status_container:
                        st.write(f"✅ {log}")
                last_log_count = len(current_logs)

                # 2. 更新处理阶段
                stage = current_state.get("process_stage", "排查中")
                status_container.update(label=f"⏳ 当前阶段：{stage}")

                # 3. 根因节点专属：实时流式渲染生成内容
                if node_name == "aggregate_root_cause":
                    is_root_cause_generating = True
                    current_root_cause = current_state.get("root_cause", "")
                    # 用markdown实时渲染，支持代码块格式
                    root_cause_placeholder.markdown(current_root_cause)

        if is_root_cause_generating:
            root_cause_placeholder.info("✅ 根因分析生成完成，下方查看结构化结果")

        # 高危操作会在 human_approval 节点前中断（不会跑 execute_fix 及之后的节点），
        # 需要人工审批后调用 resume_with_approval 才能继续；这里用 get_state(...).next
        # 判断图是否还停在中断点，而不是想当然地认为 stream 结束就等于全流程跑完
        if workflow.get_state(config).next:
            status_container.update(label="⚠️ 命中高危操作，等待人工审批", state="running", expanded=True)
            st.session_state["awaiting_approval"] = True
        else:
            status_container.update(label="✅ 故障排查完成", state="complete", expanded=False)

        st.session_state["final_state"] = current_state
        st.session_state["audit_logs"] = audit_logs

    except Exception as e:
        status_container.update(label="❌ 排查执行失败", state="error")
        st.error(f"执行出错：{str(e)}")
        with st.expander("查看详细错误堆栈"):
            import traceback
            st.code(traceback.format_exc())

# ===================== 人工审批区：命中高危操作时展示 =====================
# 独立于 run_btn 之外，这样审批按钮点击触发的 rerun 也能正常显示（Streamlit 每次交互都会重跑整个脚本）
if st.session_state.get("awaiting_approval"):
    st.divider()
    st.warning("🚧 检测到高危修复操作，execute_fix / verify_result / reflection 尚未执行，需人工审批后才会继续")

    approve_col, reject_col = st.columns(2)
    with approve_col:
        if st.button("✅ 批准执行", type="primary", use_container_width=True, key="approve_btn"):
            resumed_state = resume_with_approval(
                workflow, st.session_state["mcp_config"], approved=True
            )
            st.session_state["final_state"] = resumed_state
            st.session_state["audit_logs"] = resumed_state.get("audit_logs", [])
            st.session_state["awaiting_approval"] = False
            st.rerun()
    with reject_col:
        if st.button("❌ 驳回修复", use_container_width=True, key="reject_btn"):
            resumed_state = resume_with_approval(
                workflow, st.session_state["mcp_config"], approved=False
            )
            st.session_state["final_state"] = resumed_state
            st.session_state["audit_logs"] = resumed_state.get("audit_logs", [])
            st.session_state["awaiting_approval"] = False
            st.rerun()

# ===================== 结构化展示结果 =====================
# final_state 可能来自本次 run_btn 的直接执行，也可能来自审批后的 resume_with_approval，统一在这里展示
if st.session_state.get("final_state") and not st.session_state.get("awaiting_approval"):
    final_state = st.session_state["final_state"]
    audit_logs = st.session_state.get("audit_logs", final_state.get("audit_logs", []))

    st.divider()
    st.subheader("📋 排查结果总览")

    # 解析结构化根因
    root_cause_raw = final_state.get("root_cause", "")
    root_cause_json = parse_llm_json(root_cause_raw)

    # 概览卡片
    col1, col2, col3 = st.columns(3)
    with col1:
        severity = root_cause_json["impact_scope"]["level"] if root_cause_json else "未知"
        st.metric("故障等级", severity, delta_color="inverse")
    with col2:
        stage = final_state.get("process_stage", "完成")
        st.metric("处理阶段", stage)
    with col3:
        domain_count = len(final_state.get("domains_to_check", []))
        st.metric("排查领域数", domain_count)

    # 分Tab展示详情
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 根因分析", "🛠️ 修复方案", "📜 全流程审计日志", "📊 领域排查详情"])

    # Tab1: 根因分析
    with tab1:
        if root_cause_json:
            st.markdown(f"### 核心根因\n{root_cause_json['root_cause']}")
            st.markdown(f"### 异常现象汇总\n{root_cause_json['phenomenon_summary']}")
            st.markdown(f"### 影响范围\n- 等级：**{root_cause_json['impact_scope']['level']}**\n- 描述：{root_cause_json['impact_scope']['description']}")
            if root_cause_json.get("knowledge_reference"):
                st.markdown("### 参考知识库文档")
                for doc in root_cause_json["knowledge_reference"]:
                    st.markdown(f"- {doc}")
        else:
            st.text_area("根因分析原文", root_cause_raw, height=300)

    # Tab2: 修复方案
    with tab2:
        if root_cause_json and "fix_scheme" in root_cause_json:
            fix = root_cause_json["fix_scheme"]
            st.markdown("### 🩹 临时止血方案")
            st.info(fix["immediate"])

            st.markdown("### ✅ 根治方案")
            st.success(fix["permanent"])

            st.markdown("### ↩️ 回滚方案")
            st.warning(fix["rollback"])

            st.markdown("### ✅ 验证标准")
            st.markdown(root_cause_json["verify_method"])

            # 高危操作标记
            if root_cause_json.get("is_high_risk"):
                st.error(f"⚠️ 高危操作提示：{root_cause_json['risk_desc']}")
        else:
            st.write("修复方案：", final_state.get("fix_actions", []))

    # Tab3: 审计日志
    with tab3:
        for i, log in enumerate(audit_logs, 1):
            st.markdown(f"{i}. {log}")

    # Tab4: 各领域排查详情
    with tab4:
        domain_results = final_state.get("domain_results", {})
        for domain, result in domain_results.items():
            with st.expander(f"📂 {domain} 领域排查结果", expanded=True):
                st.write(result)


# 页面底部说明
st.divider()
st.caption("💡 基于 LangGraph 编排的多领域子Agent + RAG 运维知识库，实现故障自动排查-分析-修复闭环")