"""evidence_ranking.py

Tools for parsing evidence text, identifying risk factors, and extracting scientific citations.
"""

import re
from typing import List
from schemas.contracts import PatientProfile, RiskFactor, Citation


def classify_evidence_quality(text: str) -> str:
    """Classifies the quality level of a retrieved document or reference text.

    Args:
        text: The scientific document text or reference title/content.

    Returns:
        A string classification from the evidence quality hierarchy.
    """
    text_lower = text.lower()
    
    # Clinical Guidelines
    if any(x in text_lower for x in ["guideline", "who guidelines", "iarc monograph", "nccn", "uspstf", "cdc"]):
        return "Clinical Guideline"
        
    # Systematic Reviews / Meta-analyses
    if any(x in text_lower for x in ["meta-analysis", "systematic review", "systematic reviews"]):
        return "Systematic Review / Meta-analysis"
            
    # RCTs
    if any(x in text_lower for x in ["randomized controlled trial", "randomized trial", "rct"]):
        return "Randomized Controlled Trial"
        
    # Prospective Cohort Studies
    if any(x in text_lower for x in ["prospective cohort", "cohort study", "cohort studies"]):
        return "Prospective Cohort"
        
    # Case-Control Study
    if "case-control" in text_lower:
        return "Case-Control Study"
        
    # Cross-sectional Study
    if "cross-sectional" in text_lower:
        return "Cross-sectional Study"
        
    # Expert Consensus
    if any(x in text_lower for x in ["consensus", "expert opinion", "expert consensus"]):
        return "Expert Consensus"
        
    # Mechanistic / Laboratory Study
    if any(x in text_lower for x in ["mechanistic", "laboratory", "in vitro", "cell culture", "cellular senescence", "senescence and aging"]):
        return "Mechanistic / Laboratory Study"
        
    # Case Report
    if "case report" in text_lower or "case series" in text_lower:
        return "Case Report"
        
    # Background Reference
    return "Background Reference"


