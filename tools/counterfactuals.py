"""counterfactuals.py

Tools for simulating hypothetical lifestyle modifications and evaluating comparative risk impacts.
"""

from typing import List
from schemas.contracts import PatientProfile, Scenario, Comparison


def generate_scenarios(
    profile: PatientProfile, primary_drivers: List[str]
) -> List[Scenario]:
    """Generates what-if lifestyle or exposure scenarios based on a patient profile and top drivers.

    In future stages, this tool will:
    1. Identify modifiable lifestyle parameters (e.g. diet, smoking, physical activity).
    2. Propose realistic, specific lifestyle changes.
    3. Project expected impact grades (high, medium, low) using epidemiological logic.

    Args:
        profile: The PatientProfile containing patient habits.
        primary_drivers: Top drivers identified in previous causality analysis.

    Returns:
        A list of Scenario schema objects representing hypothetical changes.
    """
    scenarios = []

    # Propose changes for smoking
    has_smoking = any("smoke" in d.lower() or "tobacco" in d.lower() for d in primary_drivers)
    if has_smoking:
        scenarios.append(
            Scenario(
                scenario_id="S_SMOKE_STOP",
                change="Complete smoking cessation",
                expected_effect="high",
                reasoning="Eliminating tobacco exposure stops further accumulation of mutagenic chemicals.",
            )
        )
        scenarios.append(
            Scenario(
                scenario_id="S_SMOKE_HALF",
                change="Reduce smoking by 50%",
                expected_effect="medium",
                reasoning="Decreases overall toxin dose but does not halt cumulative cellular damage entirely.",
            )
        )

    # General fitness/lifestyle proposals
    if profile.bmi > 25:
        scenarios.append(
            Scenario(
                scenario_id="S_WEIGHT_LOSS",
                change="Achieve a healthy BMI (reduce by 5-10%)",
                expected_effect="medium",
                reasoning="Reduces chronic adipose inflammation which is a known tumor promoter.",
            )
        )

    # Fallback/General scenarios
    if not scenarios:
        scenarios.append(
            Scenario(
                scenario_id="S_FITNESS",
                change="Increase cardiovascular physical activity to 150 minutes per week",
                expected_effect="medium",
                reasoning="Enhances immune surveillance and metabolic regulation.",
            )
        )

    return scenarios


def compare_scenarios(scenarios: List[Scenario]) -> List[Comparison]:
    """Performs a pairwise comparison between generated scenarios to determine relative impact.

    In future stages, this tool will:
    1. Calculate relative hazard ratio reductions for the scenarios.
    2. Rank the options to help the user identify the most impactful change.

    Args:
        scenarios: The list of generated scenarios.

    Returns:
        A list of Comparison objects showing relative benefits.
    """
    comparisons = []
    if len(scenarios) >= 2:
        comparisons.append(
            Comparison(
                scenario_a=scenarios[0].scenario_id,
                scenario_b=scenarios[1].scenario_id,
                higher_impact=(
                    f"Cessation or larger reduction in {scenarios[0].change} has a higher expected "
                    f"impact than minor reductions or lifestyle changes like {scenarios[1].change}."
                ),
            )
        )
    return comparisons
