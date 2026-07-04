"""retrieval.py

Document retrieval tools for fetching scientific context from ChromaDB.
"""

from typing import List
from tools.rag.vector_store import ChromaVectorStore
from tools.rag.retrieval import RAGRetriever
from tools.rag.ingest import RAGIngestor


# Import mock/demo documents and seeding utilities
from tools.rag.seed import MOCK_DOCUMENTS, seed_database

import threading
import sqlite3

# Use thread-safe global storage for DB client and retriever to prevent connection collisions and schema teardowns
_global_lock = threading.Lock()
_global_store = None
_global_retriever = None
_global_ingestor = None
_global_is_populated = False
_keep_alive_conn = None


def _get_thread_store():
    """Lazily retrieves or initializes the global ChromaDB store and agents in a thread-safe manner."""
    global _global_store, _global_retriever, _global_ingestor, _keep_alive_conn
    with _global_lock:
        if _global_store is None:
            # Keep a connection alive to prevent the SQLite in-memory database from being destroyed
            # when worker threads finish and close their thread-local connections.
            _keep_alive_conn = sqlite3.connect("file::memory:?cache=shared", uri=True)
            _global_store = ChromaVectorStore(
                persist_directory=None,
                collection_name="cancer_risk_evidence_production"
            )
            _global_retriever = RAGRetriever(vector_store=_global_store)
            _global_ingestor = RAGIngestor(vector_store=_global_store)
    return _global_store, _global_retriever, _global_ingestor


def _ensure_populated() -> None:
    """Helper to seed ChromaDB with MOCK_DOCUMENTS if empty."""
    global _global_is_populated
    store, retriever, ingestor = _get_thread_store()
    with _global_lock:
        if not _global_is_populated:
            seed_database(store, ingestor)
            _global_is_populated = True


def retrieve_documents(query: str, limit: int = 3) -> List[str]:
    """Retrieves related research document chunks for a search query from ChromaDB.

    Args:
        query: The search query string.
        limit: Maximum number of document chunks to retrieve.

    Returns:
        A list of retrieved document chunks.
    """
    store, retriever, ingestor = _get_thread_store()
    _ensure_populated()
    
    query_lower = query.lower()
    matched_keys = [k for k in MOCK_DOCUMENTS.keys() if k in query_lower]
    
    if matched_keys:
        retrieved = []
        # Query ChromaDB specifically for matched categories to preserve semantic mapping
        for key in matched_keys:
            res = store.collection.query(
                query_texts=[key],
                where={"category": key},
                n_results=limit,
            )
            if res and res["documents"] and res["documents"][0]:
                for doc in res["documents"][0]:
                    if doc not in retrieved:
                        retrieved.append(doc)
        if retrieved:
            return retrieved[:limit]

    # If no keywords matched, return the fallback default results from ChromaDB
    res = store.collection.query(
        query_texts=["fallback"],
        where={"category": "fallback"},
        n_results=limit,
    )
    if res and res["documents"] and res["documents"][0]:
        return res["documents"][0][:limit]
        
    return []


