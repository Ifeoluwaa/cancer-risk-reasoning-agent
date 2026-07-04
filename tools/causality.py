"""causality.py

Causality reasoning tools for ranking cancer risk factors and identifying primary drivers.
"""

from typing import List, Optional
from schemas.contracts import PatientProfile, RiskFactor, Contributor


def rank_contributors(factors: List[RiskFactor], profile: Optional[PatientProfile] = None) -> List[Contributor]:
    """Ranks identified risk factors by evidence score in descending order and formats explanation reasons.

    Args:
        factors: A list of identified RiskFactor schemas.
        profile: An optional PatientProfile to personalize explanation reasons.

    Returns:
        A list of Contributor schemas.
    """
    from tools.attribution import calculate_attribution
    from schemas.contracts import EvidencePackage

    if profile is not None:
        # Detect active interactions if present in the caller/stack or via detection
        from tools.interaction import detect_interactions
        interactions = detect_interactions(profile, factors)
        evidence = EvidencePackage(risk_factors=factors, citations=[], retrieved_documents=[], interactions=interactions)
        return calculate_attribution(profile, evidence)

    sorted_factors = sorted(factors, key=lambda f: f.evidence_score, reverse=True)

    contributors = []
    for i, rf in enumerate(sorted_factors):
        rank = i + 1
        reason = f"Ranked {rank} contributor with {rf.evidence_strength} evidence strength (score: {rf.evidence_score:.2f})."

        from tools.impact_tier import classify_impact_tier, generate_visual_bar
        fallback_score = rf.evidence_score * 100.0 if rf.evidence_score is not None else 0.0
        contributors.append(
            Contributor(
                factor=rf.factor,
                rank=rank,
                reason=reason,
                impact_tier=classify_impact_tier(fallback_score),
                impact_bar=generate_visual_bar(fallback_score)
            )
        )
    return contributors


def identify_primary_drivers(contributors: List[Contributor], threshold_rank: int = 1) -> List[str]:
    """Identifies the primary risk drivers from the ranked list of contributors.

    Args:
        contributors: A list of Contributor schemas.
        threshold_rank: The rank limit up to which contributors are considered primary drivers (inclusive).

    Returns:
        A list of string factor names representing the primary drivers.
    """
    return [c.factor for c in contributors if c.rank <= threshold_rank]
