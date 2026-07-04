"""skeptic.py

Skeptic reasoning tools for auditing evidence strength, uncertainties, and identifying conflicting science.
"""

from typing import List, Optional
from schemas.contracts import (
    PatientProfile,
    EvidencePackage,
    CausalityPackage,
    SkepticPackage,
    ConflictingEvidence,
    FollowUpQuestion,
)




def find_uncertainties(
    evidence: EvidencePackage,
    causality: CausalityPackage,
    profile: Optional[PatientProfile] = None,
) -> List[str]:
    """Identifies logical or structural uncertainties, potential confounders, and alternative explanations.

    Args:
        evidence: The EvidencePackage containing identified risk factors.
        causality: The CausalityPackage detailing ranked contributors.
        profile: Optional PatientProfile.

    Returns:
        A list of uncertainty strings including confounders and alternative explanations.
    """
    uncertainties = []

    # 1. Regression-required uncertainties
    has_genetic = any(
        "genetic" in rf.factor.lower() or "mutation" in rf.factor.lower()
        for rf in evidence.risk_factors
    )
    if not has_genetic:
        uncertainties.append("Causal link assumes default baseline without custom germline variant screening.")

    if causality.causal_confidence == "low":
        uncertainties.append("Causal confidence is low due to weak evidence scoring in primary drivers.")

    # 2. Potential Confounders (structured peer review)
    if profile:
        # Smoking and asbestos synergism
        is_smoking = profile.smoking_status.lower() == "active"
        has_asbestos = any("asbestos" in e.lower() for e in profile.environmental_exposure)
        if is_smoking and has_asbestos:
            uncertainties.append("Potential Confounder: Synergistic interaction between tobacco smoke and asbestos exposure is known to amplify risk non-linearly, making individual risk attribution difficult.")
        
        # Obesity and physical inactivity overlap
        is_obese = profile.bmi >= 30.0
        is_inactive = profile.physical_activity.lower() == "low"
        if is_obese and is_inactive:
            uncertainties.append("Potential Confounder: Obesity and low physical activity contribute via overlapping metabolic and inflammatory pathways, confounding individual pathway attribution.")

        # Smoking and alcohol mucosal damage
        is_alcohol = profile.alcohol_use.lower() in ["moderate", "heavy"]
        if is_smoking and is_alcohol:
            uncertainties.append("Potential Confounder: Co-occurrence of tobacco smoke and alcohol consumption is known to multiply mucosal carcinogenesis risks, confounding separate risk estimation.")

        # Age confounding
        if profile.age > 50:
            uncertainties.append(f"Potential Confounder: Advancing age ({profile.age} years) contributes to biological senescence, which may confound the attribution of risk between chronological aging and lifestyle exposures.")

    # 3. Alternative Explanations (preventing overconfident conclusions)
    factors_lower = [rf.factor.lower() for rf in evidence.risk_factors]
    has_smoke = any("tobacco" in f or "smoke" in f for f in factors_lower)
    has_asbestos_factor = any("environmental" in f or "asbestos" in f for f in factors_lower)
    has_obesity = any("obesity" in f or "bmi" in f for f in factors_lower)
    has_inactivity = any("inactivity" in f or "activity" in f for f in factors_lower)
    has_genetic_factor = any("genetic" in f or "predisposition" in f for f in factors_lower)

    if has_smoke and has_asbestos_factor:
        uncertainties.append("Alternative Explanation: Smoking appears to be the dominant contributor; however, occupational asbestos exposure may also substantially contribute to the observed lung risk profile.")
    if has_obesity and has_inactivity:
        uncertainties.append("Alternative Explanation: Obesity and low physical activity may jointly contribute to the overall metabolic and lifestyle-related risk profile rather than acting as independent drivers.")
    
    if has_genetic_factor:
        uncertainties.append("Alternative Explanation: Genetic predisposition establishes a high baseline risk; lifestyle factors may marginally modulate, but do not replace, the underlying hereditary risk driver.")
    
    if not has_smoke and not has_genetic_factor and not has_asbestos_factor and not has_obesity:
        uncertainties.append("Alternative Explanation: Observed risk may be entirely accounted for by general baseline aging rather than specific environmental or lifestyle exposures.")

    # Fallback default if no uncertainties found
    if not uncertainties:
        uncertainties.append("Baseline environmental interactions are poorly quantified.")

    return uncertainties


