from state import OpsAgentState
from rag import mock_rag_retrieve

def qa_node(state: OpsAgentState) -> OpsAgentState:
    """问答节点：直接调用RAG返回结果"""
    answer = mock_rag_retrieve(state["user_input"])
    state["final_answer"] = f"{state['thought']}\n\n📖 问答结果：{answer}"
    return state