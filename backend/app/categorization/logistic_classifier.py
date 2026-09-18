"""
Baseline Logistic Regression Classifier for Transaction Categorization (Task 3.3).

Trains on 384-dimensional sentence-transformers embeddings across the 12 canonical categories.
Supports cross-validation, serialized artifact persistence, and confidence scoring.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np

if TYPE_CHECKING:
    from sklearn.linear_model import LogisticRegression

from app.categorization.embedder import (
    TransactionEmbedder,
    get_transaction_embedder,
)

DEFAULT_MODEL_PATH: Path = Path("data/categorization/models/logistic_regression.joblib")


class LogisticRegressionClassifier:
    """
    Multiclass Logistic Regression Classifier wrapped for transaction narration categorization.
    """

    def __init__(
        self,
        C: float = 2.0,
        max_iter: int = 1000,
        random_state: int = 42,
        class_weight: Optional[str] = "balanced",
    ):
        self.C = C
        self.max_iter = max_iter
        self.random_state = random_state
        self.class_weight = class_weight
        self.model: Optional[LogisticRegression] = None
        self.classes_: List[str] = []

    def fit(self, X: np.ndarray, y: List[str]) -> "LogisticRegressionClassifier":
        """Fits the logistic regression model on input embedding matrix X and label list y."""
        from sklearn.linear_model import LogisticRegression

        X_arr = np.asarray(X, dtype=np.float32)
        y_arr = np.asarray(y, dtype=object)

        self.model = LogisticRegression(
            C=self.C,
            max_iter=self.max_iter,
            random_state=self.random_state,
            class_weight=self.class_weight,
            solver="lbfgs",
        )
        self.model.fit(X_arr, y_arr)
        self.classes_ = list(self.model.classes_)
        return self

    def predict(self, X: np.ndarray) -> List[str]:
        """Predicts categories for given embedding matrix X."""
        if self.model is None:
            raise RuntimeError("Model is not fitted. Call fit() or load() first.")
        X_arr = np.asarray(X, dtype=np.float32)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)
        preds = self.model.predict(X_arr)
        return [str(p) for p in preds]

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
        Embeds raw transaction description text(s) and predicts (category, confidence).
        Returns a list of (category, confidence_probability) tuples.
        """
        if self.model is None:
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
            category = self.classes_[best_idx]
            confidence = float(probs[idx][best_idx])
            results.append((category, round(confidence, 4)))

        return results

    def save(self, model_path: Union[str, Path] = DEFAULT_MODEL_PATH) -> Path:
        """Serializes the classifier state and sklearn model to disk via joblib."""
        if self.model is None:
            raise RuntimeError("Cannot save an unfitted model.")
        p = Path(model_path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "C": self.C,
            "max_iter": self.max_iter,
            "random_state": self.random_state,
            "class_weight": self.class_weight,
            "classes_": self.classes_,
            "sklearn_model": self.model,
        }
        joblib.dump(payload, str(p))
        return p

    @classmethod
    def load(cls, model_path: Union[str, Path] = DEFAULT_MODEL_PATH) -> "LogisticRegressionClassifier":
        """Loads a saved classifier artifact from disk."""
        p = Path(model_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Model file not found at: {p}")
        payload = joblib.load(str(p))
        instance = cls(
            C=payload.get("C", 2.0),
            max_iter=payload.get("max_iter", 1000),
            random_state=payload.get("random_state", 42),
            class_weight=payload.get("class_weight", "balanced"),
        )
        instance.classes_ = payload["classes_"]
        instance.model = payload["sklearn_model"]
        return instance


def train_baseline_logistic(
    test_size: float = 0.2,
    C: float = 2.0,
    random_state: int = 42,
    output_model_path: Optional[Union[str, Path]] = DEFAULT_MODEL_PATH,
) -> Tuple[LogisticRegressionClassifier, Dict[str, Any]]:
    """
    Trains the baseline Logistic Regression classifier on the labeled transaction dataset.
    Performs train/test holdout evaluation and saves the model artifact.

    Returns:
        (classifier: LogisticRegressionClassifier, eval_metrics: Dict[str, Any])
    """
    from sklearn.metrics import accuracy_score, classification_report, f1_score
    from sklearn.model_selection import train_test_split

    embedder = get_transaction_embedder()
    embeddings, descriptions, categories = embedder.embed_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        embeddings,
        categories,
        test_size=test_size,
        random_state=random_state,
        stratify=categories,
    )

    clf = LogisticRegressionClassifier(C=C, random_state=random_state)
    clf.fit(X_train, y_train)

    # Evaluate on holdout test split
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

    # Retrain on full dataset for maximum production accuracy and save
    full_clf = LogisticRegressionClassifier(C=C, random_state=random_state)
    full_clf.fit(embeddings, categories)

    if output_model_path:
        full_clf.save(output_model_path)

    return full_clf, metrics


_TRAINED_LOGISTIC_CLASSIFIER: Optional[LogisticRegressionClassifier] = None


def get_trained_logistic_classifier(
    model_path: Union[str, Path] = DEFAULT_MODEL_PATH,
) -> LogisticRegressionClassifier:
    """Returns a trained LogisticRegressionClassifier singleton, loading or training as needed."""
    global _TRAINED_LOGISTIC_CLASSIFIER
    if _TRAINED_LOGISTIC_CLASSIFIER is not None:
        return _TRAINED_LOGISTIC_CLASSIFIER

    p = Path(model_path).resolve()
    if p.exists():
        _TRAINED_LOGISTIC_CLASSIFIER = LogisticRegressionClassifier.load(p)
    else:
        _TRAINED_LOGISTIC_CLASSIFIER, _ = train_baseline_logistic(output_model_path=p)

    return _TRAINED_LOGISTIC_CLASSIFIER
