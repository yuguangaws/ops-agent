# mcp_config.py
from typing import List, Any
import requests
from dataclasses import dataclass


@dataclass
class McpConfig:
    """MCP 服务全局配置，默认 localhost + 8080 端口"""
    MCP_HOST: str = "localhost"
    MCP_PORT: int = 8080
    MCP_TIMEOUT: int = 10  # 单位：秒
    BASE_URL: str = f"http://{MCP_HOST}:{MCP_PORT}"


# 全局单例配置
mcp_config = McpConfig()


def call_mcp_tool(tool_name: str, **params: Any) -> str:
    """
    通用 MCP 工具调用方法，支持动态传参
    :param tool_name: MCP 服务端注册的工具名称
    :param params: 工具业务参数，自动封装到请求体 params 字段
    :return: 工具执行结果字符串
    """
    payload = {
        "tool": tool_name,
        "params": params
    }

    try:
        resp = requests.post(
            url=f"{mcp_config.BASE_URL}/api/mcp/call",
            json=payload,
            timeout=mcp_config.MCP_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()

        # 兼容标准 MCP 返回格式
        if data.get("code") == 0 and "data" in data:
            return data["data"]
        else:
            err_msg = data.get("msg", "工具执行未知错误")
            return f"【{tool_name}执行失败】{err_msg}"

    except requests.exceptions.ConnectionError:
        return f"【{tool_name}连接失败】无法连接 MCP 服务 {mcp_config.BASE_URL}，请检查服务是否启动"
    except requests.exceptions.Timeout:
        return f"【{tool_name}请求超时】MCP 服务响应超时"
    except Exception as e:
        return f"【{tool_name}异常】请求出错：{str(e)}"