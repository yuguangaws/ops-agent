from typing import List
import psutil
import docker
from docker.errors import DockerException
from ..registry import register_mcp_tool  # 导入注册装饰器


@register_mcp_tool
def check_host(params: dict) -> str:
    """主机排查：CPU/内存/磁盘/进程/Docker状态"""
    assets = params.get("assets", [])
    enable_docker = params.get("enable_docker", True)

    # 基础资源检查（本地直接执行）
    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    zombie_count = len([p for p in psutil.process_iter() if p.status() == psutil.STATUS_ZOMBIE])
    base_result = f"""
【基础资源状态】
节点资产：{', '.join(assets)}
CPU使用率：{cpu_usage}%
内存使用率：{mem.percent}%
根分区磁盘使用率：{disk.percent}%
僵死进程数：{zombie_count}个
""".strip()

    if not enable_docker:
        return base_result

    # Docker状态检查（本地直接执行）
    try:
        client = docker.from_env()
        client.ping()
        all_containers = client.containers.list(all=True)
        running = [c for c in all_containers if c.status == "running"]
        exited = [c for c in all_containers if c.status == "exited"]
        
        abnormal = []
        for c in exited:
            code = c.attrs["State"]["ExitCode"]
            if code != 0:
                abnormal.append(f"{c.name} (退出码: {code})")
        
        stats_top = []
        for c in running[:3]:
            stat = c.stats(stream=False)
            cpu_pct = stat["cpu_stats"]["cpu_usage"]["total_usage"] / stat["cpu_stats"]["system_cpu_usage"] * 100
            mem_mb = stat["memory_stats"]["usage"] / 1024 / 1024
            stats_top.append(f"{c.name} | CPU: {cpu_pct:.1f}% | 内存: {mem_mb:.1f}MB")
        
        docker_result = f"""
【Docker运行状态】
Daemon状态：正常运行
总容器数：{len(all_containers)}个
运行中：{len(running)}个
已停止：{len(exited)}个
异常退出容器：{', '.join(abnormal) if abnormal else '无'}
资源占用Top3：
{chr(10).join(['  - ' + s for s in stats_top]) if stats_top else '  无运行容器'}
""".strip()
        return base_result + "\n\n" + docker_result

    except DockerException:
        return base_result + "\n\n【Docker运行状态】异常：Docker Daemon未启动或无法连接"
    except PermissionError:
        return base_result + "\n\n【Docker运行状态】异常：当前用户无Docker操作权限"
    except Exception as e:
        return base_result + f"\n\n【Docker运行状态】异常：{str(e)}"