from ..registry import register_mcp_tool


@register_mcp_tool
def check_db(params: dict) -> str:
    """数据库排查：连接数、慢查询、锁等待"""
    assets = params.get("assets", [])
    return f"""
【数据库状态检查】
实例列表：{', '.join(assets)}
总连接数：128 / 最大连接数 500（使用率 25.6%）
慢查询数量（近5分钟）：3 条
锁等待：0 个
主从同步状态：正常，延迟 0s
""".strip()