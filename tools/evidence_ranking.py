"""evidence_ranking.py

Tools for parsing evidence text, identifying risk factors, and extracting scientific citations.
"""

import re
from typing import List
from schemas.contracts import PatientProfile, RiskFactor, Citation


def score_source_quality(source: str) -> float:
    """Scores the quality of a scientific source deterministically.

    Args:
        source: The source name or identifier.

    Returns:
        A float quality score between 0.0 and 1.0.
    """
    source_lower = source.lower()
    if "nejm" in source_lower or "nature" in source_lower or "iarc" in source_lower:
        return 0.95
    elif "pubmed" in source_lower or "lancet" in source_lower:
        return 0.90
    elif "who" in source_lower or "world health organization" in source_lower:
        return 0.85
    elif "cdc" in source_lower or "centers for disease control" in source_lower:
        return 0.80
    elif "nci" in source_lower or "national cancer institute" in source_lower:
        return 0.80
    elif "acs" in source_lower or "american cancer society" in source_lower:
        return 0.75
    else:
        return 0.50


def rank_evidence(factors: List[RiskFactor]) -> List[RiskFactor]:
    """Ranks risk factors by their evidence score in descending order.

    Args:
        factors: A list of RiskFactor instances.

    Returns:
        The sorted list of RiskFactor instances.
    """
    return sorted(factors, key=lambda f: f.evidence_score, reverse=True)


def extract_risk_factors(profile: PatientProfile, documents: List[str] = None) -> List[RiskFactor]:
    """Analyzes the patient profile inputs and extracts matching evidence-backed risk factors.

    If a list of documents is provided, the extraction is grounded: only factors verified
    by the documents are returned.

    Args:
        profile: The PatientProfile containing demographic and lifestyle info.
        documents: Optional list of retrieved document texts to ground the extraction.

    Returns:
        A list of RiskFactor schema objects matching the profile and grounded by documents (if provided).
    """
    factors = []

    # Determine risk indicators from profile details
    is_smoking = profile.smoking_status.lower() in ["active", "former"] or profile.smoking_years > 0
    is_ageing = profile.age > 50
    is_family_history = profile.family_history or len(profile.known_mutations) > 0
    is_sun = profile.sun_exposure.lower() == "high"
    is_alcohol = profile.alcohol_use.lower() in ["moderate", "heavy"]

    # If documents are provided, ground extraction by searching for keywords inside the documents
    if documents is not None:
        doc_text = " ".join(documents).lower()
        has_smoke_doc = "smoke" in doc_text or "tobacco" in doc_text
        has_age_doc = bool(re.search(r'\bage\b|senescence', doc_text))
        has_genetic_doc = "genetic" in doc_text or "brca" in doc_text or "mutations" in doc_text
        has_sun_doc = "sun" in doc_text or "uv" in doc_text
        has_alcohol_doc = "alcohol" in doc_text

        if is_smoking and has_smoke_doc:
            factors.append(
                RiskFactor(
                    factor="Tobacco Smoke Exposure",
                    evidence_strength="high",
                    evidence_score=0.95,
                    source_count=12,
                )
            )
        if is_ageing and has_age_doc:
            factors.append(
                RiskFactor(
                    factor="Age-related Cellular Senescence",
                    evidence_strength="high",
                    evidence_score=0.88,
                    source_count=8,
                )
            )
        if is_family_history and has_genetic_doc:
            factors.append(
                RiskFactor(
                    factor="Genetic/Familial Predisposition",
                    evidence_strength="medium",
                    evidence_score=0.72,
                    source_count=5,
                )
            )
        if is_sun and has_sun_doc:
            factors.append(
                RiskFactor(
                    factor="UV/Sun Exposure",
                    evidence_strength="medium",
                    evidence_score=0.70,
                    source_count=4,
                )
            )
        if is_alcohol and has_alcohol_doc:
            factors.append(
                RiskFactor(
                    factor="Alcohol Consumption Risk",
                    evidence_strength="medium",
                    evidence_score=0.65,
                    source_count=3,
                )
            )
    else:
        # Retain original profile-only fallback checks if no documents are passed
        if is_smoking:
            factors.append(
                RiskFactor(
                    factor="Tobacco Smoke Exposure",
                    evidence_strength="high",
                    evidence_score=0.95,
                    source_count=12,
                )
            )
        if is_ageing:
            factors.append(
                RiskFactor(
                    factor="Age-related Cellular Senescence",
                    evidence_strength="high",
                    evidence_score=0.88,
                    source_count=8,
                )
            )
        if is_family_history:
            factors.append(
                RiskFactor(
                    factor="Genetic/Familial Predisposition",
                    evidence_strength="medium",
                    evidence_score=0.72,
                    source_count=5,
                )
            )
        if is_sun:
            factors.append(
                RiskFactor(
                    factor="UV/Sun Exposure",
                    evidence_strength="medium",
                    evidence_score=0.70,
                    source_count=4,
                )
            )
        if is_alcohol:
            factors.append(
                RiskFactor(
                    factor="Alcohol Consumption Risk",
                    evidence_strength="medium",
                    evidence_score=0.65,
                    source_count=3,
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



def extract_citations(factors: List[str], documents: List[str] = None) -> List[Citation]:
    """Extracts scientific citations supporting the given list of risk factors.

    Can compile citations dynamically from retrieved document metadata if provided.

    Args:
        factors: A list of string names of identified risk factors.
        documents: Optional list of retrieved document strings.

    Returns:
        A list of Citation schema objects.
    """
    citations = []

    # If documents are provided, compile citations dynamically by parsing metadata
    if documents:
        for doc in documents:
            # Pattern matching: Source (Year): Content
            match = re.match(r"^([^(:]+)\s*\((\d{4})\)\s*:\s*(.+)$", doc)
            if match:
                source = match.group(1).strip()
                year = int(match.group(2))
                title = match.group(3).strip()
                if len(title) > 60:
                    title = title[:57] + "..."
                citations.append(Citation(source=source, title=title, year=year))
            else:
                # Fallback parser
                year_match = re.search(r"\((\d{4})\)", doc)
                year = int(year_match.group(1)) if year_match else 2020
                parts = doc.split(":", 1)
                if len(parts) > 1:
                    source = parts[0].strip()
                    title = parts[1].strip()
                else:
                    source = "Research Publication"
                    title = doc.strip()
                if len(title) > 60:
                    title = title[:57] + "..."
                citations.append(Citation(source=source, title=title, year=year))

        # Deduplicate compiled citations
        seen = set()
        dedup = []
        for c in citations:
            key = (c.source, c.title)
            if key not in seen:
                seen.add(key)
                dedup.append(c)
        if dedup:
            return dedup

    # Fallback to key-matching list on factors if no documents are passed or parsing returned empty
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
