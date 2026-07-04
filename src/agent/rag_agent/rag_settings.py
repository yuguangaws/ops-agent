from typing import Optional
import os

# ===================== Milvus 向量库配置 =====================
MILVUS_HOST: str = "localhost"
MILVUS_PORT: int = 19530
MILVUS_TIMEOUT: int = 10000  # 单位：毫秒
MILVUS_COLLECTION_NAME: str = "ops_sre_docs"  # 运维知识库集合名
VECTOR_DIM: int = 2048  # 需与 ZHIPU_EMBEDDING_MODEL 实际输出维度一致（embedding-3 默认 2048 维，可通过模型参数调整），改维度时务必同步修改这里，否则 Milvus collection schema 会与实际向量维度不匹配导致写入失败

# ===================== 文档切片配置（Markdown 最优参数） =====================
CHUNK_SIZE: int = 1000        # 单块字符数
CHUNK_OVERLAP: int = 200      # 块重叠字符数
KEEP_SEPARATOR: bool = True   # 保留 Markdown 分隔符

# ===================== 智谱 Embedding 配置 =====================
ZHIPU_EMBEDDING_MODEL: str = "embedding-3"  # 智谱向量模型
EMBEDDING_BATCH_SIZE: int = 16  # 批量向量化批次大小

# ===================== 文档路径 =====================
DOC_BASE_DIR: str = "../../docs"  # 相对于 rag_agent 的文档根目录

# ===================== 向量检索配置 =====================
SEARCH_TOP_K: int = 5  # 检索返回 TopK 结果
SEARCH_METRIC_TYPE: str = "COSINE"  # 相似度算法：余弦相似度

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")