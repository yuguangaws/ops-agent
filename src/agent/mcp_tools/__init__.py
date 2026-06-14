from .check_host import check_host
from .check_db import check_db
from .check_app import check_app
from .check_logs import check_logs
from .fix_service import fix_service

# ==================== 工具注册中心（完全兼容原有调用方式） ====================
OPS_TOOLS = {
    "host": check_host,
    "db": check_db,
    "app": check_app,
    "logs": check_logs,
    "fix": fix_service
}

# 工具列表（后续接入 LangGraph @tool / ToolNode 时直接使用）
MCP_TOOLS_LIST = [check_host, check_db, check_app, check_logs, fix_service]

__all__ = [
    "OPS_TOOLS",
    "MCP_TOOLS_LIST",
    "check_host",
    "check_db",
    "check_app",
    "check_logs",
    "fix_service"
]