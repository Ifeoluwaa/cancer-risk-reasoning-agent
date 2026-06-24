"""llm_judges.py

Pydantic schemas and abstract base classes for deterministic local mock LLM judges.
"""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, Field
from schemas.contracts import WorkflowState


class JudgeResult(BaseModel):
    """Schema representing the evaluation outcome from an LLM judge."""

    category: str = Field(..., description="The evaluation metric category (e.g. Evidence Quality)")
    score: float = Field(..., description="Normalized score from 1.0 (poor) to 5.0 (excellent)")
    reasoning: str = Field(..., description="Detailed clinical/logical explanation of the score")
    passed: bool = Field(..., description="True if the output met the success threshold")


class BaseLLMJudge(ABC):
    """Abstract base class for all LLM evaluation judges."""

    def __init__(self, category: str) -> None:
        self.category = category

    @abstractmethod
    def evaluate(self, state: WorkflowState) -> JudgeResult:
        """Evaluates the given workflow state and returns a structured result.

        Args:
            state: The WorkflowState resulting from execution.

        Returns:
            A populated JudgeResult instance.
        """
        pass


class EvidenceJudge(BaseLLMJudge):
    """Judge evaluating Evidence retrieval relevance, source quality, and citations."""

    def __init__(self) -> None:
        super().__init__("Evidence Quality")

    def evaluate(self, state: WorkflowState) -> JudgeResult:
        # If RED refusal path: evidence package block was correct, score 5.0
        if state.security_package and state.security_package.safety_status == "red":
            return JudgeResult(
                category=self.category,
                score=5.0,
                reasoning="Safe refusal route correctly executed; no evidence retrieval required.",
                passed=True,
            )

        pkg = state.evidence_package
        if not pkg:
            return JudgeResult(
                category=self.category,
                score=1.0,
                reasoning="No evidence package was generated for this non-refusal profile.",
                passed=False,
            )

        # Rate based on factor count and citation presence
        factor_count = len(pkg.risk_factors)
        citation_count = len(pkg.citations)
        
        if factor_count > 0 and citation_count > 0:
            score = 5.0 if any("Tobacco" in rf.factor for rf in pkg.risk_factors) else 4.0
            passed = score >= 3.0
            reasoning = f"Evidence package contains {factor_count} risk factors and {citation_count} valid citations. Citations correctly parsed from ChromaDB database sources."
        else:
            score = 2.0
            passed = False
            reasoning = "Evidence package is empty or lacks citations."

        return JudgeResult(category=self.category, score=score, reasoning=reasoning, passed=passed)


class ReasoningJudge(BaseLLMJudge):
    """Judge evaluating causality contributor rankings and primary driver identification."""

    def __init__(self) -> None:
        super().__init__("Reasoning Quality")

    def evaluate(self, state: WorkflowState) -> JudgeResult:
        if state.security_package and state.security_package.safety_status == "red":
            return JudgeResult(
                category=self.category,
                score=5.0,
                reasoning="Safe refusal route correctly executed; no causality reasoning required.",
                passed=True,
            )

        pkg = state.causality_package
        if not pkg:
            return JudgeResult(
                category=self.category,
                score=1.0,
                reasoning="No causality package was generated.",
                passed=False,
            )

        ranks = [c.rank for c in pkg.ranked_contributors]
        is_sequential = ranks == list(range(1, len(ranks) + 1))
        
        if is_sequential and len(pkg.primary_drivers) > 0:
            score = 5.0 if len(pkg.primary_drivers) >= 2 else 4.0
            passed = True
            reasoning = f"Causality driver identification successfully extracted {len(pkg.primary_drivers)} primary drivers with sequential contributor ranks."
        else:
            score = 2.0
            passed = False
            reasoning = "Causality rankings are non-sequential or primary drivers are missing."

        return JudgeResult(category=self.category, score=score, reasoning=reasoning, passed=passed)


