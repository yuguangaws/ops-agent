from settings import MOCK_OPS_KNOWLEDGE

def mock_rag_retrieve(user_input: str) -> str:
    """Mock RAG知识库检索"""
    answer = "未找到相关运维知识，请换个问题~"
    for key, value in MOCK_OPS_KNOWLEDGE.items():
        if key in user_input:
            answer = value
            break
    return answer