import sys
from pathlib import Path
CURR_PATH = Path(__file__).resolve()
SRC_PATH = CURR_PATH.parent.parent.parent
sys.path.append(str(SRC_PATH))

from .rag_agent import OpsRagAgent

if __name__ == "__main__":
    # 仅首次执行构建，后续注释该行，直接检索
    OpsRagAgent.build_knowledge_base()

    # 测试用例列表
    test_queries = [
        "服务器CPU占用过高如何排查？",          # 精准问题
        "内存溢出 OOM 怎么处理",              # 模糊匹配
        "日志报错怎么分析",                   # 通用运维问题
        "如何配置K8s网络策略",                # 测试无相关文档场景
    ]

    for idx, q in enumerate(test_queries, 1):
        print(f"\n===== 测试用例 {idx} =====")
        print(f"问题：{q}")
        res = OpsRagAgent.retrieve_context(q)
        print(f"检索结果：\n{res}")

    OpsRagAgent.close()