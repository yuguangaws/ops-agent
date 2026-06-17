import pymysql
from ..registry import register_mcp_tool


@register_mcp_tool
def check_db(params: dict) -> str:
    """
    MySQL数据库运行状态与进程检查
    检查项：连接连通性、运行时长、连接线程统计、活跃进程列表、慢查询计数
    默认检查本地 bi_test 库，支持通过参数覆盖连接配置
    """
    # 目标资产列表（兼容上层Agent传参，用于展示）
    assets = params.get("assets", ["bi_test本地实例"])

    # MySQL 连接配置（后续可抽离到统一配置文件）
    db_config = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "MyNew#Pass123",
        "database": "bi_test",
        "connect_timeout": 5,  # 连接超时5秒，避免卡住
        "charset": "utf8mb4"
    }

    # 支持通过参数动态覆盖连接配置（比如切换其他数据库实例）
    if params.get("db_config"):
        db_config.update(params["db_config"])

    conn = None
    try:
        # 1. 建立数据库连接，验证连通性
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # 2. 获取核心运行状态指标
        status_keys = [
            "Uptime",               # 数据库运行时长（秒）
            "Threads_connected",    # 当前已建立的连接数
            "Threads_running",      # 当前正在执行的活跃进程数
            "Slow_queries",         # 累计慢查询数量
            "Max_used_connections"  # 历史峰值连接数
        ]
        status_map = {}
        for key in status_keys:
            cursor.execute(f"SHOW STATUS LIKE '{key}'")
            row = cursor.fetchone()
            status_map[row[0]] = row[1]

        # 运行时长转换为易读格式
        uptime_sec = int(status_map["Uptime"])
        days = uptime_sec // 86400
        hours = (uptime_sec % 86400) // 3600
        minutes = (uptime_sec % 3600) // 60
        uptime_readable = f"{days}天{hours}小时{minutes}分钟"

        # 3. 获取完整进程列表（SHOW FULL PROCESSLIST）
        cursor.execute("SHOW FULL PROCESSLIST")
        process_list = cursor.fetchall()
        # 列顺序：Id, User, Host, db, Command, Time, State, Info

        # 格式化进程列表（最多展示20条，避免输出过长）
        max_show = 20
        process_text = []
        for idx, proc in enumerate(process_list[:max_show]):
            proc_id, user, host, db, command, time, state, info = proc
            # SQL文本截断展示，避免过长
            sql_preview = (info[:120] + "...") if info and len(info) > 120 else (info or "无")
            process_text.append(
                f"  进程{idx+1}：ID={proc_id} | 用户={user} | 来源={host} | 库={db} | 命令={command} | 运行{time}s | 状态={state} | SQL={sql_preview}"
            )
        if len(process_list) > max_show:
            process_text.append(f"  ... 共{len(process_list)}条进程，仅展示前{max_show}条")

        # 4. 组装最终结果文本
        result = f"""
【MySQL数据库运行状态检查】
目标资产：{', '.join(assets)}
实例地址：{db_config['host']}:{db_config['port']}
数据库名：{db_config['database']}
连接状态：✅ 正常连通
运行时长：{uptime_readable}

【核心指标统计】
当前总连接数：{status_map['Threads_connected']}
活跃运行进程：{status_map['Threads_running']}
历史峰值连接：{status_map['Max_used_connections']}
累计慢查询数：{status_map['Slow_queries']}

【当前数据库进程列表】
{chr(10).join(process_text) if process_text else "  无运行中的进程"}
""".strip()

        return result

    # 异常分类捕获，返回友好的排查提示
    except pymysql.err.OperationalError as e:
        return f"""
【MySQL数据库检查失败】❌
目标资产：{', '.join(assets)}
错误类型：连接失败
错误详情：{str(e)}
排查建议：1. 确认MySQL服务是否启动 2. 确认地址端口是否正确 3. 确认防火墙是否放行3306端口
""".strip()

    except pymysql.err.ProgrammingError as e:
        return f"""
【MySQL数据库检查失败】❌
目标资产：{', '.join(assets)}
错误类型：库不存在或权限不足
错误详情：{str(e)}
排查建议：1. 确认 bi_test 数据库已创建 2. 确认root用户有该库的访问权限
""".strip()

    except Exception as e:
        return f"""
【MySQL数据库检查异常】❌
目标资产：{', '.join(assets)}
错误类型：未知异常
错误详情：{str(e)}
""".strip()

    finally:
        # 关闭连接，释放资源
        if conn:
            conn.close()