def verify_evidence(evidence: EvidencePackage, profile: Optional[PatientProfile] = None) -> List[str]:
    """Verifies scientific quality parameters, evidence limitations, and generates overall critical assessment.

    Args:
        evidence: The EvidencePackage to check.
        profile: Optional PatientProfile.

    Returns:
        A list of study limitations and overall critical assessments.
    """
    limitations = [
        "Occupational history is self-reported and lacks precise quantitative dosimetry."
    ]

    has_high_evidence = any(rf.evidence_strength == "high" for rf in evidence.risk_factors)
    if not has_high_evidence:
        limitations.append("All retrieved documents represent general epidemiological populations rather than high-relevance patient cohorts.")

    # Structured Peer Review: Evidence Limitations
    factors_lower = [rf.factor.lower() for rf in evidence.risk_factors]
    
    if any("alcohol" in f for f in factors_lower):
        limitations.append("Evidence Limitation: Alcohol-related conclusions are supported primarily by observational studies and should not be interpreted as direct causal evidence.")

    if any("obesity" in f or "diet" in f or "inactivity" in f for f in factors_lower):
        limitations.append("Evidence Limitation: Lifestyle risk associations (diet, activity, BMI) rely heavily on epidemiological cohorts with potential self-reporting and confounding biases.")

    if any("environmental" in f or "carcinogen" in f for f in factors_lower):
        limitations.append("Evidence Limitation: Environmental and occupational hazard associations (e.g. asbestos) are established in high-exposure cohorts; risk magnitude for low-exposure environments remains uncertain.")

    if len(evidence.risk_factors) <= 1 and any("baseline" in f or "general" in f for f in factors_lower):
        limitations.append("Evidence Limitation: Reasoning is based on generic environmental baselines without patient-specific high-strength literature support.")

    # Structured Peer Review: Interaction critiques
    interactions = getattr(evidence, "interactions", [])
    for inter in interactions:
        if "asbestos" in inter.name.lower():
            limitations.append("Evidence Limitation: Synergistic interaction between smoking and asbestos is supported only in high-exposure occupational cohorts; low-exposure risk remains uncertain.")
            limitations.append("Evidence Limitation: Missing precise exposure duration or pack-years history reduces precision of tobacco-asbestos synergy estimation.")
        elif "alcohol" in inter.name.lower():
            limitations.append("Evidence Limitation: The alcohol and tobacco synergistic interaction is inferred primarily from observational literature with potential self-reporting and lifestyle confounding biases.")
        elif "obesity" in inter.name.lower() or "diet" in inter.name.lower() or "inactivity" in inter.name.lower():
            limitations.append("Evidence Limitation: Overlapping metabolic pathway interactions are supported by observational studies; clinical trials showing causality are limited.")
        elif "brca" in inter.name.lower():
            limitations.append("Evidence Limitation: Genetic interaction and pedigree penetrance models assume standard inheritance patterns without custom locus sequencing.")

    # Structured Peer Review: Overall Critical Assessment
    has_strong_drivers = any("tobacco" in f or "genetic" in f or "carcinogen" in f for f in factors_lower)
    has_lifestyle_drivers = any("obesity" in f or "diet" in f or "inactivity" in f or "alcohol" in f for f in factors_lower)

    if has_strong_drivers:
        limitations.append("Overall Critical Assessment: The reasoning is well grounded in multiple independent evidence sources. The primary contributors are strongly supported by the literature. However, incomplete family pedigree details and self-reported exposure history reduce confidence in the absolute risk attribution.")
    elif has_lifestyle_drivers:
        limitations.append("Overall Critical Assessment: The reasoning relies on established lifestyle risk associations supported by epidemiological literature. However, lack of precise physical activity logs and long-term BMI trends limits the specificity of the counterfactual recommendations.")
    else:
        limitations.append("Overall Critical Assessment: The reasoning is limited to generic environmental and baseline aging risk. Lacking patient-specific high-strength contributors or genetic variants, the assessment has low specific clinical utility.")

    # Attribution critiques
    if profile is not None:
        limitations.append("Evidence Limitation: Relative risk attribution percentages are approximate estimates derived from epidemiological literature rather than individualized bio-clinical prediction models.")
        limitations.append("Evidence Limitation: Multiple biological pathways overlap (e.g. obesity and inactivity), meaning their independent risk attributions cannot be fully separated.")

    # Evidence Quality Critiques (Sprint 3 Milestone 3)
    qualities = [c.evidence_quality for c in evidence.citations if c.evidence_quality]
    if qualities:
        has_rct = any("Randomized" in q for q in qualities)
        has_guideline = any("Guideline" in q for q in qualities)
        if not has_rct and not has_guideline:
            limitations.append("Evidence Limitation: Reasoning relies primarily on observational literature; limited randomized evidence exists to establish direct causal links.")
        if any("Cohort" in q or "Cross-sectional" in q for q in qualities):
            limitations.append("Evidence Limitation: Recommendations extrapolated from population studies rather than randomized clinical trials.")
        if interactions:
            limitations.append("Evidence Limitation: Synergistic interaction supported mainly by cohort studies with self-reporting biases.")
        if any(rf.evidence_strength in ["medium", "low"] for rf in evidence.risk_factors):
            limitations.append("Evidence Limitation: Evidence consistency is moderate rather than strong across some identified risk factors.")

    return limitations


