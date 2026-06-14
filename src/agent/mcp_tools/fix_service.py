from typing import List
from .mcp_config import call_mcp_tool


def fix_service(assets: List[str]) -> str:
    """
    服务修复工具：对异常服务执行重启恢复操作
    :param assets: 需要修复的服务资产列表
    :return: 修复执行结果
    """
    return call_mcp_tool(tool_name="fix_service", assets=assets)