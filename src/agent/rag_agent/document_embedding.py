from typing import List
from langchain_community.embeddings import ZhipuAIEmbeddings
from .rag_settings import ZHIPU_EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE
from .rag_settings import ZHIPUAI_API_KEY


class ZhipuDocEmbedding:
    """智谱 Embedding 向量化工具，输出 1024 维向量"""

    def __init__(self):
        self.embedding = ZhipuAIEmbeddings(
            api_key=ZHIPUAI_API_KEY,
            model=ZHIPU_EMBEDDING_MODEL,
            batch_size=EMBEDDING_BATCH_SIZE
        )

    def embed_text(self, text: str) -> List[float]:
        """单条文本向量化"""
        return self.embedding.embed_query(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # 前置校验：移除空串、全空格、None值
        valid_texts = [t.strip() for t in texts if t and t.strip()]
        if not valid_texts:
            return []
        return self.embedding.embed_documents(valid_texts)

# 全局 Embedding 实例
zhipu_embedding = ZhipuDocEmbedding()