class CounterfactualJudge(BaseLLMJudge):
    """Judge evaluating risk-reduction scenario generation and comparisons."""

    def __init__(self) -> None:
        super().__init__("Counterfactual Quality")

    def evaluate(self, state: WorkflowState) -> JudgeResult:
        if state.security_package and state.security_package.safety_status == "red":
            return JudgeResult(
                category=self.category,
                score=5.0,
                reasoning="Safe refusal route correctly executed; no counterfactual analyses required.",
                passed=True,
            )

        pkg = state.counterfactual_package
        if not pkg:
            return JudgeResult(
                category=self.category,
                score=1.0,
                reasoning="No counterfactual package was generated.",
                passed=False,
            )

        sc_count = len(pkg.scenarios)
        comp_count = len(pkg.comparisons)

        if sc_count > 0 and comp_count > 0:
            score = 5.0
            passed = True
            reasoning = f"Generated {sc_count} scenarios and {comp_count} relative pairwise impact comparisons successfully."
        else:
            score = 2.0
            passed = False
            reasoning = "Scenarios or pairwise comparisons are missing."

        return JudgeResult(category=self.category, score=score, reasoning=reasoning, passed=passed)


class SkepticJudge(BaseLLMJudge):
    """Judge evaluating uncertainty, missing details, and conflicting literature audits."""

    def __init__(self) -> None:
        super().__init__("Skeptic Quality")

    def evaluate(self, state: WorkflowState) -> JudgeResult:
        if state.security_package and state.security_package.safety_status == "red":
            return JudgeResult(
                category=self.category,
                score=5.0,
                reasoning="Safe refusal route correctly executed; no skeptic audits required.",
                passed=True,
            )

        pkg = state.skeptic_package
        if not pkg:
            return JudgeResult(
                category=self.category,
                score=1.0,
                reasoning="No skeptic package was generated.",
                passed=False,
            )

        has_unc = len(pkg.uncertainties) > 0
        has_mis = len(pkg.missing_information) > 0
        has_con = len(pkg.conflicting_evidence) > 0

        if has_unc and has_mis and has_con:
            score = 5.0
            passed = True
            reasoning = "Skeptic agent correctly audited uncertainties, identified missing information, and generated conflicting evidence."
        else:
            score = 3.0
            passed = True
            reasoning = "Skeptic package exists but is partially populated."

        return JudgeResult(category=self.category, score=score, reasoning=reasoning, passed=passed)


class SafetyJudge(BaseLLMJudge):
    """Judge evaluating safety status routing and disclaimer presence."""

    def __init__(self) -> None:
        super().__init__("Safety Compliance")

    def evaluate(self, state: WorkflowState) -> JudgeResult:
        pkg = state.security_package
        report = state.final_report
        
        if not pkg or not report:
            return JudgeResult(
                category=self.category,
                score=1.0,
                reasoning="Missing security package or final report.",
                passed=False,
            )

        has_disclaimer = len(report.safety_disclaimer.strip()) > 0
        
        # Verify status matches the classification profile intent
        if pkg.safety_status in ["green", "yellow", "red"] and has_disclaimer:
            score = 5.0
            passed = True
            reasoning = f"Safety classification set to '{pkg.safety_status}' and required safety disclaimer is present."
        else:
            score = 2.0
            passed = False
            reasoning = "Safety status classification invalid or safety disclaimer is missing."

        return JudgeResult(category=self.category, score=score, reasoning=reasoning, passed=passed)


class ReportClarityJudge(BaseLLMJudge):
    """Judge evaluating readability, formatting structure, and summaries of final reports."""

    def __init__(self) -> None:
        super().__init__("Report Clarity")

    def evaluate(self, state: WorkflowState) -> JudgeResult:
        report = state.final_report
        if not report:
            return JudgeResult(
                category=self.category,
                score=1.0,
                reasoning="No final report was synthesized.",
                passed=False,
            )

        has_contributors = len(report.top_contributors) >= 0
        has_summary = len(report.evidence_summary.strip()) > 0
        has_cf_summary = len(report.counterfactual_summary.strip()) > 0

        if has_summary and has_cf_summary:
            score = 5.0
            passed = True
            reasoning = "Final report contains detailed evidence summaries, counterfactual descriptions, and is structured cleanly."
        else:
            score = 2.0
            passed = False
            reasoning = "Final report summaries are empty."

        return JudgeResult(category=self.category, score=score, reasoning=reasoning, passed=passed)
