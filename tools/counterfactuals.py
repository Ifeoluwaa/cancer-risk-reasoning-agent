"""counterfactuals.py

Tools for simulating hypothetical lifestyle modifications and evaluating comparative risk impacts.
"""

from typing import List, Union
from schemas.contracts import PatientProfile, Scenario, Comparison, CausalityPackage, CounterfactualPackage


def generate_scenarios(
    profile: PatientProfile, causality_or_drivers: Union[CausalityPackage, List[str]]
) -> List[Scenario]:
    """Generates what-if lifestyle or exposure scenarios based on a patient profile and top drivers.

    Args:
        profile: The PatientProfile containing patient habits.
        causality_or_drivers: The CausalityPackage or list of primary driver strings.

    Returns:
        A list of Scenario schema objects representing hypothetical changes.
    """
    if isinstance(causality_or_drivers, CausalityPackage):
        primary_drivers = causality_or_drivers.primary_drivers
    else:
        primary_drivers = causality_or_drivers

    scenarios = []

    # Map drivers to counterfactual scenario proposals
    for driver in primary_drivers:
        driver_lower = driver.lower()

        if "smoke" in driver_lower or "tobacco" in driver_lower:
            scenarios.append(
                Scenario(
                    scenario_id="S_SMOKE_STOP",
                    change="Complete smoking cessation",
                    expected_effect="high",
                    reasoning="Stopping tobacco use stops the inhalation of carcinogens, allowing lung tissues to heal.",
                )
            )
            scenarios.append(
                Scenario(
                    scenario_id="S_SMOKE_HALF",
                    change="Reduce smoking by 50%",
                    expected_effect="medium",
                    reasoning="Reduction decreases exposure dose but does not eliminate the elevated mutagenic risk entirely.",
                )
            )
        elif "sun" in driver_lower or "uv" in driver_lower:
            scenarios.append(
                Scenario(
                    scenario_id="S_SUN_PROTECT",
                    change="Apply SPF 30+ sunscreen daily and wear protective clothing",
                    expected_effect="high",
                    reasoning="Daily SPF and physical covers shield skin cells from damaging ultraviolet radiation.",
                )
            )
            scenarios.append(
                Scenario(
                    scenario_id="S_SUN_LIMIT",
                    change="Limit direct sun exposure during peak UV hours (10 AM to 4 PM)",
                    expected_effect="medium",
                    reasoning="Reduces intensity of peak exposure, though off-peak damage accumulation remains possible.",
                )
            )
        elif "alcohol" in driver_lower:
            scenarios.append(
                Scenario(
                    scenario_id="S_ALCOHOL_STOP",
                    change="Cessation of alcohol consumption",
                    expected_effect="high",
                    reasoning="Eliminates exposure to acetaldehyde, a primary metabolite and known carcinogen.",
                )
            )
            scenarios.append(
                Scenario(
                    scenario_id="S_ALCOHOL_LIMIT",
                    change="Limit alcohol intake to under 1 drink per week",
                    expected_effect="medium",
                    reasoning="Significantly reduces exposure dose but doesn't reach absolute baseline risk.",
                )
            )
        elif "age" in driver_lower:
            scenarios.append(
                Scenario(
                    scenario_id="S_CELL_ANTIOXIDANT",
                    change="Adopt a diet high in antioxidants and polyphenols",
                    expected_effect="medium",
                    reasoning="Helps mitigate oxidative stress, reducing the rate of age-related cellular senescence.",
                )
            )
        elif "genetic" in driver_lower or "familial" in driver_lower:
            scenarios.append(
                Scenario(
                    scenario_id="S_GENETIC_SCREEN",
                    change="Undergo annual clinical screening and surveillance",
                    expected_effect="high",
                    reasoning="Allows early detection of precursor lesions when treatment efficacy is highest.",
                )
            )

    # General fitness/lifestyle proposals if BMI is high and not covered by primary drivers
    if profile.bmi > 25.0 and not any("weight" in s.scenario_id.lower() for s in scenarios):
        scenarios.append(
            Scenario(
                scenario_id="S_WEIGHT_LOSS",
                change="Achieve a healthy BMI (reduce by 5-10%)",
                expected_effect="medium",
                reasoning="Reduces chronic adipose inflammation which is a known tumor promoter.",
            )
        )

    # General fallback scenarios if no specific drivers were matched
    if not scenarios:
        scenarios.append(
            Scenario(
                scenario_id="S_FITNESS",
                change="Increase cardiovascular physical activity to 150 minutes per week",
                expected_effect="medium",
                reasoning="Enhances immune surveillance and metabolic regulation.",
            )
        )
        scenarios.append(
            Scenario(
                scenario_id="S_DIET",
                change="Adopt a high-fiber, low-red-meat diet",
                expected_effect="medium",
                reasoning="Supports gut health and minimizes exposure to dietary mutagens.",
            )
        )

    return scenarios


def compare_scenarios(scenarios: List[Scenario]) -> List[Comparison]:
    """Performs a pairwise comparison between generated scenarios to determine relative impact.

    Args:
        scenarios: The list of generated scenarios.

    Returns:
        A list of Comparison objects showing relative benefits.
    """
    comparisons = []
    if len(scenarios) >= 2:
        effect_rank = {"high": 3, "medium": 2, "low": 1}

        for i in range(len(scenarios) - 1):
            s_a = scenarios[i]
            s_b = scenarios[i + 1]

            rank_a = effect_rank.get(s_a.expected_effect.lower(), 0)
            rank_b = effect_rank.get(s_b.expected_effect.lower(), 0)

            if rank_a > rank_b:
                higher_impact = (
                    f"{s_a.change} ({s_a.expected_effect} expected effect) has a higher expected "
                    f"risk reduction benefit than {s_b.change} ({s_b.expected_effect} expected effect) "
                    f"due to more direct mitigation of key exposure pathways."
                )
            elif rank_b > rank_a:
                higher_impact = (
                    f"{s_b.change} ({s_b.expected_effect} expected effect) has a higher expected "
                    f"risk reduction benefit than {s_a.change} ({s_a.expected_effect} expected effect) "
                    f"due to more direct mitigation of key exposure pathways."
                )
            else:
                higher_impact = (
                    f"Both {s_a.change} and {s_b.change} show comparable expected risk "
                    f"reduction benefits, addressing complementary health habits."
                )

            comparisons.append(
                Comparison(
                    scenario_a=s_a.scenario_id,
                    scenario_b=s_b.scenario_id,
                    higher_impact=higher_impact,
                )
            )

    return comparisons


def create_counterfactual_package(
    scenarios: List[Scenario], comparisons: List[Comparison]
) -> CounterfactualPackage:
    """Wraps scenarios and comparisons into a valid CounterfactualPackage contract.

    Args:
        scenarios: List of generated Scenario objects.
        comparisons: List of Comparison objects.

    Returns:
        A CounterfactualPackage instance.
    """
    return CounterfactualPackage(scenarios=scenarios, comparisons=comparisons)

