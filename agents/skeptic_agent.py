"""Skeptic Agent implementation for CRRA.

Responsible for identifying uncertainty, missing information, and conflicting evidence in conclusions.
"""

from schemas.contracts import (
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
    ) -> SkepticPackage:
        """Evaluates previous steps and identifies limitations and uncertainty.

        Args:
            evidence: The EvidencePackage from the Evidence Agent.
            causality: The CausalityPackage from the Causality Agent.
            counterfactual: The CounterfactualPackage from the Counterfactual Agent.

        Returns:
            A SkepticPackage with critiqued findings and adjusted confidence scores.
        """
        uncertainties = []
        limitations = []
        conflicting = []
        missing_info = []

        # Check for genetic details in the evidence
        has_genetic = any("genetic" in rf.factor.lower() or "mutation" in rf.factor.lower() for rf in evidence.risk_factors)
        if not has_genetic:
            missing_info.append("Genetic testing data (e.g. BRCA status is unconfirmed in general profiles)")
            uncertainties.append("Causal link assumes default baseline without custom germline variant screening.")

        # Check for occupational exposure
        limitations.append("Occupational history is self-reported and lacks precise quantitative dosimetry.")

        # Gather any conflicting evidence mock info
        for rf in evidence.risk_factors:
            if "tobacco" in rf.factor.lower() or "smoke" in rf.factor.lower():
                conflicting.append(
                    ConflictingEvidence(
                        factor=rf.factor,
                        evidence="Some historical confounding variables (e.g., occupational exposures) exist in lung cancer cohorts.",
                        source="Epidemiology Journal 2010",
                    )
                )

        # Default adjustment of confidence
        adjusted_confidence = "medium"
        if causality.causal_confidence == "high" and len(uncertainties) == 0:
            adjusted_confidence = "high"
        elif causality.causal_confidence == "low":
            adjusted_confidence = "low"

        return SkepticPackage(
            confidence=adjusted_confidence,
            uncertainties=uncertainties or ["Baseline environmental interactions are poorly quantified."],
            limitations=limitations,
            conflicting_evidence=conflicting,
            missing_information=missing_info,
        )
