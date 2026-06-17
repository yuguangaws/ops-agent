import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.agent.core.llm import llm


def test_llm():
    print("=" * 60)
    print("【大模型调用测试】")
    print("=" * 60)
    try:
        response = llm.invoke("请用一句话回复：运维故障排查的核心流程是什么？")
        print(f"✅ 调用成功")
        print(f"返回内容: {response.content}")
        return True
    except Exception as e:
        print(f"❌ 调用失败: {str(e)}")
        return False


if __name__ == "__main__":
    test_llm()