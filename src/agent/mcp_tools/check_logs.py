from typing import List
from .mcp_config import call_mcp_tool


def check_logs(assets: List[str]) -> str:
    """
    日志检索工具：拉取服务运行日志，定位异常堆栈与报错信息
    :param assets: 目标服务资产列表
    :return: 日志检索结果
    """
    return call_mcp_tool(tool_name="check_logs", assets=assets)