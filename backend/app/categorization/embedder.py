"""
Transaction narration embedder using sentence-transformers (Task 3.2).

Produces 384-dimensional dense semantic vectors using 'all-MiniLM-L6-v2'
with caching and batch processing support for transaction categorization.
"""

import csv
from pathlib import Path
from typing import List, Optional, Tuple, Union
import numpy as np
from sentence_transformers import SentenceTransformer

# Model configuration constants
DEFAULT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION: int = 384
DEFAULT_DATASET_PATH: Path = Path("data/categorization/transactions_labeled_dataset.csv")
DEFAULT_CACHE_PATH: Path = Path("data/categorization/dataset_embeddings.npz")


class TransactionEmbedder:
    """
    Wraps sentence-transformers to encode bank narrations and descriptions
    into normalized dense vectors for downstream classifiers.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.device = device
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy loads the underlying sentence-transformers model."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def preprocess(self, text: str) -> str:
        """
        Normalizes transaction description for embedding.
        Strips non-essential whitespace while preserving UPI handles, dates, and keywords.
        """
        if not text:
            return ""
        clean = " ".join(str(text).strip().split())
        return clean

    def embed(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 64,
        normalize: bool = True,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """
        Encodes one or more text descriptions into dense numpy arrays.
        - Single string returns 1D array of shape (384,).
        - List of strings returns 2D array of shape (N, 384).
        """
        is_single = isinstance(texts, str)
        text_list = [texts] if is_single else list(texts)

        if not text_list:
            return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)

        processed_texts = [self.preprocess(t) for t in text_list]

        embeddings = self.model.encode(
            processed_texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
        )

        embeddings = np.asarray(embeddings, dtype=np.float32)

        if is_single:
            return embeddings[0]
        return embeddings

    def embed_dataset(
        self,
        csv_path: Union[str, Path] = DEFAULT_DATASET_PATH,
        cache_path: Optional[Union[str, Path]] = DEFAULT_CACHE_PATH,
        force_recompute: bool = False,
        show_progress_bar: bool = False,
    ) -> Tuple[np.ndarray, List[str], List[str]]:
        """
        Loads the labeled dataset, generates embeddings, and caches them to disk.
        Returns:
            (embeddings: np.ndarray [N, 384], descriptions: List[str], categories: List[str])
        """
        csv_p = Path(csv_path).resolve()
        if not csv_p.exists():
            raise FileNotFoundError(f"Labeled dataset not found at: {csv_p}")

        cache_p = Path(cache_path).resolve() if cache_path else None

        # Check if valid cache exists
        if not force_recompute and cache_p and cache_p.exists():
            try:
                data = np.load(str(cache_p), allow_pickle=True)
                embeddings = data["embeddings"].astype(np.float32)
                descriptions = [str(d) for d in data["descriptions"]]
                categories = [str(c) for c in data["categories"]]
                if (
                    embeddings.ndim == 2
                    and embeddings.shape[1] == EMBEDDING_DIMENSION
                    and len(descriptions) == len(embeddings)
                    and len(categories) == len(embeddings)
                ):
                    return embeddings, descriptions, categories
            except Exception:
                pass  # Fall back to recomputing if cache is corrupted

        descriptions: List[str] = []
        categories: List[str] = []

        with open(csv_p, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                descriptions.append(row["description"].strip())
                categories.append(row["category"].strip())

        embeddings = self.embed(
            descriptions,
            batch_size=64,
            normalize=True,
            show_progress_bar=show_progress_bar,
        )

        # Save to disk cache
        if cache_p:
            cache_p.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(
                str(cache_p),
                embeddings=embeddings,
                descriptions=np.array(descriptions, dtype=object),
                categories=np.array(categories, dtype=object),
            )

        return embeddings, descriptions, categories


# Singleton instance
_GLOBAL_EMBEDDER: Optional[TransactionEmbedder] = None


def get_transaction_embedder(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> TransactionEmbedder:
    """Returns a shared TransactionEmbedder singleton."""
    global _GLOBAL_EMBEDDER
    if _GLOBAL_EMBEDDER is None or _GLOBAL_EMBEDDER.model_name != model_name:
        _GLOBAL_EMBEDDER = TransactionEmbedder(model_name=model_name)
    return _GLOBAL_EMBEDDER
