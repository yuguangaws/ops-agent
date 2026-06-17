import os
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownTextSplitter
from .rag_settings import CHUNK_SIZE, CHUNK_OVERLAP, KEEP_SEPARATOR, DOC_BASE_DIR


class MarkdownDocSplitter:
    """Markdown 专用文档切片器"""

    def __init__(self):
        self.splitter = MarkdownTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            keep_separator=KEEP_SEPARATOR,
        )

    def load_md_file(self, file_path: str) -> Document:
        """加载单个 Markdown 文件为 LangChain Document 对象"""
        file = Path(file_path)
        if not file.exists() or file.suffix.lower() != ".md":
            raise FileNotFoundError(f"文件不存在或非 Markdown: {file_path}")

        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        return Document(
            page_content=content,
            metadata={
                "source": str(file_path),
                "file_name": file.name
            }
        )

    def split_single_file(self, file_path: str) -> List[Document]:
        """切片单个 MD 文件"""
        doc = self.load_md_file(file_path)
        return self.splitter.split_documents([doc])

    def split_all_docs(self, base_dir: str = DOC_BASE_DIR) -> List[Document]:
        """遍历目录下所有 .md 文件并统一切片"""
        all_chunks = []
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.lower().endswith(".md"):
                    full_path = os.path.join(root, file)
                    chunks = self.split_single_file(full_path)
                    all_chunks.extend(chunks)
        return all_chunks


# 实例化全局切片器
md_splitter = MarkdownDocSplitter()