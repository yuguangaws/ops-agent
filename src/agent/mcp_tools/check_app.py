from typing import List
from .mcp_config import call_mcp_tool


def check_app(assets: List[str]) -> str:
    """
    应用服务排查工具：检查QPS、接口错误率、实例存活状态
    :param assets: 目标应用服务资产列表
    :return: 应用服务排查结果
    """
    return call_mcp_tool(tool_name="check_app", assets=assets)