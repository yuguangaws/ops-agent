from typing import List
from langchain_core.documents import Document
from .document_split import md_splitter
from .embedding_store import milvus_store
from .embedding_query import milvus_query


class OpsRagAgent:
    """
    运维知识库 RAG 主类
    能力：1. 全量 Markdown 文档切片+向量化+入库  2. 向量检索问答
    """

    def __init__(self):
        self.splitter = md_splitter
        self.vector_store = milvus_store
        self.vector_query = milvus_query

    def build_knowledge_base(self) -> None:
        """全量构建知识库：加载MD -> 切片 -> 向量化 -> 写入Milvus"""
        print("===== 开始构建运维知识库 =====")
        # 1. 加载并切片所有 Markdown
        chunks: List[Document] = self.splitter.split_all_docs()
        print(f"📄 文档切片完成，总切片数: {len(chunks)}")

        # 2. 批量写入向量库
        self.vector_store.insert_documents(chunks)
        print("===== 知识库构建完成 =====")

    def retrieve_context(self, question: str) -> str:
        """
        根据问题检索上下文，拼接成Prompt可用文本
        :param question: 用户/运维问题
        :return: 拼接后的参考文档内容
        """
        results = self.vector_query.search(question)
        if not results:
            return "暂无相关运维知识库内容"

        # 拼接检索结果
        context_lines = []
        for idx, item in enumerate(results, 1):
            context_lines.append(
                f"【参考文档{idx}】来源：{item['source']}\n内容：{item['text']}"
            )
        return "\n\n".join(context_lines)

    def close(self):
        """关闭所有连接"""
        self.vector_store.close()
        self.vector_query.close()


# 全局 RAG 主实例
ops_rag_agent = OpsRagAgent()