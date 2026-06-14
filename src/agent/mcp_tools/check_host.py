# check_host.py
from typing import List
from .mcp_config import call_mcp_tool


def check_host(
    assets: List[str],
    enable_docker: bool = True
) -> str:
    """
    主机排查工具：覆盖基础资源+Docker运行状态
    基础检查项：CPU使用率、内存占用、磁盘使用率、僵死进程
    Docker检查项：Daemon状态、容器统计、异常容器、资源占用
    :param assets: 目标主机/节点资产列表
    :param enable_docker: 是否开启Docker运行状态排查，默认开启
    :return: 主机完整排查结果
    """
    return call_mcp_tool(
        tool_name="check_host",
        assets=assets,
        enable_docker=enable_docker
    )