"""Causality Agent implementation for CRRA.

Responsible for ranking the identified contributors and identifying the primary drivers of future cancer risk.
"""

from schemas.contracts import PatientProfile, EvidencePackage, CausalityPackage, Contributor


class CausalityAgent:
    """Causality Agent that ranks risk factors by priority and evaluates causal pathways."""

    def __init__(self) -> None:
        """Initialize the Causality Agent."""
        pass

    def run(self, profile: PatientProfile, evidence: EvidencePackage) -> CausalityPackage:
        """Ranks identified contributors based on evidence and clinical history.

        Args:
            profile: The sanitized PatientProfile.
            evidence: The EvidencePackage containing identified risk factors.

        Returns:
            A CausalityPackage detailing ranked contributors and primary drivers.
        """
        contributors = []
        primary_drivers = []

        # Sort the factors by evidence score as a default mock logic
        sorted_factors = sorted(evidence.risk_factors, key=lambda x: x.evidence_score, reverse=True)

        for i, rf in enumerate(sorted_factors):
            rank = i + 1
            reason = f"Identified as contributor of rank {rank} because of evidence score {rf.evidence_score:.2f}."
            contributors.append(
                Contributor(
                    factor=rf.factor,
                    rank=rank,
                    reason=reason,
                )
            )
            if rank == 1:
                primary_drivers.append(rf.factor)

        # Mock causality confidence based on top driver evidence strength
        causal_confidence = "low"
        if sorted_factors:
            causal_confidence = sorted_factors[0].evidence_strength

        return CausalityPackage(
            ranked_contributors=contributors,
            primary_drivers=primary_drivers,
            causal_confidence=causal_confidence,
        )
