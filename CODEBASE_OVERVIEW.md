# ops-agent — Codebase Overview

## What it is

`ops-agent` 是一个基于 LangGraph 编排的智能运维（AIOps）Agent 原型。它接收一条故障告警，自动判断需要排查的领域（主机/数据库/应用/日志），并行调用各领域的"子 Agent"收集诊断信息，再结合 RAG 知识库检索相关运维文档，调用智谱 AI（ZhipuAI）大模型做根因分析、生成修复方案，并在高危操作前插入人工审批环节，最后完成执行、验证与复盘，全程记录审计日志。目前是一个演示/原型阶段的项目（README 自称"原型"），核心排查工具是模拟（mock）实现。

## Tech stack

- **语言**：Python ≥3.10（[pyproject.toml](pyproject.toml)）
- **编排框架**：[LangGraph](https://langgraph-cli) `StateGraph`（`langgraph>=1.0.0`），驱动整个故障处理流程的节点/边/条件分支
- **LLM**：`langchain_community.chat_models.ChatZhipuAI`，模型 `glm-3-turbo`，通过 `ZHIPUAI_API_KEY` 环境变量鉴权（[src/agent/core/llm.py](src/agent/core/llm.py), [src/agent/core/settings.py](src/agent/core/settings.py)）
- **向量库 / RAG**：Milvus（`pymilvus`），配合智谱 `embedding-3` 模型做文档向量化（[src/agent/rag_agent/](src/agent/rag_agent/)）
- **前端**：Streamlit 单页应用 [app.py](app.py)，用于交互式提交告警、流式展示排查进度与根因结论
- **本地运维工具服务**：一个独立的 FastAPI 服务（[src/agent/mcp_server/main.py](src/agent/mcp_server/main.py)），暴露 `/api/mcp/call` 接口，真实实现了主机（`psutil`/`docker`）与数据库（`pymysql`）检查
- **构建/工程化**：`Makefile`（lint/format/test 走 `ruff` + `mypy` + `pytest`），`uv.lock` 表明用 `uv` 管理依赖
- **LangGraph 部署配置**：[langgraph.json](langgraph.json) 声明了一个名为 `agent` 的图，指向 `./src/agent/graph.py:graph`

## Architecture at a glance

项目实际上包含 **三条并存但耦合程度不同的执行路径**：

1. **主流程（唯一被真正跑通的路径）**：`main.py` / `app.py` → `master_agent.build_master_agent()`（LangGraph `StateGraph`）→ 每个领域调用 `sub_agent.domain_sub_agent()` → 走 `tools.py` 里的**纯 mock 函数**返回排查结果字符串。
2. **RAG 知识库子系统**：`rag_agent/` 独立于主流程之外的一套"文档切片→向量化→写入/检索 Milvus"的流水线，仅在 `aggregate_root_cause` 节点里被调用一次，用于拼接 Prompt 上下文。
3. **MCP 工具服务（真实实现，但未接入主流程）**：`mcp_server/`（FastAPI 服务端，真实检查主机/数据库状态）+ `mcp_tools/`（HTTP 客户端封装，通过 `mcp_config.call_mcp_tool` 调 MCP 服务）。这套是"真实工具"的雏形，但 `sub_agent.py` 目前仍然只 import `tools.py` 的 mock 函数，两者尚未打通（见下方 Notes）。

```
┌────────────┐      ┌──────────────────────────────────────────┐
│ app.py     │      │              master_agent.py               │
│ (Streamlit)│─────▶│  StateGraph(OpsState)                      │
└────────────┘      │                                            │
┌────────────┐      │  alarm_convergence                          │
│ main.py    │─────▶│        │                                    │
│ (CLI Demo) │      │        ▼                                    │
└────────────┘      │  parallel_check ──▶ sub_agent.domain_sub_agent │
                     │        │                 │                  │
                     │        │                 ▼                  │
                     │        │           tools.py (mock host/db/app/logs)
                     │        ▼                                    │
                     │  aggregate_root_cause ──▶ rag_agent.ops_rag_agent.retrieve_context()
                     │        │                     │              │
                     │        │                     ▼              │
                     │        │              Milvus (embedding_store/query)
                     │        │                                    │
                     │        ▼ (llm.stream, ROOT_CAUSE_PROMPT)     │
                     │  judge_operation ─┬─ normal ──▶ execute_fix  │
                     │                   └─ high_risk ─▶ human_approval (interrupt) ─▶ execute_fix
                     │        │                                    │
                     │        ▼                                    │
                     │  verify_result ─▶ reflection ─▶ END          │
                     └──────────────────────────────────────────┘

（未接入上述主流程的独立子系统）
┌────────────────┐  HTTP   ┌───────────────────┐
│ mcp_tools/*.py  │───────▶│ mcp_server/main.py │── psutil / docker / pymysql
│ (client stubs)  │        │ (FastAPI 服务)      │
└────────────────┘        └───────────────────┘
```

## Directory & module map

| 目录/文件 | 职责 |
|---|---|
| [app.py](app.py) | Streamlit 前端：输入告警、流式展示 LangGraph 执行过程与结构化结果 |
| [src/agent/main.py](src/agent/main.py) | CLI 演示入口：构建 Agent、灌入 `TEST_ALARM`、打印结果 |
| [src/agent/master_agent.py](src/agent/master_agent.py) | 核心：定义 `OpsState` 流转的 LangGraph 节点（告警收敛→并行排查→根因研判→审批→修复→验证→复盘）与图编译逻辑 |
| [src/agent/sub_agent.py](src/agent/sub_agent.py) | 通用 ReAct 子 Agent：Think(LLM) → Act(调工具) → Observe，各领域复用同一实现 |
| [src/agent/tools.py](src/agent/tools.py) | **当前被主流程实际使用**的 mock 工具集：`host/db/app/logs/fix`，均为写死的字符串返回 |
| [src/agent/qa_graph.py](src/agent/qa_graph.py) | 一个独立的问答节点草稿，**引用了不存在的 `OpsAgentState` 和 `mock_rag_retrieve`**，未被其他模块 import（见 Notes） |
| [src/agent/core/state.py](src/agent/core/state.py) | `OpsState` TypedDict：贯穿全流程的状态定义（告警信息、排查结果、审批、审计日志等） |
| [src/agent/core/llm.py](src/agent/core/llm.py) | 全局 `llm` 实例（ChatZhipuAI） |
| [src/agent/core/pe.py](src/agent/core/pe.py) | 三套 Prompt 模板：根因分析、ReAct 思考、故障复盘 |
| [src/agent/core/settings.py](src/agent/core/settings.py) | 环境变量加载（`.env`）与运维配置常量（告警等级、高危动作列表） |
| [src/agent/rag_agent/](src/agent/rag_agent/) | RAG 子系统：`document_split.py`（Markdown 切片）→ `document_embedding.py`（智谱向量化）→ `embedding_store.py` / `embedding_query.py`（Milvus 写入/检索）→ `rag_agent.py`（对外统一接口 `OpsRagAgent`） |
| [src/agent/mcp_server/](src/agent/mcp_server/) | 独立 FastAPI 服务：真实实现的 `check_host`（psutil+docker）、`check_db`（pymysql），通过装饰器 `register_mcp_tool` 注册到 `MCP_TOOLS_REGISTRY` |
| [src/agent/mcp_tools/](src/agent/mcp_tools/) | MCP 服务的 HTTP 客户端封装（`check_host/check_db/check_app/check_logs/fix_service`），通过 `mcp_config.call_mcp_tool` 请求上面的 FastAPI 服务 |
| [src/docs/](src/docs/) | 运维知识库原始 Markdown 文档（CPU/磁盘/内存/服务不可用/响应慢等 SOP），是 RAG 的数据源 |
| [tests/](tests/) | pytest 用例：`test_master_agent.py`（端到端）、`test_sub_agent.py`、`test_llm.py`、`test_rag.py`、`test_mcp_tools.py` 等；`tests/unit_tests/` 和 `tests/integration_tests/` 是 LangGraph 模板遗留的空壳目录 |

## Core flows

### 1. CLI 演示流程（`main.py`）

1. `build_master_agent()` 构建并编译 LangGraph（`master_agent.py:169`），入口节点 `alarm_convergence`。
2. `alarm_convergence`：用关键词匹配（"CPU/主机/内存" → host，"数据库" → db，"服务/应用/接口" → app，"日志/异常/报错" → logs）填充 `domains_to_check`（`master_agent.py:11-27`）。
3. `parallel_check`：对每个领域顺序调用 `sub_agent.domain_sub_agent()`（命名为"并行"但实现是 for 循环，见 Notes），每个子 Agent 内部先调 LLM 做 ReAct "思考"（结果未使用，见 Notes），再调 `tools.py` 中对应领域的 mock 函数拿到结果，写入 `state["domain_results"]`。
4. `aggregate_root_cause`：是一个生成器节点（LangGraph 流式节点），先查询 RAG（`ops_rag_agent.retrieve_context`），拼接 `ROOT_CAUSE_PROMPT`，然后 `llm.stream()` 逐 token 产出 `root_cause`；结束后尝试把输出解析成结构化 JSON，提取 `fix_actions` / `is_high_risk`。
5. `judge_operation` 路由：`is_high_risk=True` → `human_approval`（图在此中断，等待外部把 `approval_status` 置为 `approved`）；否则直接 `execute_fix`。
6. `execute_fix` 调 `tools.py` 的 `mock_fix_service`；`verify_result`、`reflection` 各自追加审计日志并推进 `process_stage`，最终 `END`。
7. `main.py` 打印 `process_stage`、`root_cause`、`fix_actions` 与完整 `audit_logs`。

### 2. Streamlit 交互流程（`app.py`）

与上面共享同一个 `build_master_agent()`（用 `@st.cache_resource` 缓存，避免重复连接 Milvus），但用 `workflow.stream(init_state)` 逐步获取每个节点的增量输出，实时合并到 `current_state` 并更新 UI：审计日志实时追加、`aggregate_root_cause` 节点的流式 token 实时渲染到 Markdown 占位符，执行完成后按 Tab 展示根因/修复方案/审计日志/领域详情。

## Key design decisions & patterns

- **单一全局状态 (`OpsState`) 贯穿全图**：所有节点读写同一个 TypedDict，而不是各自的局部状态，简化了节点间传递，但也意味着节点对状态字段有隐式的顺序依赖（例如 `execute_fix` 依赖 `is_high_risk` 已被 `aggregate_root_cause` 设置）。
- **流式生成器节点**：`aggregate_root_cause` 用 Python `yield` 实现 LangGraph 的增量状态更新，配合 `workflow.stream()` 达到打字机效果，是这个项目里最"精心设计"的部分。
- **中断驱动的人工审批**：`workflow.compile(interrupt_before=["human_approval"])` 用 LangGraph 原生中断机制表达"高危操作需要人工确认"，但当前代码库里没有看到恢复中断、写入 `approval_status="approved"` 后继续执行的调用点（CLI 和 Streamlit 都没有处理 `interrupt` 后半段）。
- **Prompt 即契约**：`core/pe.py` 里的 `ROOT_CAUSE_PROMPT` 强制模型输出严格 JSON，下游用 ` ```json ` 分隔符做字符串解析（`master_agent.py:110-116`，`app.py:29-42`），属于弱类型契约，一旦模型不遵守格式解析会静默失败并 fallback。
- **注册表模式**：`mcp_server/registry.py` 用装饰器 `@register_mcp_tool` 把函数注册进全局字典，`mcp_server/main.py` 靠 `from .tools import *` 触发注册的副作用——这是一种常见但隐式的插件注册手法，新增工具必须记得写 `@register_mcp_tool` 且被 `tools/__init__.py` import 到。

## Getting started

来自 [README.md](README.md) 与 [Makefile](Makefile)：

```bash
# 安装依赖
pip install -e . "langgraph-cli[inmem]"

# 配置密钥
export ZHIPUAI_API_KEY=你的智谱API_KEY

# 运行 CLI 演示
python src/agent/main.py

# 运行 Streamlit UI
streamlit run app.py

# 运行测试
make test                 # 默认 tests/unit_tests/（目前为空壳）
python -m pytest tests/test_master_agent.py   # 实际的端到端测试在 tests/ 根目录
make lint / make format   # ruff + mypy
```

若要跑通真实工具链路（`mcp_server`），还需单独启动：

```bash
python src/agent/mcp_server/main.py   # FastAPI 服务，默认 0.0.0.0:8080
```

以及本地 Milvus 服务（默认连 `localhost:19530`，见 [rag_settings.py](src/agent/rag_agent/rag_settings.py)）。

## Notes & observations

以下是阅读中发现的、可能值得关注的点（均为观察，非定论）：

- **`langgraph.json` 指向不存在的文件**：配置声明图入口为 `./src/agent/graph.py:graph`，但 `src/agent/` 下没有 `graph.py`（只有 `master_agent.py` 导出 `build_master_agent`，`qa_graph.py` 导出 `qa_node`）。用 `langgraph dev`/`langgraph up` 启动大概率会失败。
- **`qa_graph.py` 是断链代码**：它 `from agent.core.state import OpsAgentState`，但 `core/state.py` 里只定义了 `OpsState`，没有 `OpsAgentState`；函数体里调用的 `mock_rag_retrieve` 在仓库中也搜不到定义。当前没有其他文件 import 这个模块，运行主流程不受影响，但它本身是无法执行的。
- **"并行排查"其实是串行**：`master_agent.parallel_check`（[master_agent.py:29-38](src/agent/master_agent.py#L29-L38)）用普通 `for` 循环依次调用各领域子 Agent，注释和函数名叫"并行调度"，但没有用线程池/`asyncio`/LangGraph 的并行分支能力，是名不副实的注释，也是 README 里提到的"并行排查多个领域"与实现之间的差距。
- **ReAct "Think" 步骤的 LLM 调用结果被丢弃**：`sub_agent.py:19` 里 `llm.invoke(prompt)` 的返回值没有被使用，也没有解析 Prompt 里要求的 `Action`/`Action Input` 格式来决定调用哪个工具——工具选择实际上是 `master_agent.py` 里关键词匹配 + 领域名硬编码到 `OPS_TOOLS[domain]`，`REACT_THINK_PROMPT` 目前更像是装饰性调用，尚未真正驱动决策。
- **两套工具实现并存，主流程只用了"假"的那套**：`tools.py` 是硬编码字符串的 mock；`mcp_server/` + `mcp_tools/` 是真实调用 `psutil`/`docker`/`pymysql` 的完整实现，但 `sub_agent.py` 并未 import `mcp_tools`，所以 README 里"扩展建议：将 TOOLS 替换为真实运维接口"这条其实已经写了一半（`mcp_tools`），只是还没接进 `sub_agent.py` / `master_agent.py`。
- **中断后的审批恢复逻辑缺失**：`human_approval` 节点只是把 `approval_status` 设为 `"pending"` 并记录日志，配合 `interrupt_before=["human_approval"]`——但代码库里没有看到任何地方在中断后调用 `workflow.update_state(...)` 或用 `Command(resume=...)` 写入审批结果并继续图的执行；`execute_fix` 里判断 `approval_status != "approved"` 的分支目前无法被触发为 `approved`。
- **`db_config` 里的数据库密码硬编码在源码中**（[mcp_server/tools/db.py:20](src/agent/mcp_server/tools/db.py#L20)），本地开发场景下问题不大，但如果该服务被部署或该文件被提交到公共仓库需要注意。
- **`VECTOR_DIM` 与 embedding 模型维度的注释不一致**：[rag_settings.py:9](src/agent/rag_agent/rag_settings.py#L9) 里 `VECTOR_DIM = 2048` 的注释写"智谱 Embedding 固定 2048 维"，但智谱官方 `embedding-3` 模型默认输出是 2048 维（可通过参数调整为其他维度如 1024/512/256）——如果后续更换维度参数需要同步改这里，否则 Milvus 建的 collection schema 会和实际向量维度不匹配导致插入失败。
- **`app.py` 里保留了一大段被注释掉的旧实现**（第 106-221 行），与紧接着的新实现重复，建议后续清理，避免维护时误改错版本。
