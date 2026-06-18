# ops-agent

`ops-agent` 是一个智能运维 Agent 原型，基于 LangGraph 流程编排，结合智谱 AI 与 RAG 知识库，实现告警接收、领域排查、根因分析、修复执行与复盘闭环。

## 项目概览

- 入口：`src/agent/main.py`
- 核心流程：`src/agent/master_agent.py`
- 子 Agent：`src/agent/sub_agent.py`
- 工具模拟：`src/agent/tools.py`
- RAG 知识库：`src/agent/rag_agent/rag_agent.py`
- LLM 与 Prompt：`src/agent/core/llm.py`, `src/agent/core/pe.py`
- 全局状态定义：`src/agent/core/state.py`
- 环境配置：`src/agent/core/settings.py`

## 功能说明

- 告警收敛：自动识别 `host/db/app/logs` 排查领域
- 并行排查：多个领域的子 Agent 同时执行
- 根因分析：结合 RAG 编译辅助上下文，调用智谱 AI 推断故障根因
- 修复执行：模拟修复操作，并支持高危操作审批分支
- 验证复盘：记录审计日志，完成结果验证与故障复盘

## 目录结构

```
src/agent/
  main.py
  master_agent.py
  sub_agent.py
  tools.py
  qa_graph.py
  rag_agent/
    rag_agent.py
    document_embedding.py
    document_split.py
    embedding_query.py
    embedding_store.py
  core/
    llm.py
    pe.py
    settings.py
    state.py
  mcp_tools/
    check_app.py
    check_db.py
    check_host.py
    check_logs.py
    fix_service.py
    mcp_config.py
```

## 运行方式

1. 安装依赖

```bash
pip install -e . "langgraph-cli[inmem]"
```

2. 设置环境变量

```bash
export ZHIPUAI_API_KEY=你的智谱API_KEY
```

3. 运行主脚本

```bash
python src/agent/main.py
```

## 核心组件说明

### `src/agent/main.py`

- 初始化主 Agent
- 通过 `TEST_ALARM` 模拟告警
- 输出流程状态、根因、修复方案与审计日志

### `src/agent/master_agent.py`

- 使用 `langgraph.graph.StateGraph` 定义智能运维工作流
- 节点包括：告警收敛、并行排查、聚合根因、人工审批、执行修复、验证结果、复盘
- 内置高危分支处理，支持在 `human_approval` 前中断

### `src/agent/sub_agent.py`

- 通用 ReAct 子 Agent 实现
- 先调用 LLM 思考排查策略，再执行领域工具，最后记录观察结果

### `src/agent/tools.py`

- 模拟运维工具函数：`host`, `db`, `app`, `logs`, `fix`
- 用于在流程中返回排查结果与修复响应

### `src/agent/rag_agent/rag_agent.py`

- 构建运维知识库：Markdown 切片、向量化、写入 Milvus
- 通过向量检索返回上下文用于根因分析

### `src/agent/core/llm.py`

- 使用 `langchain_community.chat_models.ChatZhipuAI`
- 配置 `glm-3-turbo` 模型与低温度设置

### `src/agent/core/pe.py`

- 定义根因分析、ReAct 思考、复盘提示词模板

### `src/agent/core/state.py`

- 定义 `OpsState` TypedDict，贯穿告警、排查结果、审批状态、流程阶段、审计日志

## 扩展建议

- 将 `TOOLS` 替换为真实运维接口
- 增加审批结果输入与高危动作处理
- 完善 RAG 文档切片与向量检索策略
- 将流程部署为可接受真实告警输入的服务

