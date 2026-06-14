from typing import List
from .mcp_config import call_mcp_tool


def check_db(assets: List[str]) -> str:
    """
    数据库排查工具：检查连接数、慢查询、锁等待、表空间状态
    :param assets: 目标数据库实例资产列表
    :return: 数据库排查结果
    """
    return call_mcp_tool(tool_name="check_db", assets=assets)