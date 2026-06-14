# RAG Agent 调用关系图

下面是 `rag_agent` 模块的调用关系（Mermaid 图）：

```mermaid
flowchart TB
  A[OpsRagAgent<br/>(ops_rag_agent)] -->|split_all_docs()| B[md_splitter<br/>(MarkdownDocSplitter)]
  B --> C[切片列表 (List<Document>)]
  A -->|insert_documents(chunks)| D[milvus_store<br/>(MilvusVectorStore)]
  D -->|embed_texts(texts)| E[zhipu_embedding<br/>(ZhipuDocEmbedding)]
  E --> F[Milvus 集合 (vector 写入)]
  A -->|retrieve_context(question)| G[milvus_query<br/>(MilvusVectorQuery)]
  G -->|embed_text(question)| E
  G -->|search by vector| F
  G --> H[返回检索结果 -> OpsRagAgent 格式化]
  subgraph util
    I[drop_current_embedding.py] -->|drop collection| F
  end
```

说明：
- `OpsRagAgent` 负责编排（构建知识库与检索）。
- `md_splitter` 负责读取并切分 Markdown 文档。
- `zhipu_embedding` 提供单条与批量向量化。
- `milvus_store` 负责写入 Milvus，`milvus_query` 负责检索。
- `drop_current_embedding.py` 为可选的运维清理脚本。
