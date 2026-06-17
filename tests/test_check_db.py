# ========== 自动添加项目根路径 ==========
# ========== 放在文件最开头，所有导入之前 ==========
import os
# 强制 localhost/127.0.0.1 不走代理
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"

import sys
from pathlib import Path

curr_file = Path(__file__).resolve()
project_root = curr_file.parent
while not (project_root / "src").exists() and project_root.parent != project_root:
    project_root = project_root.parent

sys.path.append(str(project_root))
# ========================================

# 导入MCP客户端工具
from src.agent.mcp_tools import check_db

if __name__ == "__main__":
    print("=" * 60)
    print("【MCP客户端全链路测试：MySQL检查】")
    print("=" * 60)

    # 客户端调用方式：直接传资产列表，和Agent里调用方式完全一致
    result = check_db(["bi_test本地实例"])
    print(result)