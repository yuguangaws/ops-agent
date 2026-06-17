import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.agent.rag_agent.rag_agent import OpsRagAgent


def test_rag():
    print("=" * 60)
    print("【RAG知识库检索测试】")
    print("=" * 60)
    try:
        rag = OpsRagAgent()
        query = "Java服务OOM内存溢出怎么排查？"

        # ========== 测试1：上层标准接口（Agent主流程用）==========
        print("\n▶ 测试1：retrieve_context 上下文检索（标准接口）")
        context = rag.retrieve_context(query)
        print("✅ 检索成功")
        print(f"返回内容预览:\n{context[:300]}...")

        # ========== 测试2：底层向量召回（调试详情）==========
        print("\n" + "-" * 50)
        print("\n▶ 测试2：vector_query.search 底层召回详情")
        raw_results = rag.vector_query.search(query)
        print(f"✅ 召回成功，共 {len(raw_results)} 条结果")
        for i, item in enumerate(raw_results, 1):
            print(f"\n第{i}条 | 来源: {item.get('source', '未知')}")
            print(f"  内容预览: {item.get('text', '')[:120]}...")

        # 关闭连接
        rag.close()
        return True

    except Exception as e:
        print(f"❌ 检索失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_rag()