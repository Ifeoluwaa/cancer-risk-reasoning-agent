"""Skeptic Agent implementation for CRRA.

Responsible for identifying uncertainty, missing information, and conflicting evidence in conclusions.
"""

from typing import Optional
from schemas.contracts import (
    PatientProfile,
    EvidencePackage,
    CausalityPackage,
    CounterfactualPackage,
    SkepticPackage,
    ConflictingEvidence,
)


class SkepticAgent:
    """Skeptic Agent that audits other agents' outputs, highlighting gaps and conflicting information."""

    def __init__(self) -> None:
        """Initialize the Skeptic Agent."""
        pass

    def run(
        self,
        evidence: EvidencePackage,
        causality: CausalityPackage,
        counterfactual: CounterfactualPackage,
        profile: Optional[PatientProfile] = None,
    ) -> SkepticPackage:
        """Evaluates previous steps and identifies limitations and uncertainty.

        Args:
            evidence: The EvidencePackage from the Evidence Agent.
            causality: The CausalityPackage from the Causality Agent.
            counterfactual: The CounterfactualPackage from the Counterfactual Agent.
            profile: Optional PatientProfile.

        Returns:
            A SkepticPackage with critiqued findings and adjusted confidence scores.
        """
        from tools.skeptic import (
            find_uncertainties,
            verify_evidence,
            retrieve_conflicting_evidence,
            detect_missing_information,
            calculate_confidence
        )

        uncertainties = find_uncertainties(evidence, causality, profile=profile)
        limitations = verify_evidence(evidence, profile=profile)
        conflicting = retrieve_conflicting_evidence(evidence)
        missing_info = detect_missing_information(evidence, profile=profile)

        # Dynamic adjustment of confidence based on evidence quality and quantity
        adjusted_confidence = calculate_confidence(evidence, causality, uncertainties)

        from tools.questioning import generate_followup_questions

        recommended_questions = []
        if profile:
            recommended_questions = generate_followup_questions(profile, evidence, uncertainties)

        return SkepticPackage(
            confidence=adjusted_confidence,
            uncertainties=uncertainties,
            limitations=limitations,
            conflicting_evidence=conflicting,
            missing_information=missing_info,
            recommended_questions=recommended_questions,
        )
