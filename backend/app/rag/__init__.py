"""
Tax Rules RAG Layer (Phase 6).
"""

from app.rag.retriever import (
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_CORPUS_PATH,
    TaxRAGService,
    get_rag_service,
    index_tax_rules_corpus,
    retrieve_tax_rules,
)

__all__ = [
    "TaxRAGService",
    "get_rag_service",
    "retrieve_tax_rules",
    "index_tax_rules_corpus",
    "DEFAULT_CHROMA_DIR",
    "DEFAULT_COLLECTION_NAME",
    "DEFAULT_CORPUS_PATH",
]
