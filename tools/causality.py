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
    sorted_factors = sorted(factors, key=lambda f: f.evidence_score, reverse=True)

    contributors = []
    for i, rf in enumerate(sorted_factors):
        rank = i + 1
        reason = f"Ranked {rank} contributor with {rf.evidence_strength} evidence strength (score: {rf.evidence_score:.2f})."

        if profile:
            factor_lower = rf.factor.lower()
            if "smoke" in factor_lower or "tobacco" in factor_lower:
                reason += f" Matches patient history of smoking {profile.smoking_years} years."
            elif "age" in factor_lower:
                reason += f" Matches patient age of {profile.age} years (increases susceptibility)."
            elif "genetic" in factor_lower or "familial" in factor_lower:
                mutations_str = ", ".join(profile.known_mutations) if profile.known_mutations else "none detected"
                reason += f" Matches family history of cancer with mutations: {mutations_str}."
            elif "sun" in factor_lower or "uv" in factor_lower:
                reason += f" Matches history of high sun exposure ({profile.sun_exposure})."
            elif "alcohol" in factor_lower:
                reason += f" Matches alcohol consumption level of {profile.alcohol_use}."

        contributors.append(
            Contributor(
                factor=rf.factor,
                rank=rank,
                reason=reason,
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
