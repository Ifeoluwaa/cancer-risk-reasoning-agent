"""counterfactuals.py

Tools for simulating hypothetical lifestyle modifications and evaluating comparative risk impacts.
"""

from typing import List, Union, Optional
from schemas.contracts import PatientProfile, Scenario, Comparison, CausalityPackage, CounterfactualPackage, RiskFactor, EvidencePackage


def generate_scenarios(
    profile: PatientProfile,
    causality_or_drivers: Union[CausalityPackage, List[str]],
    evidence: Optional[EvidencePackage] = None,
) -> List[Scenario]:
    """Generates what-if lifestyle or exposure scenarios based on a patient profile and top drivers.

    Args:
        profile: The PatientProfile containing patient habits.
        causality_or_drivers: The CausalityPackage or list of primary driver strings.
        evidence: Optional EvidencePackage containing identified risk factors and citations.

    Returns:
        A list of Scenario schema objects representing hypothetical changes.
    """
    if isinstance(causality_or_drivers, CausalityPackage):
        primary_drivers = causality_or_drivers.primary_drivers
    else:
        primary_drivers = causality_or_drivers

    # Define non-modifiable factors details
    non_modifiable_details = []
    if profile.age > 50:
        non_modifiable_details.append(f"age cellular senescence ({profile.age} years)")
    if profile.family_history:
        non_modifiable_details.append("family history of cancer")
    if profile.known_mutations:
        non_modifiable_details.append(f"genetic mutations ({', '.join(profile.known_mutations)})")
    if profile.previous_cancer_history:
        non_modifiable_details.append("previous malignancy history")

    driver_to_factor = {
        "Tobacco Smoke Exposure": "smoking",
        "Obesity-related Cancer Risk": "bmi",
        "Alcohol Consumption Risk": "alcohol",
        "Poor Dietary Pattern": "diet",
        "Physical Inactivity": "activity",
        "UV/Sun Exposure": "uv"
    }

    # Define modifiable, unsatisfied risk factors
    modifiable_unsatisfied = {}
    if profile.smoking_status.lower() == "active":
        modifiable_unsatisfied["smoking"] = {
            "factor_name": "Tobacco Smoke Exposure",
            "scenarios": [
                Scenario(
                    scenario_id="S_SMOKE_STOP",
                    change="Complete smoking cessation",
                    expected_effect="high",
                    reasoning=""
                ),
                Scenario(
                    scenario_id="S_SMOKE_HALF",
                    change="Reduce smoking by 50%",
                    expected_effect="medium",
                    reasoning=""
                )
            ]
        }
    if profile.bmi > 25.0:
        modifiable_unsatisfied["bmi"] = {
            "factor_name": "Obesity-related Cancer Risk",
            "scenarios": [
                Scenario(
                    scenario_id="S_WEIGHT_LOSS",
                    change="Achieve a healthy BMI (reduce by 5-10%)",
                    expected_effect="medium",
                    reasoning=""
                )
            ]
        }
    if profile.alcohol_use.lower() in ["moderate", "heavy"]:
        modifiable_unsatisfied["alcohol"] = {
            "factor_name": "Alcohol Consumption Risk",
            "scenarios": [
                Scenario(
                    scenario_id="S_ALCOHOL_STOP",
                    change="Cessation of alcohol consumption",
                    expected_effect="high",
                    reasoning=""
                ),
                Scenario(
                    scenario_id="S_ALCOHOL_LIMIT",
                    change="Limit alcohol intake to under 1 drink per week",
                    expected_effect="medium",
                    reasoning=""
                )
            ]
        }
    if profile.diet_quality.lower() in ["low", "medium"]:
        modifiable_unsatisfied["diet"] = {
            "factor_name": "Poor Dietary Pattern",
            "scenarios": [
                Scenario(
                    scenario_id="S_DIET",
                    change="Adopt a high-fiber, low-red-meat, low-processed-food diet",
                    expected_effect="medium",
                    reasoning=""
                )
            ]
        }
    if profile.physical_activity.lower() in ["low", "medium"]:
        modifiable_unsatisfied["activity"] = {
            "factor_name": "Physical Inactivity",
            "scenarios": [
                Scenario(
                    scenario_id="S_FITNESS",
                    change="Increase cardiovascular physical activity to 150 minutes per week",
                    expected_effect="medium",
                    reasoning=""
                )
            ]
        }
    if profile.sun_exposure.lower() == "high":
        modifiable_unsatisfied["uv"] = {
            "factor_name": "UV/Sun Exposure",
            "scenarios": [
                Scenario(
                    scenario_id="S_SUN_PROTECT",
                    change="Apply SPF 30+ sunscreen daily and wear protective clothing",
                    expected_effect="high",
                    reasoning=""
                ),
                Scenario(
                    scenario_id="S_SUN_LIMIT",
                    change="Limit direct sun exposure during peak UV hours (10 AM to 4 PM)",
                    expected_effect="medium",
                    reasoning=""
                )
            ]
        }

    # Extract attribution map from CausalityPackage if available
    attr_map = {}
    if isinstance(causality_or_drivers, CausalityPackage):
        for c in causality_or_drivers.ranked_contributors:
            if c.attribution_percentage is not None:
                attr_map[c.factor] = c.attribution_percentage

    # Add default fallbacks for all modifiable factors to avoid missing values
    fallback_pcts = {
        "Tobacco Smoke Exposure": 35.0,
        "Obesity-related Cancer Risk": 20.0,
        "Alcohol Consumption Risk": 15.0,
        "Poor Dietary Pattern": 12.0,
        "Physical Inactivity": 10.0,
        "UV/Sun Exposure": 8.0,
    }
    for key, info in modifiable_unsatisfied.items():
        factor_name = info["factor_name"]
        pct = attr_map.get(factor_name, fallback_pcts.get(factor_name, 10.0))
        info["attribution_percentage"] = pct
        priority = pct
        if factor_name in primary_drivers:
            priority += 1000.0
        info["sort_priority"] = priority

    # Order/Prioritize modifiable factors based on sort priority descending
    ordered_keys = sorted(
        modifiable_unsatisfied.keys(),
        key=lambda k: modifiable_unsatisfied[k]["sort_priority"],
        reverse=True
    )

    if not ordered_keys:
        # Default wellness maintenance scenario if no modifiable factors are unsatisfied
        reasoning_text = "Selected to support continued cancer prevention. Maintaining high physical activity and a balanced diet is expected to prevent future onset of modifiable metabolic risks."
        if non_modifiable_details:
            reasoning_text += f" Note: Your non-modifiable factors ({', '.join(non_modifiable_details)}) establish a baseline risk and therefore cannot be modified through behavioural intervention."
        return [
            Scenario(
                scenario_id="S_MAINTAIN",
                change="Maintain current healthy lifestyle and high physical activity",
                expected_effect="medium",
                reasoning=reasoning_text
            )
        ]

    # Detect active interactions
    from tools.interaction import detect_interactions
    dummy_factors = [
        RiskFactor(factor="Tobacco Smoke Exposure", evidence_strength="high", evidence_score=0.9, source_count=1),
        RiskFactor(factor="Environmental Carcinogen Exposure", evidence_strength="high", evidence_score=0.9, source_count=1),
        RiskFactor(factor="Alcohol Consumption Risk", evidence_strength="high", evidence_score=0.9, source_count=1),
        RiskFactor(factor="Genetic/Familial Predisposition", evidence_strength="high", evidence_score=0.9, source_count=1),
        RiskFactor(factor="Obesity-related Cancer Risk", evidence_strength="high", evidence_score=0.9, source_count=1),
        RiskFactor(factor="Physical Inactivity", evidence_strength="high", evidence_score=0.9, source_count=1),
        RiskFactor(factor="Poor Dietary Pattern", evidence_strength="high", evidence_score=0.9, source_count=1),
    ]
    interactions = detect_interactions(profile, dummy_factors)
    key_to_factor = {
        "smoking": "Tobacco Smoke Exposure",
        "bmi": "Obesity-related Cancer Risk",
        "alcohol": "Alcohol Consumption Risk",
        "diet": "Poor Dietary Pattern",
        "activity": "Physical Inactivity",
        "uv": "UV/Sun Exposure"
    }

    scenarios = []
    for idx, key in enumerate(ordered_keys):
        factor_info = modifiable_unsatisfied[key]
        pct_val = factor_info["attribution_percentage"]
        
        # Determine selection reason
        if key == "smoking":
            selection_reason = f"Selected because you are an active smoker (smoking status: {profile.smoking_status}, {profile.smoking_years} years)."
        elif key == "bmi":
            selection_reason = f"Selected because you have an elevated BMI of {profile.bmi}."
        elif key == "alcohol":
            selection_reason = f"Selected because you have {profile.alcohol_use.lower()} alcohol use."
        elif key == "diet":
            selection_reason = f"Selected because your diet quality is assessed as {profile.diet_quality.lower()}."
        elif key == "activity":
            selection_reason = f"Selected because your physical activity frequency is {profile.physical_activity.lower()}."
        elif key == "uv":
            selection_reason = f"Selected because you have {profile.sun_exposure.lower()} sun exposure."
        else:
            selection_reason = "Selected as a modifiable lifestyle change."
            
        # Determine prioritization reason
        matched_inters = [inter for inter in interactions if key_to_factor.get(key) in inter.participating_factors]
        is_high_synergy = any(inter.strength == "high" for inter in matched_inters)

        if is_high_synergy and key == "smoking":
            prioritization = "Smoking cessation is the highest-priority intervention because it disrupts one of the strongest interaction pathways currently driving this patient's lung cancer risk."
        elif idx == 0:
            prioritization = "This intervention is prioritized as your highest-ranked modifiable risk contributor."
        else:
            higher_factors = [modifiable_unsatisfied[k]["factor_name"] for k in ordered_keys[:idx]]
            prioritization = f"This intervention is prioritized below {', '.join(higher_factors)} because those represent larger modifiable risk drivers in your profile."

        # Fetch evidence quality details
        evidence_pkg = evidence
        matched_quals = []
        if evidence_pkg:
            factor_words = [w.lower() for w in factor_info["factor_name"].split() if len(w) > 3]
            for c in evidence_pkg.citations:
                cit_text = f"{c.title} {c.source}".lower()
                if any(w in cit_text for w in factor_words) or (("tobacco" in factor_words or "smoke" in factor_words) and "tobacco" in cit_text):
                    if c.evidence_quality:
                        matched_quals.append(c.evidence_quality)

        evidence_types = []
        if any("Guideline" in q for q in matched_quals):
            evidence_types.append("multiple international clinical guidelines")
        if any("Review" in q or "Meta" in q for q in matched_quals):
            evidence_types.append("high-quality systematic reviews")
        if any("Randomized" in q for q in matched_quals):
            evidence_types.append("randomized controlled trials")
        if any("Cohort" in q for q in matched_quals):
            evidence_types.append("extensive epidemiological evidence from prospective cohort studies")

        if not evidence_types and matched_quals:
            evidence_types.append(f"{matched_quals[0].lower()} studies")
        if not evidence_types:
            if key == "smoking":
                evidence_types.append("multiple international clinical guidelines and extensive epidemiological evidence")
            else:
                evidence_types.append("epidemiological studies")

        evidence_str = " and ".join(evidence_types[:2])
        prioritization += f" Supported by {evidence_str}."

        for template_scenario in factor_info["scenarios"]:
            # Determine risk reduction explanation
            if template_scenario.scenario_id == "S_SMOKE_STOP":
                effect_reason = "Stopping tobacco use halts the inhalation of carcinogens, allowing lung tissues to heal and stopping mutagenic accumulation."
            elif template_scenario.scenario_id == "S_SMOKE_HALF":
                effect_reason = "Reducing tobacco use decreases the carcinogen exposure dose but does not eliminate the risk entirely."
            elif template_scenario.scenario_id == "S_WEIGHT_LOSS":
                effect_reason = "Achieving a healthy weight reduces chronic adipose-tissue inflammation, which is a known tumor promoter."
            elif template_scenario.scenario_id == "S_ALCOHOL_STOP":
                effect_reason = "Eliminates exposure to acetaldehyde, a primary metabolite and Group 1 carcinogen."
            elif template_scenario.scenario_id == "S_ALCOHOL_LIMIT":
                effect_reason = "Significantly reduces exposure dose to acetaldehyde, lowering risk towards baseline."
            elif template_scenario.scenario_id == "S_DIET":
                effect_reason = "Adopting a balanced diet supports the gut microbiome and minimizes colorectal exposure to dietary mutagens and processed carcinogens."
            elif template_scenario.scenario_id == "S_FITNESS":
                effect_reason = "Increasing physical activity enhances immune surveillance, reduces systemic inflammation, and regulates metabolic function."
            elif template_scenario.scenario_id == "S_SUN_PROTECT":
                effect_reason = "Daily SPF and physical covers shield skin cells from damaging ultraviolet radiation, reducing skin cancer risks."
            elif template_scenario.scenario_id == "S_SUN_LIMIT":
                effect_reason = "Limits the intensity of peak UV exposure, although off-peak damage accumulation remains possible."
            else:
                effect_reason = template_scenario.reasoning

            # Enrich change title to indicate attribution reduction impact
            change_title = template_scenario.change
            # Add addresses ~X% of attributed risk in parentheses
            if "cessation" in change_title.lower() or "stop" in change_title.lower() or "achieve" in change_title.lower() or "adopt" in change_title.lower() or "increase" in change_title.lower() or "apply" in change_title.lower():
                change_title = f"{change_title} (addresses ~{pct_val:.0f}% of attributed risk)"
            elif "reduce" in change_title.lower() or "limit" in change_title.lower():
                # Partial reduction addresses half the risk
                change_title = f"{change_title} (addresses ~{pct_val/2:.0f}% of attributed risk)"

            reasoning = f"{selection_reason} {effect_reason} {prioritization}"
            if non_modifiable_details:
                reasoning += f" Note: Your non-modifiable factors ({', '.join(non_modifiable_details)}) establish a baseline risk and therefore cannot be modified through behavioural intervention."

            scenarios.append(
                Scenario(
                    scenario_id=template_scenario.scenario_id,
                    change=change_title,
                    expected_effect=template_scenario.expected_effect,
                    reasoning=reasoning
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

