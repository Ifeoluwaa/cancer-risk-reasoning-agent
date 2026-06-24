"""test_rag.py

Unit tests for Stage 14 RAG ingestion and retrieval infrastructure.
"""

import unittest
from tools.retrieval import retrieve_documents as mock_retrieve_documents
from tools.rag.chunking import chunk_text
from tools.rag.embeddings import SimpleLocalEmbeddingFunction
from tools.rag.vector_store import ChromaVectorStore
from tools.rag.retrieval import RAGRetriever
from tools.rag.ingest import RAGIngestor


class TestRAGInfrastructure(unittest.TestCase):
    """Unit test suite for validating RAG text processing and vector storage."""

    def test_chunk_generation(self) -> None:
        """Validate text chunking split logic, constraints, and overlaps."""
        text = "abcdefghijklmnopqrstuvwxyz"
        # 1. Standard split
        chunks = chunk_text(text, chunk_size=10, chunk_overlap=2)
        # Expected:
        # chunk 0: abcdefghij (length 10)
        # chunk 1: ijklmnopqr (length 10, overlap 'ij')
        # chunk 2: qrstuvwxyz (length 10, overlap 'qr')
        self.assertEqual(chunks[0], "abcdefghij")
        self.assertEqual(chunks[1], "ijklmnopqr")
        self.assertEqual(chunks[2], "qrstuvwxyz")

        # 2. Border cases
        self.assertEqual(chunk_text("", chunk_size=5, chunk_overlap=1), [])
        
        # 3. Invalid inputs
        with self.assertRaises(ValueError):
            chunk_text(text, chunk_size=0)
        with self.assertRaises(ValueError):
            chunk_text(text, chunk_size=5, chunk_overlap=5)

    def test_local_embeddings(self) -> None:
        """Validate deterministic behavior of local embedding generation."""
        emb_fn = SimpleLocalEmbeddingFunction(dimension=16)
        texts = ["lung cancer study", "BRCA1 genetic mutation"]
        
        embeddings = emb_fn(texts)
        
        self.assertEqual(len(embeddings), 2)
        self.assertEqual(len(embeddings[0]), 16)
        self.assertEqual(len(embeddings[1]), 16)
        
        # Test determinism
        self.assertEqual(list(emb_fn([texts[0]])[0]), list(embeddings[0]))

    def test_chromadb_collection_and_insertion(self) -> None:
        """Validate ChromaDB ephemeral collection creation and vector insertion."""
        store = ChromaVectorStore(persist_directory=None, collection_name="test_collection")
        
        # Test collection initialization
        self.assertIsNotNone(store.collection)
        
        # Insert test chunks
        chunks = ["Document chunk one about tobacco.", "Document chunk two about alcohol."]
        metadatas = [{"source": "WHO"}, {"source": "IARC"}]
        ids = ["doc_1", "doc_2"]
        
        store.add_chunks(chunks, metadatas, ids)
        
        # Query store
        results = store.query("tobacco", limit=1)
        self.assertEqual(len(results), 1)
        self.assertIn(results[0]["id"], ["doc_1", "doc_2"])
        self.assertIn(results[0]["metadata"]["source"], ["WHO", "IARC"])

    def test_document_ingestion_and_retrieval(self) -> None:
        """Validate end-to-end ingestion pipeline and retriever querying."""
        store = ChromaVectorStore(persist_directory=None, collection_name="test_ingest_collection")
        ingestor = RAGIngestor(vector_store=store)
        retriever = RAGRetriever(vector_store=store)
        
        doc_text = "Genetic risk factors play a significant role. BRCA1 and BRCA2 mutations are primary indicators."
        metadata = {"category": "genetics"}
        
        # Ingest
        chunk_ids = ingestor.ingest_document(
            text=doc_text,
            metadata=metadata,
            doc_id_prefix="gene_study",
            chunk_size=40,
            chunk_overlap=10
        )
        
        self.assertTrue(len(chunk_ids) > 0)
        self.assertTrue(all(cid.startswith("gene_study_chunk_") for cid in chunk_ids))
        
        # Retrieve
        results = retriever.retrieve_documents("BRCA1 mutation", limit=2)
        self.assertTrue(len(results) > 0)
        self.assertTrue(any("BRCA1" in res for res in results))

    def test_backward_compatibility(self) -> None:
        """Validate that Stage 8 mock retrieval functionality remains unchanged."""
        docs = mock_retrieve_documents("tobacco smoking age", limit=5)
        # Verify it still returns correct mock documents
        self.assertTrue(len(docs) >= 2)
        self.assertTrue(any("WHO Guidelines" in d for d in docs))
        self.assertTrue(any("senescence" in d.lower() or "dna damage" in d.lower() for d in docs))


if __name__ == "__main__":
    unittest.main()
