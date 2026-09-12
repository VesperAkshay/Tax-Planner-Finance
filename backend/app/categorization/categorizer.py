"""
Transaction Categorization Service with Confidence Thresholding (Task 3.6).

Applies confidence thresholding: predictions with confidence below the configured
threshold set category = "Uncategorized" and needs_review = True.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from app.categorization.embedder import TransactionEmbedder, get_transaction_embedder
from app.categorization.logistic_classifier import (
    LogisticRegressionClassifier,
    get_trained_logistic_classifier,
)
from app.parsing.schemas import ParsedTransactionRow

DEFAULT_CATEGORIZATION_CONFIDENCE_THRESHOLD: float = 0.60
UNCATEGORIZED_CATEGORY: str = "Uncategorized"


class CategorizationResult(BaseModel):
    """Structured result of categorizing a transaction narration with confidence thresholding."""

    category: str = Field(description="Final assigned category (or 'Uncategorized' if below threshold)")
    raw_predicted_category: str = Field(description="Top model prediction prior to threshold check")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score / probability of top prediction")
    needs_review: bool = Field(description="Flag indicating if manual human review is required")
    is_thresholded: bool = Field(description="True if category was set to Uncategorized due to low confidence")
    threshold: float = Field(description="The threshold value applied during categorization")


class TransactionCategorizer:
    """
    Categorization engine applying sentence-transformer embeddings,
    multiclass classifier inference, and confidence thresholding.
    """

    def __init__(
        self,
        classifier: Optional[LogisticRegressionClassifier] = None,
        embedder: Optional[TransactionEmbedder] = None,
        default_threshold: float = DEFAULT_CATEGORIZATION_CONFIDENCE_THRESHOLD,
    ):
        self.default_threshold = default_threshold
        self._classifier = classifier
        self._embedder = embedder

    @property
    def classifier(self) -> LogisticRegressionClassifier:
        if self._classifier is None:
            self._classifier = get_trained_logistic_classifier()
        return self._classifier

    @property
    def embedder(self) -> TransactionEmbedder:
        if self._embedder is None:
            self._embedder = get_transaction_embedder()
        return self._embedder

    def categorize(
        self,
        description: str,
        threshold: Optional[float] = None,
    ) -> CategorizationResult:
        """
        Categorizes a single transaction narration with confidence thresholding.
        If confidence < threshold, category is set to 'Uncategorized' and needs_review = True.
        """
        results = self.categorize_batch([description], threshold=threshold)
        return results[0]

    def categorize_batch(
        self,
        descriptions: List[str],
        threshold: Optional[float] = None,
    ) -> List[CategorizationResult]:
        """
        Batch categorizes a list of transaction narrations.
        Efficiently embeds and scores narrations in batches.
        """
        effective_threshold = self.default_threshold if threshold is None else threshold

        if not descriptions:
            return []

        # Handle empty/blank descriptions
        non_empty_indices = [i for i, d in enumerate(descriptions) if d and d.strip()]
        if not non_empty_indices:
            return [
                CategorizationResult(
                    category=UNCATEGORIZED_CATEGORY,
                    raw_predicted_category=UNCATEGORIZED_CATEGORY,
                    confidence=0.0,
                    needs_review=True,
                    is_thresholded=True,
                    threshold=effective_threshold,
                )
                for _ in descriptions
            ]

        # Embed descriptions
        embeddings = self.embedder.embed(descriptions, normalize=True)
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        # Get probabilities and top predictions
        probs = self.classifier.predict_proba(embeddings)
        best_indices = probs.argmax(axis=1)
        classes = self.classifier.classes_

        results: List[CategorizationResult] = []
        for idx in range(len(descriptions)):
            desc = descriptions[idx]
            if not desc or not desc.strip():
                results.append(
                    CategorizationResult(
                        category=UNCATEGORIZED_CATEGORY,
                        raw_predicted_category=UNCATEGORIZED_CATEGORY,
                        confidence=0.0,
                        needs_review=True,
                        is_thresholded=True,
                        threshold=effective_threshold,
                    )
                )
                continue

            best_idx = best_indices[idx]
            raw_cat = classes[best_idx]
            conf = float(probs[idx][best_idx])
            conf_rounded = round(conf, 4)

            # Apply confidence thresholding per Task 3.6
            if conf < effective_threshold:
                assigned_category = UNCATEGORIZED_CATEGORY
                needs_review = True
                is_thresholded = True
            else:
                assigned_category = raw_cat
                needs_review = False
                is_thresholded = False

            results.append(
                CategorizationResult(
                    category=assigned_category,
                    raw_predicted_category=raw_cat,
                    confidence=conf_rounded,
                    needs_review=needs_review,
                    is_thresholded=is_thresholded,
                    threshold=effective_threshold,
                )
            )

        return results

    def apply_to_parsed_row(
        self,
        row: ParsedTransactionRow,
        threshold: Optional[float] = None,
    ) -> Tuple[ParsedTransactionRow, CategorizationResult]:
        """
        Categorizes a ParsedTransactionRow and updates its needs_review flag.
        Preserves existing parse-level review flags if already True.
        """
        result = self.categorize(row.description, threshold=threshold)
        if result.needs_review:
            row.needs_review = True
        return row, result

    def apply_to_parsed_rows(
        self,
        rows: List[ParsedTransactionRow],
        threshold: Optional[float] = None,
    ) -> List[Tuple[ParsedTransactionRow, CategorizationResult]]:
        """
        Batch categorizes a list of ParsedTransactionRow objects.
        """
        if not rows:
            return []

        descriptions = [r.description for r in rows]
        results = self.categorize_batch(descriptions, threshold=threshold)

        annotated: List[Tuple[ParsedTransactionRow, CategorizationResult]] = []
        for row, res in zip(rows, results):
            if res.needs_review:
                row.needs_review = True
            annotated.append((row, res))

        return annotated


_CATEGORIZER_SINGLETON: Optional[TransactionCategorizer] = None


def get_transaction_categorizer(
    threshold: float = DEFAULT_CATEGORIZATION_CONFIDENCE_THRESHOLD,
) -> TransactionCategorizer:
    """Returns the singleton instance of TransactionCategorizer."""
    global _CATEGORIZER_SINGLETON
    if _CATEGORIZER_SINGLETON is None:
        _CATEGORIZER_SINGLETON = TransactionCategorizer(default_threshold=threshold)
    return _CATEGORIZER_SINGLETON
