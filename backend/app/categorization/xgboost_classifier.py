"""
XGBoost Classifier for Transaction Categorization (Task 3.4).

Trains an XGBoost gradient-boosted decision tree classifier on 384-dimensional
sentence-transformers embeddings, with label encoding, serialization, and comparison against baseline.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from app.categorization.embedder import (
    TransactionEmbedder,
    get_transaction_embedder,
)

DEFAULT_XGBOOST_MODEL_PATH: Path = Path("data/categorization/models/xgboost_classifier.joblib")


class XGBoostTransactionClassifier:
    """
    Multiclass XGBoost Classifier for transaction narration categorization.
    Handles internal integer label encoding and probability distribution outputs.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        learning_rate: float = 0.1,
        max_depth: int = 4,
        random_state: int = 42,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_state = random_state
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.model: Optional[XGBClassifier] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self.classes_: List[str] = []

    def fit(self, X: np.ndarray, y: List[str]) -> "XGBoostTransactionClassifier":
        """Fits label encoder and XGBoost model on input embedding matrix X and category strings y."""
        X_arr = np.asarray(X, dtype=np.float32)
        y_list = list(y)

        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y_list)
        self.classes_ = list(self.label_encoder.classes_)

        self.model = XGBClassifier(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            random_state=self.random_state,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            eval_metric="mlogloss",
            verbosity=0,
        )
        self.model.fit(X_arr, y_encoded)
        return self

    def predict(self, X: np.ndarray) -> List[str]:
        """Predicts category strings for given embedding matrix X."""
        if self.model is None or self.label_encoder is None:
            raise RuntimeError("Model is not fitted. Call fit() or load() first.")
        X_arr = np.asarray(X, dtype=np.float32)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)
        encoded_preds = self.model.predict(X_arr)
        return list(self.label_encoder.inverse_transform(encoded_preds))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Returns category probability distributions for embedding matrix X."""
        if self.model is None:
            raise RuntimeError("Model is not fitted. Call fit() or load() first.")
        X_arr = np.asarray(X, dtype=np.float32)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)
        return self.model.predict_proba(X_arr)

    def predict_with_confidence(
        self,
        texts: Union[str, List[str]],
        embedder: Optional[TransactionEmbedder] = None,
    ) -> List[Tuple[str, float]]:
        """
        Embeds raw transaction text(s) and predicts (category, confidence).
        Returns list of (category, confidence_probability) tuples.
        """
        if self.model is None or self.label_encoder is None:
            raise RuntimeError("Model is not fitted. Call fit() or load() first.")

        emb_client = embedder or get_transaction_embedder()
        is_single = isinstance(texts, str)
        text_list = [texts] if is_single else list(texts)

        if not text_list:
            return []

        embeddings = emb_client.embed(text_list, normalize=True)
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        probs = self.predict_proba(embeddings)
        best_indices = np.argmax(probs, axis=1)

        results: List[Tuple[str, float]] = []
        for idx, best_idx in enumerate(best_indices):
            category = str(self.classes_[best_idx])
            confidence = float(probs[idx][best_idx])
            results.append((category, round(confidence, 4)))

        return results

    def save(self, model_path: Union[str, Path] = DEFAULT_XGBOOST_MODEL_PATH) -> Path:
        """Serializes the classifier state, label encoder, and XGBoost model via joblib."""
        if self.model is None or self.label_encoder is None:
            raise RuntimeError("Cannot save an unfitted model.")
        p = Path(model_path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "n_estimators": self.n_estimators,
            "learning_rate": self.learning_rate,
            "max_depth": self.max_depth,
            "random_state": self.random_state,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "classes_": self.classes_,
            "label_encoder": self.label_encoder,
            "xgb_model": self.model,
        }
        joblib.dump(payload, str(p))
        return p

    @classmethod
    def load(cls, model_path: Union[str, Path] = DEFAULT_XGBOOST_MODEL_PATH) -> "XGBoostTransactionClassifier":
        """Loads a saved XGBoost classifier artifact from disk."""
        p = Path(model_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Model file not found at: {p}")
        payload = joblib.load(str(p))
        instance = cls(
            n_estimators=payload.get("n_estimators", 100),
            learning_rate=payload.get("learning_rate", 0.1),
            max_depth=payload.get("max_depth", 4),
            random_state=payload.get("random_state", 42),
            subsample=payload.get("subsample", 0.8),
            colsample_bytree=payload.get("colsample_bytree", 0.8),
        )
        instance.classes_ = payload["classes_"]
        instance.label_encoder = payload["label_encoder"]
        instance.model = payload["xgb_model"]
        return instance


def train_xgboost_classifier(
    test_size: float = 0.2,
    random_state: int = 42,
    output_model_path: Optional[Union[str, Path]] = DEFAULT_XGBOOST_MODEL_PATH,
) -> Tuple[XGBoostTransactionClassifier, Dict[str, Any]]:
    """
    Trains the XGBoost classifier on the labeled transaction dataset.
    Performs train/test holdout evaluation and saves the model artifact.
    """
    embedder = get_transaction_embedder()
    embeddings, descriptions, categories = embedder.embed_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        embeddings,
        categories,
        test_size=test_size,
        random_state=random_state,
        stratify=categories,
    )

    clf = XGBoostTransactionClassifier(random_state=random_state)
    clf.fit(X_train, y_train)

    test_preds = clf.predict(X_test)
    test_acc = float(accuracy_score(y_test, test_preds))
    macro_f1 = float(f1_score(y_test, test_preds, average="macro"))
    weighted_f1 = float(f1_score(y_test, test_preds, average="weighted"))
    report = classification_report(y_test, test_preds, output_dict=True)

    metrics = {
        "holdout_accuracy": round(test_acc, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "classification_report": report,
    }

    # Retrain on full dataset and save artifact
    full_clf = XGBoostTransactionClassifier(random_state=random_state)
    full_clf.fit(embeddings, categories)

    if output_model_path:
        full_clf.save(output_model_path)

    return full_clf, metrics


def compare_logistic_vs_xgboost(
    test_size: float = 0.2, random_state: int = 42
) -> Dict[str, Any]:
    """
    Compares Baseline Logistic Regression against XGBoost on the same train/test split (Task 3.4).
    """
    from app.categorization.logistic_classifier import LogisticRegressionClassifier

    embedder = get_transaction_embedder()
    embeddings, descriptions, categories = embedder.embed_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        embeddings,
        categories,
        test_size=test_size,
        random_state=random_state,
        stratify=categories,
    )

    # 1. Baseline Logistic Regression
    lr = LogisticRegressionClassifier(C=2.0, random_state=random_state)
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)
    lr_acc = float(accuracy_score(y_test, lr_preds))
    lr_macro_f1 = float(f1_score(y_test, lr_preds, average="macro"))

    # 2. XGBoost
    xgb = XGBoostTransactionClassifier(random_state=random_state)
    xgb.fit(X_train, y_train)
    xgb_preds = xgb.predict(X_test)
    xgb_acc = float(accuracy_score(y_test, xgb_preds))
    xgb_macro_f1 = float(f1_score(y_test, xgb_preds, average="macro"))

    return {
        "logistic_regression": {
            "accuracy": round(lr_acc, 4),
            "macro_f1": round(lr_macro_f1, 4),
        },
        "xgboost": {
            "accuracy": round(xgb_acc, 4),
            "macro_f1": round(xgb_macro_f1, 4),
        },
        "winner": "logistic_regression" if lr_acc >= xgb_acc else "xgboost",
        "difference_accuracy": round(abs(lr_acc - xgb_acc), 4),
    }


_TRAINED_XGBOOST_CLASSIFIER: Optional[XGBoostTransactionClassifier] = None


def get_trained_xgboost_classifier(
    model_path: Union[str, Path] = DEFAULT_XGBOOST_MODEL_PATH,
) -> XGBoostTransactionClassifier:
    """Returns a trained XGBoostTransactionClassifier singleton, loading or training as needed."""
    global _TRAINED_XGBOOST_CLASSIFIER
    if _TRAINED_XGBOOST_CLASSIFIER is not None:
        return _TRAINED_XGBOOST_CLASSIFIER

    p = Path(model_path).resolve()
    if p.exists():
        _TRAINED_XGBOOST_CLASSIFIER = XGBoostTransactionClassifier.load(p)
    else:
        _TRAINED_XGBOOST_CLASSIFIER, _ = train_xgboost_classifier(output_model_path=p)

    return _TRAINED_XGBOOST_CLASSIFIER
