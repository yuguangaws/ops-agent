from typing import List

# ==================== Mock 运维工具 ====================
def mock_check_host(assets: List[str]) -> str:
    """主机排查工具：CPU/内存/进程/磁盘"""
    return f"【主机排查】{assets} | CPU使用率95%，内存88%，Java进程僵死"

def mock_check_db(assets: List[str]) -> str:
    """数据库排查工具：连接数/慢查询/锁"""
    return f"【数据库排查】{assets} | 连接数正常，无慢查询/锁等待"

def mock_check_app(assets: List[str]) -> str:
    """应用服务排查工具：QPS/错误率/实例状态"""
    return f"【应用排查】{assets} | 接口5xx错误率80%，服务无响应"

def mock_check_logs(assets: List[str]) -> str:
    """日志检索工具：异常堆栈/错误信息"""
    return f"【日志排查】{assets} | OOM内存溢出，服务启动失败"

def mock_fix_service(assets: List[str]) -> str:
    """服务修复工具：重启服务"""
    return f"【修复执行】{assets} | 服务已重启，进程恢复正常"

# ==================== 工具注册中心 ====================
OPS_TOOLS = {
    "host": mock_check_host,
    "db": mock_check_db,
    "app": mock_check_app,
    "logs": mock_check_logs,
    "fix": mock_fix_service
}