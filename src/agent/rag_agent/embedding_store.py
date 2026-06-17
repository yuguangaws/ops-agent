from typing import List
from pymilvus import (
    Collection, CollectionSchema, FieldSchema, DataType,
    connections, utility
)
from langchain_core.documents import Document
from .rag_settings import (
    MILVUS_HOST, MILVUS_PORT, MILVUS_TIMEOUT,
    MILVUS_COLLECTION_NAME, VECTOR_DIM, SEARCH_METRIC_TYPE
)
from .document_embedding import zhipu_embedding


class MilvusVectorStore:
    """Milvus 向量库写入管理器"""

    def __init__(self):
        self.host = MILVUS_HOST
        self.port = MILVUS_PORT
        self.timeout = MILVUS_TIMEOUT
        self.collection_name = MILVUS_COLLECTION_NAME
        self.vector_dim = VECTOR_DIM
        self._connect()
        self._init_collection()

    def _connect(self):
        """连接本地 Milvus 服务"""
        connections.connect(
            alias="default",
            host=self.host,
            port=self.port,
            timeout=self.timeout
        )
        print(f"✅ Milvus 连接成功: {self.host}:{self.port}")

    def _init_collection(self):
        """初始化集合，不存在则创建"""
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            self.collection.load()
            print(f"📁 已加载现有集合: {self.collection_name}")
            return

        # 定义字段结构
        id_field = FieldSchema(
            name="id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True
        )
        text_field = FieldSchema(
            name="text",
            dtype=DataType.VARCHAR,
            max_length=65535
        )
        vector_field = FieldSchema(
            name="vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=self.vector_dim
        )
        source_field = FieldSchema(
            name="source",
            dtype=DataType.VARCHAR,
            max_length=1024
        )

        # 集合结构
        schema = CollectionSchema(
            fields=[id_field, text_field, vector_field, source_field],
            description="SRE 运维知识库向量集合"
        )

        # 创建集合
        self.collection = Collection(
            name=self.collection_name,
            schema=schema
        )

        # 创建索引（加速检索）
        index_params = {
            "index_type": "FLAT",
            "metric_type": SEARCH_METRIC_TYPE,
            "params": {}
        }
        self.collection.create_index(
            field_name="vector",
            index_params=index_params
        )
        self.collection.load()
        print(f"📁 新建集合并创建索引: {self.collection_name}")

    def insert_documents(self, docs: List[Document]) -> None:
        """批量写入切片文档+向量到 Milvus"""
        if not docs:
            print("⚠️ 无待写入文档")
            return

        # 提取文本、源文件
        texts = [doc.page_content for doc in docs]
        sources = [doc.metadata.get("source", "") for doc in docs]

        # 批量向量化
        print(f"🔨 开始批量向量化，共 {len(texts)} 条切片")
        vectors = zhipu_embedding.embed_texts(texts)

        # 组装数据并插入
        insert_data = [texts, vectors, sources]
        res = self.collection.insert(insert_data)
        print(f"✅ 向量写入完成，插入条数: {res.insert_count}")

    def close(self):
        """关闭 Milvus 连接"""
        connections.disconnect("default")


# 全局 Milvus 写入实例
milvus_store = MilvusVectorStore()