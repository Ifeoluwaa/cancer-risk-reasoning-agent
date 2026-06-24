"""retrieval.py

Retrieval abstraction for querying the ChromaDB vector store.
"""

from typing import List, Optional
from tools.rag.vector_store import ChromaVectorStore


class RAGRetriever:
    """Retriever class responsible for querying the vector store.
    """

    def __init__(self, vector_store: Optional[ChromaVectorStore] = None) -> None:
        """Initialize RAGRetriever with a vector store instance.

        Args:
            vector_store: ChromaVectorStore instance. Creates an ephemeral instance if None.
        """
        self.vector_store = vector_store or ChromaVectorStore()

    def retrieve_documents(self, query: str, limit: int = 3) -> List[str]:
        """Queries the vector store and returns matching document chunks.

        Args:
            query: The user query or clinical query context.
            limit: The maximum number of results to fetch.

        Returns:
            A list of retrieved document chunk strings.
        """
        results = self.vector_store.query(query, limit=limit)
        return [res["document"] for res in results]
