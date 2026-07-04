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
        from tools.causality import rank_contributors
        contributors = rank_contributors(evidence.risk_factors, profile=profile)

        # Primary drivers are those classified as Primary Driver or Major Contributor
        primary_drivers = [
            c.factor for c in contributors
            if c.classification in ["Primary Driver", "Major Contributor"]
        ]

        if not primary_drivers and contributors:
            primary_drivers = [contributors[0].factor]

        # Determine causality confidence
        causal_confidence = "low"
        if evidence.risk_factors:
            sorted_factors = sorted(evidence.risk_factors, key=lambda x: x.evidence_score, reverse=True)
            causal_confidence = sorted_factors[0].evidence_strength
            # If any participating factor has high interaction strength, boost causal confidence
            interactions = getattr(evidence, "interactions", [])
            if any(inter.strength == "high" for inter in interactions):
                causal_confidence = "high"

        return CausalityPackage(
            ranked_contributors=contributors,
            primary_drivers=primary_drivers,
            causal_confidence=causal_confidence,
        )
