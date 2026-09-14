"""
Tax Rules RAG Layer (Tasks 6.2 & 6.3).

Embeds and indexes curated tax rule chunks into ChromaDB and provides
top-k semantic retrieval with metadata (source_url, section, financial_year, regime).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import chromadb
from chromadb.api.models.Collection import Collection

from app.categorization.embedder import TransactionEmbedder, get_transaction_embedder

logger = logging.getLogger(__name__)

DEFAULT_CHROMA_DIR: Path = Path("data/chroma_db")
DEFAULT_COLLECTION_NAME: str = "tax_rules_fy_2025_26"
DEFAULT_CORPUS_PATH: Path = Path("data/rag/tax_rules_corpus_fy_2025_26.json")


class TaxRAGService:
    """
    RAG service managing ChromaDB persistent vector storage and semantic retrieval
    for Indian Income Tax Act rules (FY 2025-26).
    """

    def __init__(
        self,
        chroma_dir: Optional[Union[str, Path]] = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        embedder: Optional[TransactionEmbedder] = None,
    ):
        self.chroma_dir = Path(chroma_dir).resolve() if chroma_dir else DEFAULT_CHROMA_DIR.resolve()
        self.collection_name = collection_name
        self.embedder = embedder or get_transaction_embedder()
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection: Optional[Collection] = None

    @property
    def client(self) -> chromadb.PersistentClient:
        """Lazy-loaded ChromaDB persistent client."""
        if self._client is None:
            self.chroma_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self.chroma_dir))
        return self._client

    @property
    def collection(self) -> Collection:
        """Lazy-loaded or created ChromaDB collection with cosine distance."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            # If collection is newly created or empty, automatically index default corpus
            if self._collection.count() == 0 and DEFAULT_CORPUS_PATH.exists():
                self.index_corpus(DEFAULT_CORPUS_PATH)
        return self._collection

    def index_corpus(
        self,
        corpus_path: Optional[Union[str, Path]] = None,
        force_reindex: bool = False,
    ) -> int:
        """
        Loads rule chunks from the corpus JSON file, embeds them using SentenceTransformer,
        and upserts them into the ChromaDB collection (Task 6.2).

        Returns:
            Number of indexed chunks.
        """
        p = Path(corpus_path).resolve() if corpus_path else DEFAULT_CORPUS_PATH.resolve()
        if not p.exists():
            raise FileNotFoundError(f"Tax rules corpus file not found at: {p}")

        with open(p, "r", encoding="utf-8") as f:
            corpus_data = json.load(f)

        chunks = corpus_data.get("chunks", [])
        if not chunks:
            logger.warning(f"No chunks found in corpus at {p}")
            return 0

        # If already populated and not forcing reindex, return current count
        current_count = self.collection.count()
        if current_count >= len(chunks) and not force_reindex:
            logger.info(f"Collection already has {current_count} items. Skipping re-indexing.")
            return current_count

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            ids.append(chunk["id"])
            # Format composite text for semantic search
            tags_str = ", ".join(chunk.get("tags", []))
            doc_text = (
                f"Section: {chunk['section']} | Title: {chunk['title']}\n\n"
                f"{chunk['content']}\n\n"
                f"Keywords: {tags_str}"
            )
            documents.append(doc_text)
            metadatas.append({
                "chunk_id": chunk["id"],
                "section": chunk["section"],
                "title": chunk["title"],
                "financial_year": chunk["financial_year"],
                "source_url": chunk["source_url"],
                "regime_applicability": chunk.get("regime_applicability", "both"),
                "tags": tags_str,
            })

        # Compute dense embeddings using local SentenceTransformer
        embeddings = self.embedder.embed(documents, normalize=True)
        embeddings_list = [emb.tolist() for emb in embeddings]

        # Upsert into ChromaDB
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings_list,
        )

        logger.info(f"Successfully indexed {len(chunks)} tax rule chunks into collection '{self.collection_name}'.")
        return len(chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        section_filter: Optional[str] = None,
        regime_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic top-k retrieval of tax rule chunks for a given query (Task 6.3).

        Parameters:
            query: User or agent question / query string
            top_k: Number of most relevant results to return (default 3)
            section_filter: Optional filter by specific section (e.g. '80C', '80D')
            regime_filter: Optional filter by regime ('old', 'new', 'both')

        Returns:
            List of structured chunk results with metadata and similarity scores.
        """
        clean_query = self.embedder.preprocess(query)
        if not clean_query:
            return []

        # Embed query text
        query_vec = self.embedder.embed(clean_query, normalize=True)
        query_embeddings = [query_vec.tolist()]

        # Build where filter if specified
        where_conditions: List[Dict[str, Any]] = []
        if section_filter:
            where_conditions.append({"section": section_filter})
        if regime_filter:
            where_conditions.append({"regime_applicability": {"$in": [regime_filter, "both"]}})

        where_filter: Optional[Dict[str, Any]] = None
        if len(where_conditions) == 1:
            where_filter = where_conditions[0]
        elif len(where_conditions) > 1:
            where_filter = {"$and": where_conditions}

        # Query ChromaDB collection
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        formatted_results: List[Dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0] if results.get("distances") else [None] * len(ids)

        for chunk_id, doc, meta, dist in zip(ids, docs, metas, dists):
            distance_val = float(dist) if dist is not None else 0.0
            # Cosine distance is in [0, 2]; similarity = max(0, 1 - distance)
            sim_score = round(max(0.0, 1.0 - distance_val), 4)

            formatted_results.append({
                "id": chunk_id,
                "section": meta.get("section", ""),
                "title": meta.get("title", ""),
                "content": doc,
                "financial_year": meta.get("financial_year", "2025-2026"),
                "source_url": meta.get("source_url", ""),
                "regime_applicability": meta.get("regime_applicability", "both"),
                "tags": meta.get("tags", ""),
                "distance": round(distance_val, 4),
                "similarity_score": sim_score,
            })

        return formatted_results


# Global singleton instance
_GLOBAL_RAG_SERVICE: Optional[TaxRAGService] = None


def get_rag_service(
    chroma_dir: Optional[Union[str, Path]] = None,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> TaxRAGService:
    """Returns a shared TaxRAGService singleton."""
    global _GLOBAL_RAG_SERVICE
    if _GLOBAL_RAG_SERVICE is None:
        _GLOBAL_RAG_SERVICE = TaxRAGService(
            chroma_dir=chroma_dir,
            collection_name=collection_name,
        )
    return _GLOBAL_RAG_SERVICE


def retrieve_tax_rules(
    query: str,
    top_k: int = 3,
    section_filter: Optional[str] = None,
    regime_filter: Optional[str] = None,
    chroma_dir: Optional[Union[str, Path]] = None,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> List[Dict[str, Any]]:
    """
    Public entry point for retrieving relevant tax rule chunks (Task 6.3).
    """
    service = get_rag_service(chroma_dir=chroma_dir, collection_name=collection_name)
    return service.retrieve(
        query=query,
        top_k=top_k,
        section_filter=section_filter,
        regime_filter=regime_filter,
    )


def index_tax_rules_corpus(
    corpus_path: Optional[Union[str, Path]] = None,
    chroma_dir: Optional[Union[str, Path]] = None,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    force_reindex: bool = False,
) -> int:
    """
    Public entry point for indexing the tax rules corpus into ChromaDB (Task 6.2).
    """
    service = get_rag_service(chroma_dir=chroma_dir, collection_name=collection_name)
    return service.index_corpus(corpus_path=corpus_path, force_reindex=force_reindex)


if __name__ == "__main__":
    count = index_tax_rules_corpus(force_reindex=True)
    print(f"Indexed {count} tax rule chunks.")
    sample_query = "does home loan interest count?"
    results = retrieve_tax_rules(sample_query, top_k=2)
    print(f"\nSample query: '{sample_query}'")
    for r in results:
        print(f"[{r['section']}] {r['title']} (Score: {r['similarity_score']}) -> {r['source_url']}")
