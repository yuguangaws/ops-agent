"""LangGraph 平台部署入口。

`langgraph.json` 中的 `agent` 图声明指向本文件的 `graph` 对象，
供 `langgraph dev` / `langgraph up` 等 CLI 加载。
"""

from .master_agent import build_master_agent

graph = build_master_agent()
