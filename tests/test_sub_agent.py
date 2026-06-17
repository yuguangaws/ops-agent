import os
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.agent.sub_agent import domain_sub_agent
# 修正：导入实际的状态类 OpsState
from src.agent.core.state import OpsState


def test_sub_agent():
    print("=" * 60)
    print("【单领域子Agent执行测试】")
    print("=" * 60)
    try:
        # 1. 构造测试状态：字段完全和实际代码对齐
        test_state = OpsState(
            alarm_content="服务器CPU使用率持续超过90%",
            affected_assets=["test-node-01"],
            domain_results={},
            audit_logs=[],  # 必须初始化，否则代码里append会报错
            root_cause="",
            fix_suggestion=""
        )

        # 2. 修正参数顺序：先传state，再传domain
        result_state = domain_sub_agent(test_state, domain="host")

        # 3. 读取结果
        domain_result = result_state["domain_results"]["host"]
        audit_logs = result_state["audit_logs"]

        print(f"✅ 子Agent执行完成")
        print(f"领域: host")
        print(f"\n审计日志:")
        for log in audit_logs:
            print(f"  - {log}")
        print(f"\n领域检查结果预览:")
        print(f"  {domain_result[:200].strip()}...")
        return True

    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_sub_agent()