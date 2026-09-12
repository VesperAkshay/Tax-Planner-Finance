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
from app.categorization.xgboost_classifier import (
    DEFAULT_XGBOOST_MODEL_PATH,
    XGBoostTransactionClassifier,
    compare_logistic_vs_xgboost,
    get_trained_xgboost_classifier,
    train_xgboost_classifier,
)

from app.categorization.evaluator import (
    DEFAULT_REPORT_PATH,
    compute_holdout_metrics,
    generate_categorization_eval_report,
)

__all__ = [
    "DEFAULT_CACHE_PATH",
    "DEFAULT_DATASET_PATH",
    "DEFAULT_EMBEDDING_MODEL",
    "DEFAULT_LOGISTIC_MODEL_PATH",
    "DEFAULT_REPORT_PATH",
    "DEFAULT_XGBOOST_MODEL_PATH",
    "EMBEDDING_DIMENSION",
    "LogisticRegressionClassifier",
    "TransactionEmbedder",
    "XGBoostTransactionClassifier",
    "compare_logistic_vs_xgboost",
    "compute_holdout_metrics",
    "generate_categorization_eval_report",
    "get_trained_logistic_classifier",
    "get_trained_xgboost_classifier",
    "get_transaction_embedder",
    "train_baseline_logistic",
    "train_xgboost_classifier",
]
