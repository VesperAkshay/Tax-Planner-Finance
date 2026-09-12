"""
Unit tests for Task 3.2: sentence-transformers embedding pipeline.
"""

from pathlib import Path
import numpy as np
import pytest

from app.categorization.embedder import (
    DEFAULT_CACHE_PATH,
    DEFAULT_DATASET_PATH,
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    TransactionEmbedder,
    get_transaction_embedder,
)


def test_embedder_defaults_and_constants():
    """Verify embedder default constants match project specifications."""
    assert DEFAULT_EMBEDDING_MODEL == "all-MiniLM-L6-v2"
    assert EMBEDDING_DIMENSION == 384
    embedder = get_transaction_embedder()
    assert embedder.model_name == DEFAULT_EMBEDDING_MODEL


def test_single_and_batch_embedding_shapes():
    """Verify single and batch text embeddings produce expected dimensionalities."""
    embedder = get_transaction_embedder()

    # Single text embedding -> 1D array of shape (384,)
    single_emb = embedder.embed("UPI-SWIGGY-FOOD-ORDER")
    assert isinstance(single_emb, np.ndarray)
    assert single_emb.shape == (384,)
    assert single_emb.dtype == np.float32

    # Batch texts embedding -> 2D array of shape (N, 384)
    batch_texts = [
        "UPI-SWIGGY-FOOD-ORDER",
        "SALARY CREDIT INFOSYS LIMITED",
        "NEFT-RENT PAYMENT TO LANDLORD",
    ]
    batch_embs = embedder.embed(batch_texts)
    assert isinstance(batch_embs, np.ndarray)
    assert batch_embs.shape == (3, 384)
    assert batch_embs.dtype == np.float32


def test_embeddings_are_l2_normalized():
    """Verify embeddings have unit L2 norm (enabling cosine similarity via dot product)."""
    embedder = get_transaction_embedder()
    texts = [
        "POS 412345 RELIANCE FRESH BANGALORE",
        "UPI/DR/12345/bescom@billdesk/Electricity Bill",
    ]
    embs = embedder.embed(texts, normalize=True)
    for row in embs:
        norm = np.linalg.norm(row)
        assert abs(norm - 1.0) < 1e-4, f"Embedding not normalized to 1.0: {norm}"


def test_semantic_similarity_behavior():
    """Verify semantically related descriptions have significantly higher cosine similarity."""
    embedder = get_transaction_embedder()

    # Swiggy and Zomato should be semantically close (both food dining/delivery)
    swiggy = embedder.embed("UPI-SWIGGY-swiggy@icici-Food Delivery")
    zomato = embedder.embed("UPI-ZOMATO-zomato@hdfcbank-Restaurant Food Order")

    # Salary should be semantically distant from food delivery
    salary = embedder.embed("ACH/CREDIT/TCS LIMITED/SALARY CREDIT JUNE 2025")

    sim_swiggy_zomato = np.dot(swiggy, zomato)
    sim_swiggy_salary = np.dot(swiggy, salary)

    assert sim_swiggy_zomato > 0.40, f"Expected high similarity between food deliveries: {sim_swiggy_zomato}"
    assert sim_swiggy_salary < 0.15, f"Expected low similarity between food and salary: {sim_swiggy_salary}"
    assert sim_swiggy_zomato > sim_swiggy_salary + 0.30


def test_embed_dataset_caching_and_integrity(tmp_path: Path):
    """Verify embed_dataset processes the 720 dataset samples and roundtrips through disk cache."""
    assert DEFAULT_DATASET_PATH.exists(), "Labeled dataset must exist"

    embedder = get_transaction_embedder()
    test_cache_path = tmp_path / "test_embeddings.npz"

    # 1. Compute and save to test cache
    embs, descs, cats = embedder.embed_dataset(
        csv_path=DEFAULT_DATASET_PATH,
        cache_path=test_cache_path,
        force_recompute=True,
    )
    assert embs.shape == (720, 384)
    assert len(descs) == 720
    assert len(cats) == 720
    assert test_cache_path.exists()

    # 2. Fast reload from disk cache
    cached_embs, cached_descs, cached_cats = embedder.embed_dataset(
        csv_path=DEFAULT_DATASET_PATH,
        cache_path=test_cache_path,
        force_recompute=False,
    )
    assert np.allclose(embs, cached_embs, atol=1e-5)
    assert descs == cached_descs
    assert cats == cached_cats
