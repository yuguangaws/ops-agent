import os
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.agent.mcp_tools import OPS_TOOLS

def test_all_tools():
    test_assets = ["test-node-01"]
    print("="*60)
    print("【MCP全工具连通性测试】")
    print("="*60)

    for tool_name, tool_func in OPS_TOOLS.items():
        print(f"\n▶ 测试工具: {tool_name}")
        try:
            # 修复类工具单独传参，避免误执行
            if tool_name == "fix":
                result = tool_func(test_assets)
            else:
                result = tool_func(test_assets)
            print(f"✅ 调用成功，返回长度: {len(result)}")
            print(f"   预览: {result[:100].strip()}...")
        except Exception as e:
            print(f"❌ 调用失败: {str(e)}")

if __name__ == "__main__":
    test_all_tools()