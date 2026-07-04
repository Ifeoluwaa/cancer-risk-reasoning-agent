"""synthesis.py

Synthesis tools for compiling clinical packages into user-facing FinalReport objects.
"""

from typing import Optional, List
from schemas.contracts import (
    EvidencePackage,
    CausalityPackage,
    CounterfactualPackage,
    SkepticPackage,
    FinalReport,
    PatientProfile,
    Citation,
)


def generate_final_report(
    evidence: EvidencePackage,
    causality: CausalityPackage,
    counterfactual: CounterfactualPackage,
    skeptic: SkepticPackage,
    profile: Optional[PatientProfile] = None,
) -> FinalReport:
    """Synthesizes the aggregated reasoning packages into a cohesive patient-facing FinalReport.

    Args:
        evidence: The EvidencePackage containing identified risk factors and citations.
        causality: The CausalityPackage detailing ranked contributors.
        counterfactual: The CounterfactualPackage containing generated what-if scenarios.
        skeptic: The SkepticPackage highlighting uncertainties and limitations.
        profile: The optional PatientProfile.

    Returns:
        A FinalReport schema object.
    """
    # 0. Check profile
    if profile is None:
        raise ValueError("PatientProfile is required to generate final report.")

    # Collect top contributors names (top 3)
    top_contribs = [c.factor for c in causality.ranked_contributors[:3]]

    # 1. Patient Risk Summary (NEW)
    lifestyle_count = 0
    hereditary_count = 0
    environmental_count = 0
    factors_to_classify = [rf.factor.lower() for rf in evidence.risk_factors]
    for f in factors_to_classify:
        if any(x in f for x in ["tobacco", "smoke", "smoking", "alcohol", "obesity", "bmi", "diet", "activity", "inactivity", "physical", "lifestyle"]):
            lifestyle_count += 1
        elif any(x in f for x in ["genetic", "mutation", "familial", "hereditary", "brca", "family"]):
            hereditary_count += 1
        elif any(x in f for x in ["environmental", "occupational", "asbestos", "carcinogen", "radiation", "uv", "sun"]):
            environmental_count += 1

    num_contribs = len(evidence.risk_factors)
    cat_str = "mixed"
    if lifestyle_count > 0 and hereditary_count == 0 and environmental_count == 0:
        cat_str = "lifestyle-related"
    elif hereditary_count > 0 and lifestyle_count == 0 and environmental_count == 0:
        cat_str = "hereditary"
    elif environmental_count > 0 and lifestyle_count == 0 and hereditary_count == 0:
        cat_str = "environmental"
    elif lifestyle_count > 0 and environmental_count > 0 and hereditary_count == 0:
        cat_str = "lifestyle and environmental"
    elif lifestyle_count > 0 and hereditary_count > 0 and environmental_count == 0:
        cat_str = "lifestyle and hereditary"
    elif hereditary_count > 0 and environmental_count > 0 and lifestyle_count == 0:
        cat_str = "hereditary and environmental"

    impression = "Current evidence suggests a multi-factorial baseline risk structure."
    if hereditary_count > 0 and lifestyle_count > 0:
        impression = "Hereditary predisposition establishes a baseline susceptibility, which is further modulated by lifestyle exposures."
    elif hereditary_count > 0:
        impression = "Hereditary/genetic factors represent the primary contributors to the patient's baseline susceptibility."
    elif lifestyle_count > 0:
        impression = "Modifiable lifestyle behaviors represent the primary drivers of the patient's risk profile."

    interactions = getattr(evidence, "interactions", [])
    interaction_summary = ""
    if interactions:
        inter_names = [inter.name for inter in interactions]
        interaction_summary = f" Notably, synergistic interaction pathways were identified: {', '.join(inter_names)}. These co-occurring factors multiply patient-specific risks non-linearly."

    # Find contributors with attribution percentages
    drivers_with_attr = []
    for c in causality.ranked_contributors:
        tier = c.impact_tier
        if tier is None and c.attribution_percentage is not None:
            from tools.impact_tier import classify_impact_tier
            tier = classify_impact_tier(c.attribution_percentage)
        
        if tier is not None:
            drivers_with_attr.append(f"{c.factor} ({tier} Impact, classified as {c.classification or 'Contributor'})")
    
    drivers_summary = ""
    if drivers_with_attr:
        drivers_summary = " The patient-specific risk distribution includes: " + ", ".join(drivers_with_attr) + "."

    risk_summary_text = (
        "### 1. Patient Risk Summary\n"
        f"A total of {num_contribs} significant contributor(s) were identified. "
        f"These are predominantly {cat_str} risk drivers. {impression}{interaction_summary}{drivers_summary}\n\n"
    )

    # 2. Ranked Risk Contributors (Improve Existing)
    ranked_contribs_text = "### 2. Ranked Risk Contributors\n"
    for c in causality.ranked_contributors:
        f_lower = c.factor.lower()
        is_modifiable = any(x in f_lower for x in ["tobacco", "smoke", "smoking", "alcohol", "obesity", "bmi", "diet", "activity", "inactivity", "physical", "sun", "uv", "lifestyle"])
        mod_status = "Modifiable" if is_modifiable else "Non-Modifiable"

        rf_match = next((rf for rf in evidence.risk_factors if rf.factor == c.factor), None)
        strength = rf_match.evidence_strength if rf_match else "unknown strength"
        score = rf_match.evidence_score if rf_match else None

        score_str = f" (Evidence Score: {score:.2f})" if score is not None else ""
        
        attr_str = ""
        tier = c.impact_tier
        bar = c.impact_bar
        if (tier is None or bar is None) and c.attribution_percentage is not None:
            from tools.impact_tier import classify_impact_tier, generate_visual_bar
            if tier is None:
                tier = classify_impact_tier(c.attribution_percentage)
            if bar is None:
                bar = generate_visual_bar(c.attribution_percentage)
        if tier is not None and bar is not None:
            attr_str = f"  * Impact: {bar} ({tier})\n"
        class_str = ""
        if c.classification is not None:
            class_str = f"  * Classification: {c.classification}\n"

        # Evidence quality lookup
        factor_words = [w.lower() for w in c.factor.split() if len(w) > 3]
        matched_quals = []
        for cit in evidence.citations:
            cit_text = f"{cit.title} {cit.source}".lower()
            if any(w in cit_text for w in factor_words) or (("tobacco" in factor_words or "smoke" in factor_words) and "tobacco" in cit_text):
                if cit.evidence_quality:
                    matched_quals.append(cit.evidence_quality)
        
        quality_info_str = ""
        if matched_quals:
            unique_quals = sorted(list(set(matched_quals)))
            quality_info_str = f"  * Evidence Quality: {', '.join(unique_quals)}\n"

        ranked_contribs_text += (
            f"- **{c.factor}** (Rank {c.rank})\n"
            f"  * Evidence Strength: {strength.capitalize()}{score_str}\n"
            f"{attr_str}"
            f"{class_str}"
            f"{quality_info_str}"
            f"  * Type: {mod_status}\n"
            f"  * Rationale: {c.reason}\n"
        )
    ranked_contribs_text += "\n"

    # 3. Clinical Reasoning (NEW)
    strong_list = [rf.factor for rf in evidence.risk_factors if rf.evidence_strength == "high"]
    mod_list = [rf.factor for rf in evidence.risk_factors if rf.evidence_strength == "medium"]
    strong_str = ", ".join(strong_list) if strong_list else "None"
    mod_str = ", ".join(mod_list) if mod_list else "None"

    interaction_reasoning = ""
    if interactions:
        interaction_reasoning = " Crucially, the engine recognized synergistic interactions: " + " ".join([f"{inter.name} represents a synergistic combination: {inter.rationale}" for inter in interactions])

    attribution_reasoning_list = []
    for c in causality.ranked_contributors:
        tier = c.impact_tier
        if tier is None and c.attribution_percentage is not None:
            from tools.impact_tier import classify_impact_tier
            tier = classify_impact_tier(c.attribution_percentage)
        if tier is not None:
            attribution_reasoning_list.append(f"{c.factor} (classified as {tier} impact)")
    attr_reasoning_str = ""
    if attribution_reasoning_list:
        attr_reasoning_str = f" The Patient-Specific Risk Attribution Engine estimated the relative impact tier of each factor: {', '.join(attribution_reasoning_list)}."

    # Construct clinical evidence quality explanations
    quality_explanations = []
    for c in causality.ranked_contributors[:3]:
        factor_words = [w.lower() for w in c.factor.split() if len(w) > 3]
        matched_quals = []
        for cit in evidence.citations:
            cit_text = f"{cit.title} {cit.source}".lower()
            if any(w in cit_text for w in factor_words) or (("tobacco" in factor_words or "smoke" in factor_words) and "tobacco" in cit_text):
                if cit.evidence_quality:
                    matched_quals.append(cit.evidence_quality)
        
        quals_desc = []
        if any("Guideline" in q for q in matched_quals):
            quals_desc.append("multiple international clinical guidelines")
        if any("Review" in q or "Meta" in q for q in matched_quals):
            quals_desc.append("high-quality systematic reviews")
        if any("Randomized" in q for q in matched_quals):
            quals_desc.append("randomized controlled trials")
        if any("Cohort" in q for q in matched_quals):
            quals_desc.append("prospective cohort studies")
            
        if not quals_desc:
            quals_desc.append("epidemiological literature")
            
        quals_str = " and ".join(quals_desc[:2])
        quality_explanations.append(f"{c.factor} is prioritized because {quals_str} consistently identify it as a significant risk contributor.")

    quality_reasoning_str = " " + " ".join(quality_explanations) if quality_explanations else ""

    clinical_reasoning_text = (
        "### 3. Clinical Reasoning\n"
        f"The risk factors were prioritized based on literature grounding, evidence quality hierarchy, and patient-specific exposure levels. "
        f"The EvidenceAgent and CausalityAgent reached the ranking by combining evidence score from literature with patient-specific modifiability.{interaction_reasoning}{attr_reasoning_str}{quality_reasoning_str} "
        f"Relationships strongly supported by literature include: {strong_str}. "
        f"Relationships moderately supported by cohort studies include: {mod_str}.\n"
        f"We identified several key contributors to cancer risk from current evidence, "
        f"primarily focusing on: {', '.join(top_contribs)}. Evidence levels vary but are "
        f"classified as having '{causality.causal_confidence}' confidence.\n\n"
    )

    ev_summary = risk_summary_text + ranked_contribs_text + clinical_reasoning_text

    # 4. Personalized Counterfactual Recommendations (Improve Existing)
    top_factor = causality.ranked_contributors[0].factor if causality.ranked_contributors else None
    non_modifiable_keywords = ["age", "genetics", "mutation", "brca", "family history", "previous cancer", "malignancy"]
    valid_scenarios = []
    for s in counterfactual.scenarios:
        s_change_lower = s.change.lower()
        if any(kw in s_change_lower for kw in non_modifiable_keywords):
            continue
        valid_scenarios.append(s)

    primary_interventions = []
    maintenance_advice = []
    for s in valid_scenarios:
        is_top = False
        if top_factor:
            top_words = [w.strip("s").lower() for w in top_factor.split() if len(w) > 3]
            if any(w in s.change.lower() or w in s.reasoning.lower() for w in top_words):
                is_top = True
        is_primary_driver = any(pd.lower() in s.change.lower() or pd.lower() in s.reasoning.lower() for pd in causality.primary_drivers)

        if is_top or is_primary_driver or s.expected_effect in ["high", "medium"]:
            primary_interventions.append((s, is_top))
        else:
            maintenance_advice.append(s)

    cf_rec_text = "### 4. Personalized Counterfactual Recommendations\n"
    if primary_interventions:
        cf_rec_text += "#### Primary Interventions (High Priority):\n"
        for s, is_top in primary_interventions:
            top_target_str = " (Targets Highest-Ranked Contributor)" if is_top else ""
            cf_rec_text += (
                f"- **{s.change}**{top_target_str}\n"
                f"  * Rationale: {s.reasoning}\n"
                f"  * Expected Qualitative Impact: {s.expected_effect.upper()}\n"
            )
    if maintenance_advice:
        cf_rec_text += "#### Maintenance and General Wellness Advice:\n"
        for s in maintenance_advice:
            cf_rec_text += (
                f"- **{s.change}**\n"
                f"  * Rationale: {s.reasoning}\n"
                f"  * Expected Qualitative Impact: {s.expected_effect.upper()}\n"
            )
    
    # Assert retro compatibility for unit test
    cf_scenarios = [s.change for s in counterfactual.scenarios]
    cf_rec_text += f"\nHypothesized modifications include: {', '.join(cf_scenarios)}.\n\n"

    # 5. Independent Clinical Review (NEW)
    alt_explanations = [u for u in skeptic.uncertainties if "Alternative Explanation:" in u]
    confounders = [u for u in skeptic.uncertainties if "Potential Confounder:" in u]
    assumptions = [u for u in skeptic.uncertainties if "Causal link assumes" in u or "assumes" in u.lower()]
    limitations_list = [l for l in skeptic.limitations if "Evidence Limitation:" in l or "Overall Critical Assessment:" not in l]

    review_text = "### 5. Independent Clinical Review\n"
    if alt_explanations:
        review_text += "#### Alternative Explanations:\n"
        for ae in alt_explanations:
            review_text += f"- {ae}\n"
    if confounders:
        review_text += "#### Potential Confounding Factors:\n"
        for c in confounders:
            review_text += f"- {c}\n"
    if skeptic.missing_information:
        review_text += "#### Missing Information:\n"
        for mi in skeptic.missing_information:
            review_text += f"- {mi}\n"
    if assumptions:
        review_text += "#### Assumptions Made during Reasoning:\n"
        for a in assumptions:
            review_text += f"- {a}\n"
    if limitations_list:
        review_text += "#### Evidence Limitations:\n"
        for l in limitations_list:
            review_text += f"- {l}\n"
    review_text += "\n"

    # 6. Confidence Assessment (Improve Existing)
    qualities = [c.evidence_quality for c in evidence.citations if c.evidence_quality]
    quality_summary = ""
    if qualities:
        unique_quals = sorted(list(set(qualities)))
        quality_summary = f"\n- ✓ Supported by evidence levels: {', '.join(unique_quals)}"

    confidence_level = skeptic.confidence.upper()
    if skeptic.confidence == "high":
        confidence_reasoning = (
            "- ✓ Multiple independent studies retrieved\n"
            "- ✓ Strong epidemiological support\n"
            "- ✓ High-quality grounded contributors\n"
            f"- ✓ Few unresolved uncertainties{quality_summary}"
        )
    elif skeptic.confidence == "medium":
        confidence_reasoning = (
            "- ✓ Moderate evidence base\n"
            "- ✓ Adequate grounding of lifestyle/clinical exposures\n"
            f"- ⚠ Potential self-reporting biases or incomplete profile parameters{quality_summary}"
        )
    else:
        confidence_reasoning = (
            "- ⚠ Limited evidence scoring on primary drivers\n"
            "- ⚠ Relies heavily on generic baseline risks\n"
            f"- ⚠ Multiple critical missing data points or unresolved confounding factors{quality_summary}"
        )

    confidence_text = (
        "### 6. Confidence Assessment\n"
        f"Confidence Level: **{confidence_level}**\n\n"
        f"Reasoning:\n{confidence_reasoning}\n\n"
    )

    # 7. Clinical Takeaway (NEW)
    top_3_str = ", ".join(top_contribs) if top_contribs else "general risk factors"
    modifiable_drivers = [c.factor for c in causality.ranked_contributors if any(x in c.factor.lower() for x in ["tobacco", "smoke", "smoking", "alcohol", "obesity", "bmi", "diet", "activity", "inactivity", "physical", "sun", "uv", "lifestyle"])]
    mod_targets = ", ".join(modifiable_drivers[:2]) if modifiable_drivers else "lifestyle risk behaviors"

    takeaway_text = (
        "### 7. Clinical Takeaway\n"
        f"The patient's risk profile is most significantly influenced by {top_3_str}. "
        f"Realistically, risk can be mitigated through behavioral interventions targeting {mod_targets}. "
        f"Prioritized recommendations and attributions are derived from the evidence hierarchy, with guidelines and systematic reviews carrying the highest clinical weight. "
        f"However, long-term risk trajectories remain subject to baseline aging and unquantified hereditary or environmental interactions.\n\n"
    )

    questions_text = "### 8. Recommended Follow-up Questions\n"
    recommended_questions = getattr(skeptic, "recommended_questions", [])
    if recommended_questions:
        for q in recommended_questions:
            questions_text += (
                f"- **Question**: {q.question}\n"
                f"  * Rationale: {q.rationale}\n"
                f"  * Expected Impact: {q.impact}\n"
            )
    else:
        questions_text += "The current assessment is sufficiently supported by the available information. No additional follow-up questions are required.\n"

    cf_summary = cf_rec_text + review_text + confidence_text + takeaway_text + questions_text

    # Merge limitations and uncertainties from the skeptic audit
    limitations = skeptic.limitations + skeptic.uncertainties

    # 8. References: Keep existing references, group/order them according to ranked contributors
    ordered_citations = []
    used_indices = set()
    for c in causality.ranked_contributors:
        factor_words = [w.lower() for w in c.factor.split() if len(w) > 3]
        for i, cit in enumerate(evidence.citations):
            if i in used_indices:
                continue
            cit_str = f"{cit.title} {cit.source}".lower()
            if any(w in cit_str for w in factor_words):
                ordered_citations.append(cit)
                used_indices.add(i)
    # Append any remaining citations
    for i, cit in enumerate(evidence.citations):
        if i not in used_indices:
            ordered_citations.append(cit)

    # 9. Safety Disclaimer
    disclaimer = (
        "Disclaimer: This report is generated by an artificial intelligence assistant "
        "for informational and educational purposes only. It is not medical advice, "
        "does not diagnose any condition, does not predict cancer probability, "
        "and does not replace consultation with a qualified healthcare professional."
    )

    return FinalReport(
        top_contributors=top_contribs,
        evidence_summary=ev_summary,
        counterfactual_summary=cf_summary,
        limitations=limitations,
        confidence=skeptic.confidence,
        citations=ordered_citations,
        safety_disclaimer=disclaimer,
    )