def retrieve_conflicting_evidence(evidence: EvidencePackage) -> List[ConflictingEvidence]:
    """Retrieves science literature conflicting findings related to risk factors in the evidence package.

    Args:
        evidence: The EvidencePackage containing risk factors.

    Returns:
        A list of ConflictingEvidence objects.
    """
    conflicting = []

    for rf in evidence.risk_factors:
        factor_lower = rf.factor.lower()

        if "tobacco" in factor_lower or "smoke" in factor_lower:
            conflicting.append(
                ConflictingEvidence(
                    factor=rf.factor,
                    evidence="Some historical confounding variables (e.g., occupational exposures) exist in lung cancer cohorts.",
                    source="Epidemiology Journal 2010",
                )
            )
        elif "sun" in factor_lower or "uv" in factor_lower:
            conflicting.append(
                ConflictingEvidence(
                    factor=rf.factor,
                    evidence="Some level of UV exposure is required for natural Vitamin D synthesis and general wellness.",
                    source="Journal of Endocrinology 2015",
                )
            )
        elif "alcohol" in factor_lower:
            conflicting.append(
                ConflictingEvidence(
                    factor=rf.factor,
                    evidence="Moderate cardioprotective claims in older cohorts remain highly controversial and subject to healthy-user bias.",
                    source="JAMA Network Open 2020",
                )
            )

    return conflicting


def detect_missing_information(evidence: EvidencePackage, profile: Optional[PatientProfile] = None) -> List[str]:
    """Detects missing patient details or metrics that could enhance risk analysis precision.

    Args:
        evidence: The EvidencePackage containing identified risk factors.
        profile: The PatientProfile, if available.

    Returns:
        A list of missing data description strings.
    """
    missing_info = []

    # 1. Regression-required checks
    has_genetic = any(
        "genetic" in rf.factor.lower() or "mutation" in rf.factor.lower()
        for rf in evidence.risk_factors
    )
    if not has_genetic:
        missing_info.append("Genetic testing data (e.g. BRCA status is unconfirmed in general profiles)")

    # Fetch profile from stack if None
    if not profile:
        profile = _get_profile_from_stack()

    if profile:
        # Regression checks
        if not profile.environmental_exposure:
            missing_info.append("Quantitative history of environmental exposure to industrial chemicals or radon.")
        if profile.physical_activity.lower() == "medium" or profile.physical_activity.lower() == "low":
            missing_info.append("Detailed dietary logs and cardiorespiratory fitness metrics.")

        # Structured Peer Review: Missing Patient Information
        if profile.smoking_status.lower() == "active":
            missing_info.append("Missing Patient Information: Detailed smoking intensity (pack-years/frequency) to quantify cumulative carcinogen dose.")
        
        if profile.alcohol_use.lower() in ["moderate", "heavy"]:
            missing_info.append("Missing Patient Information: Alcohol consumption frequency and specific beverage type to evaluate precise acetaldehyde exposure.")
            
        if profile.environmental_exposure:
            missing_info.append("Missing Patient Information: Precise duration and quantitative dosimetry of environmental/occupational exposure.")
            
        if profile.family_history:
            missing_info.append("Missing Patient Information: Detailed family pedigree (onset ages and specific cancer types in first-degree relatives).")
        else:
            missing_info.append("Missing Patient Information: Comprehensive family history validation and genetic screening results for baseline verification.")
            
        if profile.bmi > 25.0:
            missing_info.append("Missing Patient Information: BMI trends over time and body composition metrics (fat-free mass vs. visceral adiposity).")
            
        if profile.physical_activity.lower() in ["low", "medium"]:
            missing_info.append("Missing Patient Information: Cardiorespiratory fitness metrics and detailed physical activity logs.")

    return missing_info


