"""seed.py

Seeding data and helper tools for populating ChromaDB with mock guidelines/literature.
"""

from typing import Any

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
    "obesity": [
        "WHO Obesity Report (2021): Obesity is established as a major risk factor for thirteen types of cancer.",
        "IARC Obesity Study (2019): High body fatness is associated with increased risk of postmenopausal breast and colorectal cancers."
    ],
    "bmi": [
        "PubMed PMC98214 (2022): Higher body mass index is significantly correlated with elevated risk of esophageal and pancreatic cancers.",
        "NCI Obesity Fact Sheet (2023): Body mass index exceeding 30.0 elevates risks of metabolic-related malignancies."
    ],
    "physical_activity": [
        "PubMed PMC77112 (2020): High levels of cardiorespiratory fitness and regular physical activity reduce overall cancer recurrence.",
        "WHO Activity Guidelines (2020): Regular moderate-to-vigorous exercise is strongly associated with lowered colon cancer risk."
    ],
    "inactivity": [
        "IARC Inactivity Monograph (2021): Sedentary behavior and physical inactivity increase susceptibility to endometrial and colorectal cancers.",
        "NCI Activity Report (2022): Physical inactivity is estimated to account for a significant portion of preventable breast cancers."
    ],
    "diet": [
        "WHO Diet and Cancer (2020): Low intake of fiber, fruits, and vegetables is associated with gastrointestinal cancers.",
        "NCI Dietary Guidelines (2021): Mediterranean-style dietary patterns are associated with a reduced overall cancer incidence."
    ],
    "processed_food": [
        "IARC Monograph 114 (2018): Consumption of processed meat is classified as carcinogenic to humans.",
        "PubMed PMC88102 (2021): Diets rich in ultra-processed foods are associated with increased risks of overall cancer."
    ],
    "previous_cancer": [
        "NCI Survivorship Guidelines (2022): A personal history of cancer increases the risk of developing a second primary malignancy.",
        "JCO Oncology Practice (2019): Monitoring primary cancer survivors is critical due to elevated therapy-related secondary cancer risks."
    ],
    "survivorship": [
        "PubMed PMC91230 (2020): Secondary primary malignancies are common among long-term cancer survivors.",
        "WHO Cancer Survivorship (2021): Follow-up care for former cancer patients must address elevated risks of new primary cancers."
    ],
}


def seed_database(store: Any, ingestor: Any) -> None:
    """Helper to seed ChromaDB with MOCK_DOCUMENTS and fallbacks if empty."""
    if store.collection.count() == 0:
        for category, docs in MOCK_DOCUMENTS.items():
            for idx, doc in enumerate(docs):
                ingestor.ingest_document(
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
            ingestor.ingest_document(
                text=doc,
                metadata={"category": "fallback"},
                doc_id_prefix=f"fallback_{idx}",
                chunk_size=1000,
                chunk_overlap=0,
            )
