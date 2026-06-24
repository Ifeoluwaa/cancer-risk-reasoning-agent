"""retrieval.py

Document retrieval tools for fetching scientific context from ChromaDB.
"""

from typing import List


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


def retrieve_documents(query: str, limit: int = 3) -> List[str]:
    """Retrieves related research document chunks for a search query from mock storage.

    Args:
        query: The search query string.
        limit: Maximum number of document chunks to retrieve.

    Returns:
        A list of retrieved document chunks (mocked strings).
    """
    query_lower = query.lower()
    retrieved = []

    for key, docs in MOCK_DOCUMENTS.items():
        if key in query_lower:
            for doc in docs:
                if doc not in retrieved:
                    retrieved.append(doc)

    # Fallback if no keywords matched
    if not retrieved:
        retrieved = [
            "WHO Cancer Report (2020): General overview of environmental and lifestyle cancer risk factors.",
            "PubMed General (2021): Evaluation of baseline cancer risk factors in adult populations."
        ]

    return retrieved[:limit]

