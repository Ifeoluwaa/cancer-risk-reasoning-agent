from typing import List
from schemas.contracts import PatientProfile, EvidencePackage, FollowUpQuestion


def generate_followup_questions(
    profile: PatientProfile, evidence: EvidencePackage, uncertainties: List[str]
) -> List[FollowUpQuestion]:
    """Generates patient-specific, prioritized follow-up questions to refine reasoning.

    Args:
        profile: The PatientProfile containing patient demographics and history.
        evidence: The EvidencePackage containing identified risk factors.
        uncertainties: The list of skeptic uncertainties.

    Returns:
        A list of FollowUpQuestion Pydantic models.
    """
    questions = []

    # Check active profiles and generate appropriate questions
    is_smoking = profile.smoking_status.lower() in ["active", "former"] or profile.smoking_years > 0
    is_family_history = profile.family_history
    has_brca = any("brca" in m.lower() for m in profile.known_mutations)
    is_obese = profile.bmi >= 30.0
    is_alcohol = profile.alcohol_use.lower() in ["moderate", "heavy"]
    has_environmental = len(profile.environmental_exposure) > 0

    # 1. Smoking profile questions
    if is_smoking:
        questions.append(
            FollowUpQuestion(
                question="How many cigarettes do you smoke per day?",
                rationale="This information substantially improves estimation of cumulative tobacco exposure and strengthens causal reasoning.",
                impact="Significantly improve confidence"
            )
        )
        questions.append(
            FollowUpQuestion(
                question="How many years have you been smoking?",
                rationale="Quantifies cumulative duration of exposure to refine the baseline mutagenic accumulation model.",
                impact="Significantly improve confidence"
            )
        )
        questions.append(
            FollowUpQuestion(
                question="Have you made any quit attempts in the past year?",
                rationale="Assesses behavioral readiness and quit attempt history to refine counterfactual recommendations.",
                impact="Moderately improve confidence"
            )
        )

    # 2. BRCA profile questions
    if has_brca:
        questions.append(
            FollowUpQuestion(
                question="Was your genetic mutation (e.g. BRCA1/BRCA2) clinically confirmed by a certified lab test?",
                rationale="Verifies pathogenicity classification to eliminate variant-of-uncertain-significance confounding.",
                impact="Significantly improve confidence"
            )
        )
        questions.append(
            FollowUpQuestion(
                question="Have you completed genetic counseling to discuss hereditary risk management?",
                rationale="Confirms integration of clinical guidance and psychosocial support for risk-reduction decisions.",
                impact="Moderately improve confidence"
            )
        )

    # 3. Family history profile questions
    if is_family_history:
        questions.append(
            FollowUpQuestion(
                question="Which specific first-degree relatives have been diagnosed with cancer?",
                rationale="Pinpoints genetic lineage inheritance patterns to refine hereditary risk attribution.",
                impact="Significantly improve confidence"
            )
        )
        questions.append(
            FollowUpQuestion(
                question="At what age were your relatives diagnosed with cancer?",
                rationale="Checks for early-onset patterns which strongly indicate high-penetrance germline mutations.",
                impact="Significantly improve confidence"
            )
        )
        questions.append(
            FollowUpQuestion(
                question="What specific types of cancer were diagnosed in your family?",
                rationale="Maps lineage syndromic correlations (e.g. breast-ovarian) to define precise genetic risk.",
                impact="Significantly improve confidence"
            )
        )

    # 4. Obesity profile questions
    if is_obese:
        questions.append(
            FollowUpQuestion(
                question="What is your current weight trend over the past 6 to 12 months?",
                rationale="Identifies active metabolic trajectories and insulin resistance trends.",
                impact="Moderately improve confidence"
            )
        )
        questions.append(
            FollowUpQuestion(
                question="What is your waist circumference?",
                rationale="Distinguishes visceral adiposity from general fat-free mass to improve metabolic risk attribution.",
                impact="Significantly improve confidence"
            )
        )
        questions.append(
            FollowUpQuestion(
                question="What is your typical exercise frequency and intensity?",
                rationale="Helps separate physical inactivity confounding from weight-driven metabolic factors.",
                impact="Moderately improve confidence"
            )
        )

    # 5. Alcohol profile questions
    if is_alcohol:
        questions.append(
            FollowUpQuestion(
                question="What is the frequency of your alcohol consumption and the specific beverage type?",
                rationale="Allows estimating exact daily acetaldehyde exposure to clarify metabolic carcinogen risk.",
                impact="Moderately improve confidence"
            )
        )

    # 6. Environmental profile questions
    if has_environmental:
        questions.append(
            FollowUpQuestion(
                question="What was the duration and precise intensity of your occupational or environmental exposure?",
                rationale="Helps quantify cumulative exposure dose to distinguish occupational hazard from general baseline risk.",
                impact="Significantly improve confidence"
            )
        )

    # Prioritization: sort questions by impact level (Significant first, then Moderate, then Slight)
    impact_order = {
        "Significantly improve confidence": 3,
        "Moderately improve confidence": 2,
        "Slightly improve confidence": 1
    }
    sorted_questions = sorted(questions, key=lambda q: impact_order.get(q.impact, 0), reverse=True)

    # Limit to top 5 questions
    return sorted_questions[:5]
