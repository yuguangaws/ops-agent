# ========== 加项目根路径 ==========
import sys
from pathlib import Path

curr_file = Path(__file__).resolve()
project_root = curr_file.parent

# 循环往上找，直到找到包含src目录的那一级
while not (project_root / "src").exists() and project_root.parent != project_root:
    project_root = project_root.parent

sys.path.append(str(project_root))
print("自动识别项目根目录:", project_root)

# 导入客户端工具（mcp_tools里的，不是mcp_server里的）
from src.agent.mcp_tools import check_host

if __name__ == "__main__":
    # 客户端函数直接传列表参数，内部自动封装成HTTP请求
    result = check_host(["localhost-node-01"])
    print(result)
    print("="*50)
    result_no_docker = check_host(["localhost-node-01"], enable_docker=False)
    print(result_no_docker)