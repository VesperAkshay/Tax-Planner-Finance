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
from app.categorization.logistic_classifier import (
    DEFAULT_MODEL_PATH as DEFAULT_LOGISTIC_MODEL_PATH,
    LogisticRegressionClassifier,
    get_trained_logistic_classifier,
    train_baseline_logistic,
)

__all__ = [
    "DEFAULT_CACHE_PATH",
    "DEFAULT_DATASET_PATH",
    "DEFAULT_EMBEDDING_MODEL",
    "DEFAULT_LOGISTIC_MODEL_PATH",
    "EMBEDDING_DIMENSION",
    "LogisticRegressionClassifier",
    "TransactionEmbedder",
    "get_trained_logistic_classifier",
    "get_transaction_embedder",
    "train_baseline_logistic",
]
