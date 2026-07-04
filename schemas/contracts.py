"""Data contracts and schemas for the Cancer Risk Reasoning Agent (CRRA).

All communication between agents occurs using these structured Pydantic models.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class PatientProfile(BaseModel):
    """Input demographic, lifestyle, and history details for a patient."""

    session_id: str = Field(..., description="Unique identifier for the session")
    age: int = Field(..., description="Age of the patient in years")
    sex: str = Field(..., description="Sex of the patient")
    bmi: float = Field(..., description="Body Mass Index")
    smoking_status: str = Field(..., description="Smoking history status (e.g. active, former, never)")
    smoking_years: int = Field(..., description="Number of years smoked")
    alcohol_use: str = Field(..., description="Alcohol consumption level (e.g. none, light, moderate, heavy)")
    physical_activity: str = Field(..., description="Physical activity frequency/intensity")
    diet_quality: str = Field(..., description="Dietary quality assessment")
    sun_exposure: str = Field(..., description="Level of UV/sun exposure")
    occupation: str = Field(..., description="Occupation/work environment")
    environmental_exposure: List[str] = Field(
        default_factory=list, description="List of environmental carcinogen exposures"
    )
    family_history: bool = Field(..., description="True if family history of cancer exists")
    known_mutations: List[str] = Field(
        default_factory=list, description="List of confirmed genetic mutations (e.g. BRCA1)"
    )
    previous_cancer_history: bool = Field(..., description="True if patient has a personal history of cancer")


class SecurityPackage(BaseModel):
    """Output of the Security Agent assessing safety status and performing PII redaction."""

    safety_status: Literal["green", "yellow", "red"] = Field(
        ..., description="Overall safety classification of the request"
    )
    prompt_injection_detected: bool = Field(
        ..., description="Whether a prompt injection attempt was detected"
    )
    pii_detected: bool = Field(
        ..., description="Whether personally identifiable information was detected"
    )
    redacted_fields: List[str] = Field(
        default_factory=list, description="Fields that were redacted or modified for privacy"
    )
    medical_request_type: str = Field(
        ..., description="Categorized medical request type (e.g. explanation, risk estimation, diagnosis)"
    )
    clean_profile: PatientProfile = Field(
        ..., description="The sanitized PatientProfile (PII redacted)"
    )


class RiskFactor(BaseModel):
    """Structure representing a single identified risk factor."""

    factor: str = Field(..., description="Name of the risk factor")
    evidence_strength: Literal["high", "medium", "low"] = Field(
        ..., description="Grade of evidence strength supporting this risk factor"
    )
    evidence_score: float = Field(
        ..., description="Numerical score representing the evidence level/relevance"
    )
    source_count: int = Field(..., description="Number of distinct sources corroborating the factor")


class Citation(BaseModel):
    """Structure representing a scientific citation."""

    source: str = Field(..., description="Source journal, database, or publisher")
    title: str = Field(..., description="Title of the publication")
    year: int = Field(..., description="Publication year")
    evidence_quality: Optional[str] = Field(
        None, description="Quality classification level of the evidence (e.g. Clinical Guideline, RCT, etc.)"
    )


class RiskInteraction(BaseModel):
    """Structure representing a clinically meaningful interaction between risk factors."""

    name: str = Field(..., description="Name of the risk interaction")
    participating_factors: List[str] = Field(..., description="Factors involved in the interaction")
    rationale: str = Field(..., description="Clinical rationale of the interaction")
    strength: Literal["high", "medium", "low"] = Field(..., description="Interaction strength")
    evidence_score: float = Field(..., description="Evidence score representing the strength/relevance")
    supporting_evidence: List[str] = Field(..., description="Supporting literature or studies")


class EvidencePackage(BaseModel):
    """Output of the Evidence Agent collecting retrieved sources and ranking risk factors."""

    risk_factors: List[RiskFactor] = Field(
        ..., description="List of identified risk factors matching the profile"
    )
    citations: List[Citation] = Field(
        ..., description="Scientific citations supporting the identified risk factors"
    )
    retrieved_documents: List[str] = Field(
        ..., description="Plain text or names of retrieved reference documents/resources"
    )
    interactions: List[RiskInteraction] = Field(
        default_factory=list,
        description="Clinically meaningful interactions detected between risk factors"
    )


class Contributor(BaseModel):
    """Structure representing a ranked contributor to the cancer risk profile."""

    factor: str = Field(..., description="Name of the contributor/factor")
    rank: int = Field(..., description="Importance rank of the factor (1 is highest)")
    reason: str = Field(..., description="Detailed causal/biological reasoning explanation")
    attribution_percentage: Optional[float] = Field(
        None, description="Estimated relative percentage contribution of this factor to overall risk"
    )
    classification: Optional[str] = Field(
        None, description="Classification based on attribution score (e.g. Primary Driver, Major Contributor, etc.)"
    )
    impact_tier: Optional[str] = Field(
        None, description="Clinically interpretable impact tier (e.g. Very High, High, Moderate, Low, Minimal)"
    )
    impact_bar: Optional[str] = Field(
        None, description="Visual bar representation of the impact"
    )


class CausalityPackage(BaseModel):
    """Output of the Causality Agent evaluating and ranking risk contributors."""

    ranked_contributors: List[Contributor] = Field(
        ..., description="List of contributors ranked by significance to this profile"
    )
    primary_drivers: List[str] = Field(
        ..., description="Top drivers identified as primary risk factors"
    )
    causal_confidence: Literal["high", "medium", "low"] = Field(
        ..., description="Confidence level in the established causal links"
    )


class Scenario(BaseModel):
    """Structure representing a hypothetical change scenario."""

    scenario_id: str = Field(..., description="Unique ID for this scenario")
    change: str = Field(..., description="Hypothetical change in lifestyle or exposure")
    expected_effect: Literal["high", "medium", "low"] = Field(
        ..., description="Expected impact on risk contributor magnitude"
    )
    reasoning: str = Field(..., description="Logical explanation of the expected change outcome")


class Comparison(BaseModel):
    """Structure representing a relative comparison between scenarios."""

    scenario_a: str = Field(..., description="ID of Scenario A")
    scenario_b: str = Field(..., description="ID of Scenario B")
    higher_impact: str = Field(..., description="Explanation of which scenario has a higher relative impact")


class CounterfactualPackage(BaseModel):
    """Output of the Counterfactual Agent proposing hypothetical scenarios and comparing impacts."""

    scenarios: List[Scenario] = Field(
        ..., description="List of generated counterfactual scenarios"
    )
    comparisons: List[Comparison] = Field(
        ..., description="Pairwise comparisons showing relative impact of scenarios"
    )


class ConflictingEvidence(BaseModel):
    """Structure representing conflicting evidence or alternative findings in literature."""

    factor: str = Field(..., description="The risk factor for which conflict exists")
    evidence: str = Field(..., description="Brief details of the contradictory/uncertain findings")
    source: str = Field(..., description="Source of the conflicting evidence")


class FollowUpQuestion(BaseModel):
    """Structure representing a targeted follow-up question to improve reasoning quality."""

    question: str = Field(..., description="The targeted follow-up question")
    rationale: str = Field(..., description="Clinician rationale explanation of why this information matters")
    impact: str = Field(..., description="Expected qualitative impact on reasoning confidence (e.g. Slightly/Moderately/Significantly improve confidence)")


class SkepticPackage(BaseModel):
    """Output of the Skeptic Agent critiquing conclusions, identifying limits and uncertainties."""

    confidence: Literal["high", "medium", "low"] = Field(
        ..., description="Skeptic's adjusted overall confidence score"
    )
    uncertainties: List[str] = Field(
        ..., description="Specific uncertainties identified in reasoning/data"
    )
    limitations: List[str] = Field(
        ..., description="Explicit scientific limitations of current knowledge on this risk profile"
    )
    conflicting_evidence: List[ConflictingEvidence] = Field(
        ..., description="Any literature or evidence conflicting with the Evidence/Causality findings"
    )
    missing_information: List[str] = Field(
        ..., description="Required profile details that are missing but could improve accuracy"
    )
    recommended_questions: Optional[List[FollowUpQuestion]] = Field(
        default_factory=list, description="Recommended clinical follow-up questions"
    )


class AggregatedAnalysis(BaseModel):
    """Accumulation of all agent packages compiled by the Orchestrator."""

    patient_profile: PatientProfile = Field(
        ..., description="The patient's initial or cleaned profile information"
    )
    evidence_package: EvidencePackage = Field(
        ..., description="Evidence package output by the Evidence Agent"
    )
    causality_package: CausalityPackage = Field(
        ..., description="Causality analysis package output by the Causality Agent"
    )
    counterfactual_package: CounterfactualPackage = Field(
        ..., description="Counterfactual scenarios package output by the Counterfactual Agent"
    )
    skeptic_package: SkepticPackage = Field(
        ..., description="Critical evaluation package output by the Skeptic Agent"
    )


class FinalReport(BaseModel):
    """Output of the Synthesis Agent presenting the final, user-facing report."""

    top_contributors: List[str] = Field(
        ..., description="Names of top factors contributing to future cancer risk"
    )
    evidence_summary: str = Field(
        ..., description="Clear explanation of the evidence supporting these factors"
    )
    counterfactual_summary: str = Field(
        ..., description="Summary of how lifestyle or profile changes could affect the contributors"
    )
    limitations: List[str] = Field(
        ..., description="Statement of limitations and uncertainties identified by the Skeptic"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ..., description="Overall confidence level in the generated findings"
    )
    citations: List[Citation] = Field(
        ..., description="Scientific references for the findings presented in the report"
    )
    safety_disclaimer: str = Field(
        ..., description="Required medical disclaimer stating that this is not medical advice"
    )


class WorkflowState(BaseModel):
    """The state container tracking workflow execution, progress, and accumulated inputs/outputs."""

    session_id: str = Field(..., description="The unique session identifier")
    patient_profile: Optional[PatientProfile] = Field(
        None, description="The original or sanitized patient profile input"
    )
    security_package: Optional[SecurityPackage] = Field(
        None, description="Security checks output"
    )
    evidence_package: Optional[EvidencePackage] = Field(
        None, description="Retrieved and ranked evidence package"
    )
    causality_package: Optional[CausalityPackage] = Field(
        None, description="Causal drivers ranking package"
    )
    counterfactual_package: Optional[CounterfactualPackage] = Field(
        None, description="Counterfactual/what-if scenarios package"
    )
    skeptic_package: Optional[SkepticPackage] = Field(
        None, description="Critique and uncertainty analysis package"
    )
    aggregated_analysis: Optional[AggregatedAnalysis] = Field(
        None, description="Fully compiled analysis aggregating all steps"
    )
    final_report: Optional[FinalReport] = Field(
        None, description="The final synthesized user-facing report"
    )
    current_step: str = Field(
        "START", description="Name of the current step or agent node in execution"
    )
    status: str = Field(
        "PENDING", description="Current overall status of the execution (e.g. PENDING, RUNNING, COMPLETED, FAILED)"
    )
    errors: List[str] = Field(
        default_factory=list, description="Any execution errors logged during the workflow"
    )
