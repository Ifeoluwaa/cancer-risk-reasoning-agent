"""evidence_ranking.py

Tools for parsing evidence text, identifying risk factors, and extracting scientific citations.
"""

from typing import List
from schemas.contracts import PatientProfile, RiskFactor, Citation


def extract_risk_factors(profile: PatientProfile) -> List[RiskFactor]:
    """Analyzes the patient profile inputs and extracts matching evidence-backed risk factors.

    In future stages, this tool will:
    1. Cross-reference the patient profile with retrieved document contexts.
    2. Extract risk factor magnitudes and assign numerical evidence scores.
    3. Grade evidence strength based on study design classifications (high, medium, low).

    Args:
        profile: The PatientProfile containing demographic and lifestyle info.

    Returns:
        A list of RiskFactor schema objects matching the profile.
    """
    # Return conforming mock risk factors
    factors = []
    if profile.smoking_status.lower() in ["active", "former"] or profile.smoking_years > 0:
        factors.append(
            RiskFactor(
                factor="Tobacco Smoke Exposure",
                evidence_strength="high",
                evidence_score=0.95,
                source_count=12,
            )
        )
    if profile.age > 50:
        factors.append(
            RiskFactor(
                factor="Age-related Cellular Senescence",
                evidence_strength="high",
                evidence_score=0.88,
                source_count=8,
            )
        )
    if profile.family_history:
        factors.append(
            RiskFactor(
                factor="Genetic/Familial Predisposition",
                evidence_strength="medium",
                evidence_score=0.72,
                source_count=5,
            )
        )

    if not factors:
        factors.append(
            RiskFactor(
                factor="General Environmental Baseline",
                evidence_strength="low",
                evidence_score=0.25,
                source_count=2,
            )
        )

    return factors


def extract_citations(factors: List[str]) -> List[Citation]:
    """Extracts scientific citations supporting the given list of risk factors.

    In future stages, this tool will:
    1. Retrieve metadata from retrieved research papers corresponding to the factors.
    2. Format clean AMA or APA citation records.

    Args:
        factors: A list of string names of identified risk factors.

    Returns:
        A list of Citation schema objects.
    """
    citations = []
    for factor in factors:
        factor_lower = factor.lower()
        if "tobacco" in factor_lower or "smoke" in factor_lower:
            citations.append(
                Citation(
                    source="IARC Monographs Vol. 83",
                    title="Evaluation of Carcinogenic Risks of Tobacco Smoke to Humans",
                    year=2004,
                )
            )
        elif "age" in factor_lower:
            citations.append(
                Citation(
                    source="Nature Reviews Cancer",
                    title="Aging, senescence, and cancer: pathways and mechanisms",
                    year=2011,
                )
            )
        elif "genetic" in factor_lower or "familial" in factor_lower:
            citations.append(
                Citation(
                    source="Journal of Clinical Oncology",
                    title="Clinical utility of hereditary cancer germline sequencing",
                    year=2018,
                )
            )

    if not citations:
        citations.append(
            Citation(
                source="World Health Organization",
                title="World Cancer Report: Cancer Research for Cancer Prevention",
                year=2020,
            )
        )

    return citations