def calculate_confidence(
    evidence: EvidencePackage,
    causality: CausalityPackage,
    uncertainties: List[str]
) -> str:
    """Dynamically estimates confidence level from evidence and causality metrics.

    Evaluates:
    - Quantity: number of retrieved documents and citations (max 0.25)
    - Quality: average and maximum evidence scores (max 0.35)
    - Grounding: presence of established high-quality drivers (max 0.25)
    - Skeptic Auditing: deductions for uncertainties (max 0.15)
    """
    # 1. Quantity score (max 0.25)
    num_docs = len(evidence.retrieved_documents)
    if num_docs >= 8:
        quantity = 0.25
    elif num_docs >= 4:
        quantity = 0.15
    elif num_docs >= 1:
        quantity = 0.05
    else:
        quantity = 0.0

    # 2. Quality score (max 0.35)
    if evidence.risk_factors:
        max_score = max(rf.evidence_score for rf in evidence.risk_factors)
        avg_score = sum(rf.evidence_score for rf in evidence.risk_factors) / len(evidence.risk_factors)
        quality = 0.20 * max_score + 0.15 * avg_score
    else:
        quality = 0.0

    # 3. Grounding & Specificity (max 0.25)
    # Check if we have strong genetic, smoking or environmental carcinogen exposure factors
    strong_factors = {"Tobacco Smoke Exposure", "Genetic/Familial Predisposition", "Environmental Carcinogen Exposure"}
    moderate_factors = {"Obesity-related Cancer Risk", "Alcohol Consumption Risk", "Poor Dietary Pattern", "Physical Inactivity", "UV/Sun Exposure"}
    
    has_strong = any(rf.factor in strong_factors for rf in evidence.risk_factors)
    has_moderate = any(rf.factor in moderate_factors for rf in evidence.risk_factors)
    
    if has_strong:
        grounding = 0.25
    elif has_moderate:
        grounding = 0.15
    else:
        grounding = 0.05

    # 4. Skeptic Auditing (max 0.15)
    # Deduct 0.05 for each uncertainty found, starting at 0.15, minimum 0.0
    # Ignore default fallback uncertainty so it doesn't penalize normal profiles
    actual_uncs = [u for u in uncertainties if "Baseline environmental interactions" not in u]
    skeptic_contrib = max(0.0, 0.15 - (0.05 * len(actual_uncs)))

    total_score = quantity + quality + grounding + skeptic_contrib

    # Evidence hierarchy adjustments (Sprint 3 Milestone 3)
    qualities = [c.evidence_quality for c in evidence.citations if c.evidence_quality]
    
    # Guideline-supported reasoning boost
    if any("Guideline" in q for q in qualities):
        total_score += 0.05
        
    # Multiple meta-analyses boost
    meta_count = sum(1 for q in qualities if "Systematic Review / Meta-analysis" in q)
    if meta_count >= 2:
        total_score += 0.05
        
    # Isolated observational evidence (no guidelines, no meta-analyses, no RCTs)
    has_high_quality = any(x in q for q in qualities for x in ["Guideline", "Review", "Meta", "Randomized"])
    if not has_high_quality and qualities:
        total_score -= 0.08

    # Boost confidence score if there is a high-strength synergistic interaction
    interactions = getattr(evidence, "interactions", [])
    if any(inter.strength == "high" for inter in interactions):
        total_score += 0.08

    if total_score >= 0.75:
        return "high"
    elif total_score >= 0.45:
        return "medium"
    else:
        return "low"


def create_skeptic_package(
    confidence: str,
    uncertainties: List[str],
    limitations: List[str],
    conflicting_evidence: List[ConflictingEvidence],
    missing_information: List[str],
    recommended_questions: Optional[List[FollowUpQuestion]] = None,
) -> SkepticPackage:
    """Wraps audited results into a valid SkepticPackage contract.

    Args:
        confidence: The adjusted confidence level (high, medium, low).
        uncertainties: List of identified uncertainties.
        limitations: List of identified limitations.
        conflicting_evidence: List of ConflictingEvidence objects.
        missing_information: List of missing information logs.
        recommended_questions: List of recommended follow-up questions.

    Returns:
        A SkepticPackage instance.
    """
    if recommended_questions is None:
        recommended_questions = []
    return SkepticPackage(
        confidence=confidence,
        uncertainties=uncertainties,
        limitations=limitations,
        conflicting_evidence=conflicting_evidence,
        missing_information=missing_information,
        recommended_questions=recommended_questions,
    )
