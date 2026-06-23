"""Counterfactual Agent implementation for CRRA.

Responsible for generating alternative/what-if scenarios and comparing them to show potential impacts.
"""

from typing import List
from schemas.contracts import PatientProfile, CounterfactualPackage, Scenario, Comparison


class CounterfactualAgent:
    """Counterfactual Agent that generates lifestyle or exposure scenario modifications and compares outcomes."""

    def __init__(self) -> None:
        """Initialize the Counterfactual Agent."""
        pass

    def run(self, profile: PatientProfile, primary_drivers: List[str]) -> CounterfactualPackage:
        """Generates alternative scenarios and comparative outcomes based on primary drivers.

        Args:
            profile: The sanitized PatientProfile.
            primary_drivers: The list of top contributors or drivers.

        Returns:
            A CounterfactualPackage containing scenarios and comparative insights.
        """
        scenarios = []
        comparisons = []

        # Check if tobacco exposure is a driver
        has_tobacco = any("tobacco" in d.lower() or "smoke" in d.lower() for d in primary_drivers)

        if has_tobacco:
            scenarios.append(
                Scenario(
                    scenario_id="S1",
                    change="Complete smoking cessation",
                    expected_effect="high",
                    reasoning="Stopping tobacco use stops the inhalation of carcinogens, allowing tissues to heal.",
                )
            )
            scenarios.append(
                Scenario(
                    scenario_id="S2",
                    change="Reducing smoking by 50%",
                    expected_effect="medium",
                    reasoning="Reduction decreases exposure dose but does not eliminate the elevated mutagenic risk entirely.",
                )
            )
            comparisons.append(
                Comparison(
                    scenario_a="S1",
                    scenario_b="S2",
                    higher_impact="S1 has a significantly higher impact as total cessation halts mutagenic accumulation.",
                )
            )
        else:
            # General fallback scenario
            scenarios.append(
                Scenario(
                    scenario_id="S1",
                    change="Increase physical activity to 150 mins/week",
                    expected_effect="medium",
                    reasoning="Improves immune function and reduces systemic inflammation.",
                )
            )
            scenarios.append(
                Scenario(
                    scenario_id="S2",
                    change="Adopt a high-fiber, low-red-meat diet",
                    expected_effect="medium",
                    reasoning="Supports gut microbiome and minimizes colorectal exposure to dietary mutagens.",
                )
            )
            comparisons.append(
                Comparison(
                    scenario_a="S1",
                    scenario_b="S2",
                    higher_impact="Both scenarios have complementary benefits, with S1 showing broad systemic advantages.",
                )
            )

        return CounterfactualPackage(
            scenarios=scenarios,
            comparisons=comparisons,
        )
