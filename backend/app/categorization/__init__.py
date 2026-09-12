"""
ML Categorization Pipeline for Transaction Narrations (Phase 3).
"""

from app.categorization.embedder import (
    DEFAULT_CACHE_PATH,
    DEFAULT_DATASET_PATH,
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    TransactionEmbedder,
    get_transaction_embedder,
)

__all__ = [
    "DEFAULT_CACHE_PATH",
    "DEFAULT_DATASET_PATH",
    "DEFAULT_EMBEDDING_MODEL",
    "EMBEDDING_DIMENSION",
    "TransactionEmbedder",
    "get_transaction_embedder",
]
