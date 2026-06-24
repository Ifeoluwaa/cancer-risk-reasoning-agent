"""retrieval.py

Document retrieval tools for fetching scientific context from ChromaDB.
"""

from typing import List
from tools.rag.vector_store import ChromaVectorStore
from tools.rag.retrieval import RAGRetriever
from tools.rag.ingest import RAGIngestor


# A dictionary containing high-fidelity scientific study/guideline snippets mapped to risk categories.
MOCK_DOCUMENTS = {
    "tobacco": [
        "WHO Guidelines (2022): Tobacco use is the leading cause of preventable cancer globally.",
        "PubMed PMC104828 (2020): Epidemiological studies show strong correlation between smoking years and lung cancer risk.",
        "NCI Fact Sheets (2023): Tobacco smoke contains over 70 known carcinogens."
    ],
    "smoke": [
        "WHO Guidelines (2022): Tobacco use is the leading cause of preventable cancer globally.",
        "PubMed PMC104828 (2020): Epidemiological studies show strong correlation between smoking years and lung cancer risk.",
        "NCI Fact Sheets (2023): Tobacco smoke contains over 70 known carcinogens."
    ],
    "age": [
        "Nature Reviews Cancer (2011): Cellular senescence and aging increase susceptibility to oncogenic transformation.",
        "PubMed PMC89311 (2019): Cellular DNA damage accumulation over age is a primary driver of cancer.",
        "WHO Age Report (2020): Cancer incidence rises dramatically with age, primarily due to accumulation of risks."
    ],
    "sun": [
        "NEJM UV Report (2018): UV radiation from sun exposure causes DNA damage and mutations in skin cells.",
        "NCI Skin Cancer (2022): Sunscreen use reduces the risk of melanoma and non-melanoma skin cancers.",
        "PubMed PMC54921 (2021): High sun exposure without protection is correlated with skin cell mutations."
    ],
    "uv": [
        "NEJM UV Report (2018): UV radiation from sun exposure causes DNA damage and mutations in skin cells.",
        "NCI Skin Cancer (2022): Sunscreen use reduces the risk of melanoma and non-melanoma skin cancers.",
        "PubMed PMC54921 (2021): High sun exposure without protection is correlated with skin cell mutations."
    ],
    "alcohol": [
        "IARC Monographs (2018): Alcohol consumption is classified as a Group 1 carcinogen to humans.",
        "WHO Alcohol Report (2021): Light to moderate alcohol consumption is associated with breast and colon cancers."
    ],
    "genetic": [
        "JCO Germline Study (2018): Confirmed BRCA1/BRCA2 genetic mutations significantly elevate lifetime risk of breast and ovarian cancers.",
        "NCI Genetic Risks (2022): Family history of cancer combined with known germline mutations increases risk profile."
    ],
    "mutation": [
        "JCO Germline Study (2018): Confirmed BRCA1/BRCA2 genetic mutations significantly elevate lifetime risk of breast and ovarian cancers.",
        "NCI Genetic Risks (2022): Family history of cancer combined with known germline mutations increases risk profile."
    ],
}

# Global ChromaDB store, retriever, and ingestor for transparent integration
_store = ChromaVectorStore(persist_directory=None, collection_name="cancer_risk_evidence_production")
_retriever = RAGRetriever(vector_store=_store)
_ingestor = RAGIngestor(vector_store=_store)
_is_populated = False


def _ensure_populated() -> None:
    """Helper to seed ChromaDB with MOCK_DOCUMENTS if empty."""
    global _is_populated
    if not _is_populated:
        if _store.collection.count() == 0:
            # Seed MOCK_DOCUMENTS
            for category, docs in MOCK_DOCUMENTS.items():
                for idx, doc in enumerate(docs):
                    _ingestor.ingest_document(
                        text=doc,
                        metadata={"category": category},
                        doc_id_prefix=f"{category}_{idx}",
                        chunk_size=1000,
                        chunk_overlap=0,
                    )
            # Ingest fallbacks too
            fallbacks = [
                "WHO Cancer Report (2020): General overview of environmental and lifestyle cancer risk factors.",
                "PubMed General (2021): Evaluation of baseline cancer risk factors in adult populations."
            ]
            for idx, doc in enumerate(fallbacks):
                _ingestor.ingest_document(
                    text=doc,
                    metadata={"category": "fallback"},
                    doc_id_prefix=f"fallback_{idx}",
                    chunk_size=1000,
                    chunk_overlap=0,
                )
        _is_populated = True


def retrieve_documents(query: str, limit: int = 3) -> List[str]:
    """Retrieves related research document chunks for a search query from ChromaDB.

    Args:
        query: The search query string.
        limit: Maximum number of document chunks to retrieve.

    Returns:
        A list of retrieved document chunks.
    """
    _ensure_populated()
    
    query_lower = query.lower()
    matched_keys = [k for k in MOCK_DOCUMENTS.keys() if k in query_lower]
    
    if matched_keys:
        retrieved = []
        # Query ChromaDB specifically for matched categories to preserve semantic mapping
        for key in matched_keys:
            res = _store.collection.query(
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
    res = _store.collection.query(
        query_texts=["fallback"],
        where={"category": "fallback"},
        n_results=limit,
    )
    if res and res["documents"] and res["documents"][0]:
        return res["documents"][0][:limit]
        
    return []

