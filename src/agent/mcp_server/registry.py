from typing import Callable, Dict

# 全局工具注册表
MCP_TOOLS_REGISTRY: Dict[str, Callable] = {}

def register_mcp_tool(func: Callable) -> Callable:
    """装饰器：自动把函数注册为MCP服务端工具"""
    MCP_TOOLS_REGISTRY[func.__name__] = func
    return func