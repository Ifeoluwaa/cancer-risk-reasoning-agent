"""Counterfactual Agent implementation for CRRA.

Responsible for generating alternative/what-if scenarios and comparing them to show potential impacts.
"""

from typing import List, Optional
from schemas.contracts import PatientProfile, CounterfactualPackage, Scenario, Comparison, EvidencePackage
from tools.counterfactuals import generate_scenarios, compare_scenarios


class CounterfactualAgent:
    """Counterfactual Agent that generates lifestyle or exposure scenario modifications and compares outcomes."""

    def __init__(self) -> None:
        """Initialize the Counterfactual Agent."""
        pass

    def run(
        self,
        profile: PatientProfile,
        primary_drivers: List[str],
        evidence: Optional[EvidencePackage] = None,
    ) -> CounterfactualPackage:
        """Generates alternative scenarios and comparative outcomes based on primary drivers.

        Args:
            profile: The sanitized PatientProfile.
            primary_drivers: The list of top contributors or drivers.
            evidence: Optional EvidencePackage.

        Returns:
            A CounterfactualPackage containing scenarios and comparative insights.
        """
        scenarios = generate_scenarios(profile, primary_drivers, evidence=evidence)
        comparisons = compare_scenarios(scenarios)

        return CounterfactualPackage(
            scenarios=scenarios,
            comparisons=comparisons,
        )
