"""vector_store.py

ChromaDB database manager wrapper for indexing and query execution.
"""

import os
from typing import Any, Dict, List, Optional
import chromadb
from tools.rag.embeddings import SimpleLocalEmbeddingFunction


class ChromaVectorStore:
    """Wrapper class managing a local ChromaDB instance and collections.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "cancer_risk_evidence",
    ) -> None:
        """Initialize ChromaDB client and collection.

        Args:
            persist_directory: Directory for persistent database storage. If None, uses in-memory.
            collection_name: Name of the active vector collection.
        """
        self.embedding_function = SimpleLocalEmbeddingFunction()
        
        if persist_directory:
            os.makedirs(persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.EphemeralClient()

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
        )

    def add_chunks(
        self,
        chunks: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """Adds chunks to the active collection.

        Args:
            chunks: List of text content chunks.
            metadatas: List of dictionaries matching the chunks.
            ids: List of unique IDs for each chunk.
        """
        if not chunks:
            return

        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids,
        )

    def query(self, query_text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Queries the vector store for the closest matching chunks.

        Args:
            query_text: Query search query string.
            limit: Maximum number of matches to return.

        Returns:
            A list of dictionary results containing 'document', 'metadata', 'id', and 'distance'.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=limit,
        )

        formatted = []
        if not results or not results["documents"]:
            return formatted

        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results["metadatas"] else [None] * len(documents)
        ids = results["ids"][0] if results["ids"] else [None] * len(documents)
        distances = results["distances"][0] if results["distances"] else [0.0] * len(documents)

        for i in range(len(documents)):
            formatted.append({
                "document": documents[i],
                "metadata": metadatas[i],
                "id": ids[i],
                "distance": distances[i],
            })

        return formatted
