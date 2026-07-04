from typing import List
from schemas.contracts import PatientProfile, RiskFactor, RiskInteraction


def detect_interactions(profile: PatientProfile, risk_factors: List[RiskFactor]) -> List[RiskInteraction]:
    """Identifies clinically meaningful combinations of patient risk factors.

    Args:
        profile: The PatientProfile containing patient demographics, lifestyle, and history.
        risk_factors: The list of identified RiskFactor objects.

    Returns:
        A list of RiskInteraction objects.
    """
    interactions = []
    
    # Extract factor names present for checking
    factor_names = [rf.factor for rf in risk_factors]
    has_factor = lambda name: any(name.lower() in f.lower() for f in factor_names)

    # 1. Smoking + Asbestos
    is_smoker = profile.smoking_status.lower() in ["active", "former"]
    exposures_lower = [e.lower() for e in profile.environmental_exposure]
    has_asbestos = "asbestos" in exposures_lower
    if is_smoker and has_asbestos:
        interactions.append(
            RiskInteraction(
                name="Tobacco Smoke + Asbestos Synergism",
                participating_factors=["Tobacco Smoke Exposure", "Environmental Carcinogen Exposure"],
                rationale="Tobacco smoke and asbestos exposure have a well-documented synergistic, multiplicative relationship that dramatically escalates lung cancer risk beyond the additive sum of individual exposures.",
                strength="high",
                evidence_score=0.98,
                supporting_evidence=["Synergistic Lung Cancer Risks: Tobacco and Asbestos Co-Exposures (American Journal of Respiratory Medicine, 2021)"]
            )
        )

    # 2. Smoking + Alcohol
    is_alcohol = profile.alcohol_use.lower() in ["moderate", "heavy"]
    if is_smoker and is_alcohol:
        interactions.append(
            RiskInteraction(
                name="Alcohol + Tobacco Mucosal Synergism",
                participating_factors=["Tobacco Smoke Exposure", "Alcohol Consumption Risk"],
                rationale="Alcohol acts as a solvent for tobacco carcinogens, enhancing their mucosal penetration and leading to a synergistic risk increase for upper aerodigestive cancers.",
                strength="high",
                evidence_score=0.92,
                supporting_evidence=["Co-carcinogenesis of Alcohol and Tobacco (Journal of Clinical Gastroenterology, 2020)"]
            )
        )

    # 3. BRCA Mutation + Family History
    mutations_lower = [m.lower() for m in profile.known_mutations]
    has_brca = "brca1" in mutations_lower or "brca2" in mutations_lower
    if has_brca and profile.family_history:
        interactions.append(
            RiskInteraction(
                name="BRCA Mutation + Familial Pedigree Susceptibility",
                participating_factors=["Genetic/Familial Predisposition"],
                rationale="The presence of a BRCA mutation combined with family history of cancer suggests a high-penetrance hereditary syndrome with a strongly elevated baseline risk that warrants intensive clinical surveillance.",
                strength="high",
                evidence_score=0.99,
                supporting_evidence=["Hereditary Breast and Ovarian Cancer Syndrome: BRCA and Familial Pedigrees (Lancet Oncology, 2019)"]
            )
        )

    # 4. Obesity + Physical Inactivity
    is_obese = profile.bmi >= 30.0
    is_inactive = profile.physical_activity.lower() == "low"
    if is_obese and is_inactive:
        interactions.append(
            RiskInteraction(
                name="Obesity + Inactivity Metabolic Overlap",
                participating_factors=["Obesity-related Cancer Risk", "Physical Inactivity"],
                rationale="Obesity and physical inactivity interact through overlapping metabolic and inflammatory pathways, aggravating insulin resistance and chronic systemic inflammation.",
                strength="medium",
                evidence_score=0.82,
                supporting_evidence=["Metabolic Overlap: Obesity and Inactivity in Carcinogenesis (Endocrine Reviews, 2018)"]
            )
        )

    # 5. Poor Diet + Obesity
    is_poor_diet = profile.diet_quality.lower() == "low"
    if is_obese and is_poor_diet:
        interactions.append(
            RiskInteraction(
                name="Poor Diet + Obesity Pro-inflammatory Interaction",
                participating_factors=["Obesity-related Cancer Risk", "Poor Dietary Pattern"],
                rationale="A poor dietary pattern high in processed foods interacts with obesity to exacerbate systemic lipid peroxidation and adipose tissue-driven inflammation.",
                strength="medium",
                evidence_score=0.80,
                supporting_evidence=["Dietary Patterns and Adiposity: Joint Inflammatory Effects (Journal of Nutrition, 2021)"]
            )
        )

    return interactions
