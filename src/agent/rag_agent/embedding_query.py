from typing import List, Dict
from pymilvus import Collection, connections
from .rag_settings import (
    MILVUS_HOST, MILVUS_PORT, MILVUS_TIMEOUT,
    MILVUS_COLLECTION_NAME, SEARCH_TOP_K, SEARCH_METRIC_TYPE
)
from .document_embedding import zhipu_embedding


class MilvusVectorQuery:
    """Milvus 向量检索工具"""

    def __init__(self):
        connections.connect(
            alias="default",
            host=MILVUS_HOST,
            port=MILVUS_PORT,
            timeout=MILVUS_TIMEOUT
        )
        self.collection = Collection(MILVUS_COLLECTION_NAME)
        self.collection.load()
        self.top_k = SEARCH_TOP_K
        self.metric_type = SEARCH_METRIC_TYPE

    def search(self, query_text: str) -> List[Dict]:
        """
        向量相似度检索
        :param query_text: 用户查询文本
        :return: [{"text": 原文, "source": 文档路径, "score": 相似度分数}]
        """
        # 问题向量化
        query_vector = zhipu_embedding.embed_text(query_text)

        # 检索参数
        search_params = {
            "metric_type": self.metric_type,
            "params": {}
        }

        # 执行检索
        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=self.top_k,
            output_fields=["text", "source"]
        )

        # 格式化返回结果
        ret = []
        for hits in results:
            for hit in hits:
                ret.append({
                    "text": hit.entity.get("text"),
                    "source": hit.entity.get("source"),
                    "score": hit.score
                })
        return ret

    def close(self):
        connections.disconnect("default")


# 全局检索实例
milvus_query = MilvusVectorQuery()