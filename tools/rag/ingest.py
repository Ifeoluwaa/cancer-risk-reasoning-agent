"""ingest.py

Ingestion pipeline logic for chunking and storing document resources into ChromaDB.
"""

from typing import Any, Dict, List, Optional
from tools.rag.chunking import chunk_text
from tools.rag.vector_store import ChromaVectorStore


class RAGIngestor:
    """Document Ingestion manager that chunks and uploads files/texts to the vector store.
    """

    def __init__(self, vector_store: Optional[ChromaVectorStore] = None) -> None:
        """Initialize the Ingestor.

        Args:
            vector_store: ChromaVectorStore instance. Creates an ephemeral instance if None.
        """
        self.vector_store = vector_store or ChromaVectorStore()

    def ingest_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        doc_id_prefix: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> List[str]:
        """Chunks a document and adds it to the ChromaDB vector store.

        Args:
            text: Raw document text content.
            metadata: Base metadata dictionary to attach to each chunk.
            doc_id_prefix: Prefix used to generate unique chunk IDs.
            chunk_size: Target size of each chunk.
            chunk_overlap: Target overlap size of chunks.

        Returns:
            A list of generated chunk IDs added to the database.
        """
        if not text.strip():
            return []

        chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunk_ids = [f"{doc_id_prefix}_chunk_{i}" for i in range(len(chunks))]
        
        # Prepare metadata for each chunk
        metadatas = []
        for i, chunk in enumerate(chunks):
            meta_copy = metadata.copy()
            meta_copy["chunk_index"] = i
            metadatas.append(meta_copy)

        self.vector_store.add_chunks(
            chunks=chunks,
            metadatas=metadatas,
            ids=chunk_ids,
        )

        return chunk_ids