def get_quality_multiplier(quality: str) -> float:
    """Returns the multiplier associated with each evidence quality level.

    Args:
        quality: The evidence quality level.

    Returns:
        A float multiplier (higher-quality evidence has > 1.0, lower-quality has < 1.0).
    """
    multipliers = {
        "Clinical Guideline": 1.20,
        "Systematic Review / Meta-analysis": 1.15,
        "Randomized Controlled Trial": 1.10,
        "Prospective Cohort": 1.05,
        "Case-Control Study": 1.02,
        "Cross-sectional Study": 1.00,
        "Expert Consensus": 0.95,
        "Mechanistic / Laboratory Study": 0.90,
        "Case Report": 0.80,
        "Background Reference": 0.85,
    }
    return multipliers.get(quality, 1.0)


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
    is_obese = profile.bmi >= 30.0
    is_inactive = profile.physical_activity.lower() == "low"
    is_poor_diet = profile.diet_quality.lower() == "low"
    is_prev_cancer = profile.previous_cancer_history
 
    # If documents are provided, ground extraction by searching for keywords inside the documents
    if documents is not None:
        doc_text = " ".join(documents).lower()
        has_smoke_doc = "smoke" in doc_text or "tobacco" in doc_text
        has_age_doc = bool(re.search(r'\bage\b|senescence', doc_text))
        has_genetic_doc = "genetic" in doc_text or "brca" in doc_text or "mutations" in doc_text
        has_sun_doc = "sun" in doc_text or "uv" in doc_text
        has_alcohol_doc = "alcohol" in doc_text
        has_obese_doc = "obesity" in doc_text or "bmi" in doc_text
        has_inactive_doc = "inactivity" in doc_text or "physical_activity" in doc_text or "exercise" in doc_text or "activity" in doc_text
        has_poor_diet_doc = "diet" in doc_text or "processed" in doc_text
        has_prev_cancer_doc = "previous_cancer" in doc_text or "survivorship" in doc_text or "malignancy" in doc_text or "survivor" in doc_text

        # Define keywords for each factor name to associate documents with factors
        factor_keywords = {
            "Tobacco Smoke Exposure": ["smoke", "tobacco"],
            "Age-related Cellular Senescence": ["age", "senescence"],
            "Genetic/Familial Predisposition": ["genetic", "brca", "mutation"],
            "UV/Sun Exposure": ["sun", "uv"],
            "Alcohol Consumption Risk": ["alcohol"],
            "Obesity-related Cancer Risk": ["obesity", "bmi"],
            "Physical Inactivity": ["inactivity", "physical_activity", "exercise", "activity"],
            "Poor Dietary Pattern": ["diet", "processed"],
            "Previous Malignancy History": ["previous_cancer", "survivorship", "malignancy", "survivor"]
        }

        active_factors = []
        if is_smoking and has_smoke_doc:
            active_factors.append(("Tobacco Smoke Exposure", "high", 0.95, 12))
        if is_ageing and has_age_doc:
            active_factors.append(("Age-related Cellular Senescence", "high", 0.88, 8))
        if is_family_history and has_genetic_doc:
            active_factors.append(("Genetic/Familial Predisposition", "medium", 0.72, 5))
        if is_sun and has_sun_doc:
            active_factors.append(("UV/Sun Exposure", "medium", 0.70, 4))
        if is_alcohol and has_alcohol_doc:
            active_factors.append(("Alcohol Consumption Risk", "medium", 0.65, 3))
        if is_obese and has_obese_doc:
            active_factors.append(("Obesity-related Cancer Risk", "high", 0.80, 6))
        if is_inactive and has_inactive_doc:
            active_factors.append(("Physical Inactivity", "medium", 0.60, 3))
        if is_poor_diet and has_poor_diet_doc:
            active_factors.append(("Poor Dietary Pattern", "medium", 0.55, 3))
        if is_prev_cancer and has_prev_cancer_doc:
            active_factors.append(("Previous Malignancy History", "high", 0.85, 5))
        for factor_name, strength, base_score, source_count in active_factors:
            keywords = factor_keywords.get(factor_name, [])
            matching_docs = [doc for doc in documents if any(kw in doc.lower() for kw in keywords)]
            if not matching_docs:
                matching_docs = documents

            qualities = [classify_evidence_quality(doc) for doc in matching_docs]
            multipliers = [get_quality_multiplier(q) for q in qualities]
            max_mult = max(multipliers) if multipliers else 1.0

            adjusted_score = min(1.0, base_score * max_mult)

            factors.append(
                RiskFactor(
                    factor=factor_name,
                    evidence_strength=strength,
                    evidence_score=adjusted_score,
                    source_count=source_count
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
        if is_obese:
            factors.append(
                RiskFactor(
                    factor="Obesity-related Cancer Risk",
                    evidence_strength="high",
                    evidence_score=0.80,
                    source_count=6,
                )
            )
        if is_inactive:
            factors.append(
                RiskFactor(
                    factor="Physical Inactivity",
                    evidence_strength="medium",
                    evidence_score=0.60,
                    source_count=3,
                )
            )
        if is_poor_diet:
            factors.append(
                RiskFactor(
                    factor="Poor Dietary Pattern",
                    evidence_strength="medium",
                    evidence_score=0.55,
                    source_count=3,
                )
            )
        if is_prev_cancer:
            factors.append(
                RiskFactor(
                    factor="Previous Malignancy History",
                    evidence_strength="high",
                    evidence_score=0.85,
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
                quality = classify_evidence_quality(doc)
                citations.append(Citation(source=source, title=title, year=year, evidence_quality=quality))
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
                quality = classify_evidence_quality(doc)
                citations.append(Citation(source=source, title=title, year=year, evidence_quality=quality))

        # Deduplicate compiled citations
        seen = set()
        dedup = []
        for c in citations:
            key = (c.source, c.title)
            if key not in seen:
                seen.add(key)
                dedup.append(c)
        if dedup:
            citations = dedup

    if not citations:
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
            elif "obesity" in factor_lower or "bmi" in factor_lower:
                citations.append(
                    Citation(
                        source="WHO Obesity and Cancer Study",
                        title="Obesity as a major risk factor for cancer development",
                        year=2021,
                    )
                )
            elif "inactivity" in factor_lower or "activity" in factor_lower:
                citations.append(
                    Citation(
                        source="IARC Inactivity Monograph",
                        title="Physical inactivity and sedentary behavior in cancer risk",
                        year=2021,
                    )
                )
            elif "diet" in factor_lower or "processed" in factor_lower:
                citations.append(
                    Citation(
                        source="WHO Diet and Cancer Report",
                        title="Nutritional factors and overall cancer incidence",
                        year=2020,
                    )
                )
            elif "previous" in factor_lower or "malignancy" in factor_lower or "survivor" in factor_lower:
                citations.append(
                    Citation(
                        source="NCI Survivorship Guidelines",
                        title="Personal cancer history and second primary cancer risks",
                        year=2022,
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

    # Post-process to ensure all citations have evidence_quality populated
    for c in citations:
        if c.evidence_quality is None:
            c.evidence_quality = classify_evidence_quality(c.title + " " + c.source)

    return citations
