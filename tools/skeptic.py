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
)


def find_uncertainties(evidence: EvidencePackage, causality: CausalityPackage) -> List[str]:
    """Identifies logical or structural uncertainties in the accumulated evidence and causality packages.

    Args:
        evidence: The EvidencePackage containing identified risk factors.
        causality: The CausalityPackage detailing ranked contributors.

    Returns:
        A list of uncertainty strings.
    """
    uncertainties = []

    has_genetic = any(
        "genetic" in rf.factor.lower() or "mutation" in rf.factor.lower()
        for rf in evidence.risk_factors
    )
    if not has_genetic:
        uncertainties.append("Causal link assumes default baseline without custom germline variant screening.")

    if causality.causal_confidence == "low":
        uncertainties.append("Causal confidence is low due to weak evidence scoring in primary drivers.")

    # Fallback default if no uncertainties found
    if not uncertainties:
        uncertainties.append("Baseline environmental interactions are poorly quantified.")

    return uncertainties


def verify_evidence(evidence: EvidencePackage) -> List[str]:
    """Verifies scientific quality parameters and self-reporting limitations of the evidence.

    Args:
        evidence: The EvidencePackage to check.

    Returns:
        A list of study limitation or validation warning strings.
    """
    limitations = [
        "Occupational history is self-reported and lacks precise quantitative dosimetry."
    ]

    has_high_evidence = any(rf.evidence_strength == "high" for rf in evidence.risk_factors)
    if not has_high_evidence:
        limitations.append("All retrieved documents represent general epidemiological populations rather than high-relevance patient cohorts.")

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

    has_genetic = any(
        "genetic" in rf.factor.lower() or "mutation" in rf.factor.lower()
        for rf in evidence.risk_factors
    )
    if not has_genetic:
        missing_info.append("Genetic testing data (e.g. BRCA status is unconfirmed in general profiles)")

    if profile:
        if not profile.environmental_exposure:
            missing_info.append("Quantitative history of environmental exposure to industrial chemicals or radon.")
        if profile.physical_activity.lower() == "medium" or profile.physical_activity.lower() == "low":
            missing_info.append("Detailed dietary logs and cardiorespiratory fitness metrics.")

    return missing_info


def create_skeptic_package(
    confidence: str,
    uncertainties: List[str],
    limitations: List[str],
    conflicting_evidence: List[ConflictingEvidence],
    missing_information: List[str],
) -> SkepticPackage:
    """Wraps audited results into a valid SkepticPackage contract.

    Args:
        confidence: The adjusted confidence level (high, medium, low).
        uncertainties: List of identified uncertainties.
        limitations: List of identified limitations.
        conflicting_evidence: List of ConflictingEvidence objects.
        missing_information: List of missing information logs.

    Returns:
        A SkepticPackage instance.
    """
    return SkepticPackage(
        confidence=confidence,
        uncertainties=uncertainties,
        limitations=limitations,
        conflicting_evidence=conflicting_evidence,
        missing_information=missing_information,
    )
