"""
Transaction Categorization Service with Hybrid Tiering (Pattern Matcher + XGBoost/ML + LLM).

Applies a multi-tiered classification pipeline:
1. Tier 1: Deterministic Indian Merchant & UPI Pattern Matcher (< 0.1ms).
2. Tier 2: Embedder + Configurable ML Classifier (XGBoost / Logistic Regression).
3. Tier 3: OpenRouter LLM Batch Categorizer for low-confidence / ambiguous items.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from pydantic import BaseModel, Field

from app.categorization.embedder import TransactionEmbedder, get_transaction_embedder
from app.categorization.indian_merchants import match_merchant_pattern
from app.categorization.logistic_classifier import (
    LogisticRegressionClassifier,
    get_trained_logistic_classifier,
)
from app.categorization.xgboost_classifier import (
    XGBoostTransactionClassifier,
    get_trained_xgboost_classifier,
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
    clean_merchant: Optional[str] = Field(default=None, description="Cleaned merchant or entity name")
    source: str = Field(default="ml", description="Source: 'pattern', 'xgboost', 'logistic', or 'llm'")


class TransactionCategorizer:
    """
    Categorization engine applying:
    1. Deterministic Indian merchant pattern recognition
    2. Sentence-transformer embeddings + XGBoost / Logistic classifier
    3. LLM fallback for ambiguous / uncategorized items
    """

    def __init__(
        self,
        classifier: Optional[Union[XGBoostTransactionClassifier, LogisticRegressionClassifier]] = None,
        embedder: Optional[TransactionEmbedder] = None,
        model_type: str = "xgboost",
        default_threshold: float = DEFAULT_CATEGORIZATION_CONFIDENCE_THRESHOLD,
    ):
        self.default_threshold = default_threshold
        self.model_type = model_type.lower()
        self._classifier = classifier
        self._embedder = embedder

    @property
    def classifier(self) -> Union[XGBoostTransactionClassifier, LogisticRegressionClassifier]:
        if self._classifier is None:
            if self.model_type == "xgboost":
                self._classifier = get_trained_xgboost_classifier()
            else:
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
        use_llm_fallback: bool = False,
        user_id: int = 1,
    ) -> CategorizationResult:
        """Categorizes a single transaction narration with confidence thresholding."""
        results = self.categorize_batch(
            [description],
            threshold=threshold,
            use_llm_fallback=use_llm_fallback,
            user_id=user_id,
        )
        return results[0]

    def categorize_batch(
        self,
        descriptions: List[str],
        threshold: Optional[float] = None,
        use_llm_fallback: bool = False,
        user_id: int = 1,
    ) -> List[CategorizationResult]:
        """
        Batch categorizes a list of transaction narrations across Tier 1, Tier 2, and Tier 3.
        """
        effective_threshold = self.default_threshold if threshold is None else threshold

        if not descriptions:
            return []

        results: List[Optional[CategorizationResult]] = [None] * len(descriptions)
        unmatched_indices: List[int] = []

        # --- Tier 1: Deterministic Indian Merchant & UPI Pattern Matcher (< 0.1ms) ---
        for idx, desc in enumerate(descriptions):
            if not desc or not desc.strip():
                results[idx] = CategorizationResult(
                    category=UNCATEGORIZED_CATEGORY,
                    raw_predicted_category=UNCATEGORIZED_CATEGORY,
                    confidence=0.0,
                    needs_review=True,
                    is_thresholded=True,
                    threshold=effective_threshold,
                    clean_merchant=None,
                    source="rule",
                )
                continue

            matched = match_merchant_pattern(desc)
            if matched:
                cat, merchant, conf = matched
                if conf < effective_threshold:
                    results[idx] = CategorizationResult(
                        category=UNCATEGORIZED_CATEGORY,
                        raw_predicted_category=cat,
                        confidence=conf,
                        needs_review=True,
                        is_thresholded=True,
                        threshold=effective_threshold,
                        clean_merchant=merchant,
                        source="pattern",
                    )
                else:
                    results[idx] = CategorizationResult(
                        category=cat,
                        raw_predicted_category=cat,
                        confidence=conf,
                        needs_review=False,
                        is_thresholded=False,
                        threshold=effective_threshold,
                        clean_merchant=merchant,
                        source="pattern",
                    )
            else:
                unmatched_indices.append(idx)

        # --- Tier 2: XGBoost / ML Model on sentence embeddings ---
        if unmatched_indices:
            unmatched_texts = [descriptions[i] for i in unmatched_indices]
            embeddings = self.embedder.embed(unmatched_texts, normalize=True)
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(1, -1)

            probs = self.classifier.predict_proba(embeddings)
            best_indices = probs.argmax(axis=1)
            classes = self.classifier.classes_

            for pos, orig_idx in enumerate(unmatched_indices):
                best_idx = best_indices[pos]
                raw_cat = str(classes[best_idx])
                conf = float(probs[pos][best_idx])
                conf_rounded = round(conf, 4)

                if conf < effective_threshold:
                    assigned_category = UNCATEGORIZED_CATEGORY
                    needs_review = True
                    is_thresholded = True
                else:
                    assigned_category = raw_cat
                    needs_review = False
                    is_thresholded = False

                results[orig_idx] = CategorizationResult(
                    category=assigned_category,
                    raw_predicted_category=raw_cat,
                    confidence=conf_rounded,
                    needs_review=needs_review,
                    is_thresholded=is_thresholded,
                    threshold=effective_threshold,
                    clean_merchant=descriptions[orig_idx][:30],
                    source=self.model_type,
                )

        # --- Tier 3: LLM Batch Categorizer for Uncategorized items ---
        if use_llm_fallback:
            uncategorized_indices = [
                i for i, r in enumerate(results)
                if r is not None and r.category == UNCATEGORIZED_CATEGORY and descriptions[i].strip()
            ]

            if uncategorized_indices:
                try:
                    from app.categorization.llm_categorizer import categorize_batch_with_llm
                    uncategorized_texts = [descriptions[i] for i in uncategorized_indices]
                    llm_preds = categorize_batch_with_llm(uncategorized_texts, user_id=user_id)

                    for pos, orig_idx in enumerate(uncategorized_indices):
                        if pos < len(llm_preds):
                            lp = llm_preds[pos]
                            cat = lp.get("category", UNCATEGORIZED_CATEGORY)
                            conf = round(float(lp.get("confidence", 0.90)), 4)
                            if conf < effective_threshold or cat == UNCATEGORIZED_CATEGORY:
                                assigned_cat = UNCATEGORIZED_CATEGORY
                                needs_rev = True
                                is_thresh = True
                            else:
                                assigned_cat = cat
                                needs_rev = bool(lp.get("needs_review", False))
                                is_thresh = False

                            results[orig_idx] = CategorizationResult(
                                category=assigned_cat,
                                raw_predicted_category=cat,
                                confidence=conf,
                                needs_review=needs_rev,
                                is_thresholded=is_thresh,
                                threshold=effective_threshold,
                                clean_merchant=lp.get("merchant", descriptions[orig_idx][:30]),
                                source="llm",
                            )
                except Exception as e:
                    # Non-fatal; keep ML predictions
                    pass

        # Final pass: Ensure all results are populated
        final_results: List[CategorizationResult] = []
        for idx, res in enumerate(results):
            if res is None:
                final_results.append(
                    CategorizationResult(
                        category=UNCATEGORIZED_CATEGORY,
                        raw_predicted_category=UNCATEGORIZED_CATEGORY,
                        confidence=0.0,
                        needs_review=True,
                        is_thresholded=True,
                        threshold=effective_threshold,
                        clean_merchant=descriptions[idx][:30] if descriptions[idx] else None,
                        source="unknown",
                    )
                )
            else:
                final_results.append(res)

        return final_results

    def apply_to_parsed_rows(
        self,
        rows: List[ParsedTransactionRow],
        threshold: Optional[float] = None,
        use_llm_fallback: bool = True,
        user_id: int = 1,
    ) -> List[Tuple[ParsedTransactionRow, CategorizationResult]]:
        """Batch categorizes a list of ParsedTransactionRow objects."""
        if not rows:
            return []

        descriptions = [r.description for r in rows]
        results = self.categorize_batch(
            descriptions,
            threshold=threshold,
            use_llm_fallback=use_llm_fallback,
            user_id=user_id,
        )

        annotated: List[Tuple[ParsedTransactionRow, CategorizationResult]] = []
        for row, res in zip(rows, results):
            if res.needs_review:
                row.needs_review = True
            if res.clean_merchant:
                row.cleaned_description = res.clean_merchant
            annotated.append((row, res))

        return annotated

    def apply_to_parsed_row(
        self,
        row: ParsedTransactionRow,
        threshold: Optional[float] = None,
        use_llm_fallback: bool = True,
        user_id: int = 1,
    ) -> Tuple[ParsedTransactionRow, CategorizationResult]:
        """Convenience method to categorize a single ParsedTransactionRow."""
        annotated = self.apply_to_parsed_rows(
            [row],
            threshold=threshold,
            use_llm_fallback=use_llm_fallback,
            user_id=user_id,
        )
        return annotated[0]


_CATEGORIZER_SINGLETON: Optional[TransactionCategorizer] = None


def get_transaction_categorizer(
    threshold: float = DEFAULT_CATEGORIZATION_CONFIDENCE_THRESHOLD,
    model_type: str = "xgboost",
) -> TransactionCategorizer:
    """Returns the singleton instance of TransactionCategorizer (defaulting to XGBoost)."""
    global _CATEGORIZER_SINGLETON
    if _CATEGORIZER_SINGLETON is None:
        _CATEGORIZER_SINGLETON = TransactionCategorizer(
            default_threshold=threshold,
            model_type=model_type,
        )
    return _CATEGORIZER_SINGLETON
