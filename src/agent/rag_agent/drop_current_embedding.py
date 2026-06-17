from pymilvus import connections, utility
from .rag_settings import MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION_NAME

# 连接Milvus
connections.connect(
    alias="default",
    host=MILVUS_HOST,
    port=MILVUS_PORT
)

# 删除旧集合
if utility.has_collection(MILVUS_COLLECTION_NAME):
    utility.drop_collection(MILVUS_COLLECTION_NAME)
    print(f"✅ 已删除旧集合: {MILVUS_COLLECTION_NAME}")
else:
    print("集合不存在，无需删除")