"""test_judges.py

Unit tests for Stage 17 LLM-judge evaluation framework.
"""

import os
import unittest
import json
from evaluation.datasets import SYNTHETIC_PROFILES
from evaluation.llm_judges import (
    EvidenceJudge,
    ReasoningJudge,
    CounterfactualJudge,
    SkepticJudge,
    SafetyJudge,
    ReportClarityJudge,
    JudgeResult,
)
from evaluation.judge_runner import LLMJudgeRunner
from schemas.contracts import (
    WorkflowState,
    SecurityPackage,
    EvidencePackage,
    CausalityPackage,
    CounterfactualPackage,
    SkepticPackage,
    FinalReport,
    Contributor,
    Scenario,
    Comparison,
    ConflictingEvidence,
)


class TestLLMJudges(unittest.TestCase):
    """Test suite validating LLM-judge behaviors, scoring, persistence, and aggregations."""

    def setUp(self) -> None:
        self.evidence_judge = EvidenceJudge()
        self.reasoning_judge = ReasoningJudge()
        self.counterfactual_judge = CounterfactualJudge()
        self.skeptic_judge = SkepticJudge()
        self.safety_judge = SafetyJudge()
        self.clarity_judge = ReportClarityJudge()

    def test_evidence_judge_red(self) -> None:
        """Verify evidence judge behavior on RED status state."""
        state = WorkflowState(
            session_id="test_red",
            security_package=SecurityPackage(
                safety_status="red",
                prompt_injection_detected=False,
                pii_detected=False,
                redacted_fields=[],
                medical_request_type="prescription",
                clean_profile=SYNTHETIC_PROFILES["red_safety_profile"]["profile"]
            ),
            current_step="SafeRefusalNode",
            status="COMPLETED"
        )
        res = self.evidence_judge.evaluate(state)
        self.assertIsInstance(res, JudgeResult)
        self.assertEqual(res.score, 5.0)
        self.assertTrue(res.passed)

    def test_reasoning_judge_sequential(self) -> None:
        """Verify reasoning judge evaluates ranks correctly."""
        state = WorkflowState(
            session_id="test_re",
            causality_package=CausalityPackage(
                ranked_contributors=[
                    Contributor(factor="F1", rank=1, reason="R1"),
                    Contributor(factor="F2", rank=2, reason="R2"),
                ],
                primary_drivers=["F1", "F2"],
                causal_confidence="high"
            ),
            current_step="CausalityAgent",
            status="COMPLETED"
        )
        res = self.reasoning_judge.evaluate(state)
        self.assertEqual(res.score, 5.0)
        self.assertTrue(res.passed)

    def test_counterfactual_judge(self) -> None:
        """Verify counterfactual scenarios and comparisons checks."""
        state = WorkflowState(
            session_id="test_cf",
            counterfactual_package=CounterfactualPackage(
                scenarios=[Scenario(scenario_id="S1", change="C1", expected_effect="low", reasoning="R1")],
                comparisons=[Comparison(scenario_a="S1", scenario_b="S1", higher_impact="Draw")]
            ),
            current_step="CounterfactualAgent",
            status="COMPLETED"
        )
        res = self.counterfactual_judge.evaluate(state)
        self.assertEqual(res.score, 5.0)
        self.assertTrue(res.passed)

    def test_skeptic_judge(self) -> None:
        """Verify skeptic uncertainty and limitations audits scoring."""
        state = WorkflowState(
            session_id="test_sk",
            skeptic_package=SkepticPackage(
                confidence="medium",
                uncertainties=["Unc1"],
                limitations=["Lim1"],
                conflicting_evidence=[ConflictingEvidence(factor="F1", evidence="E1", source="S1")],
                missing_information=["Mis1"]
            ),
            current_step="SkepticAgent",
            status="COMPLETED"
        )
        res = self.skeptic_judge.evaluate(state)
        self.assertEqual(res.score, 5.0)
        self.assertTrue(res.passed)

    def test_safety_and_clarity_judges(self) -> None:
        """Verify safety and report clarity judges on non-empty completed reports."""
        state = WorkflowState(
            session_id="test_sf_cl",
            security_package=SecurityPackage(
                safety_status="green",
                prompt_injection_detected=False,
                pii_detected=False,
                redacted_fields=[],
                medical_request_type="explanation",
                clean_profile=SYNTHETIC_PROFILES["smoking_profile"]["profile"]
            ),
            final_report=FinalReport(
                top_contributors=["F1"],
                evidence_summary="Extracted summary",
                counterfactual_summary="Counterfactual summary",
                limitations=[],
                confidence="high",
                citations=[],
                safety_disclaimer="Disclaimer notice"
            ),
            current_step="END",
            status="COMPLETED"
        )
        sf_res = self.safety_judge.evaluate(state)
        cl_res = self.clarity_judge.evaluate(state)
        
        self.assertEqual(sf_res.score, 5.0)
        self.assertTrue(sf_res.passed)
        self.assertEqual(cl_res.score, 5.0)
        self.assertTrue(cl_res.passed)

    def test_judge_runner_persistence_and_aggregation(self) -> None:
        """Verify that JudgeRunner correctly persists results to JSON and Markdown files."""
        json_path = "/Users/lovey/.gemini/antigravity-ide/brain/fa7ddcd5-6da4-4707-b164-7e561336d922/scratch/test_results.json"
        md_path = "/Users/lovey/.gemini/antigravity-ide/brain/fa7ddcd5-6da4-4707-b164-7e561336d922/scratch/test_report.md"
        
        runner = LLMJudgeRunner()
        results = runner.run_evaluation_suite(json_path, md_path)
        
        # Verify result format
        self.assertTrue(len(results) > 0)
        first_case = list(results.values())[0]
        self.assertIn("stage16_metrics", first_case)
        self.assertIn("stage17_judges", first_case)
        
        # Check files exist
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(md_path))
        
        # Clean up files
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(md_path):
            os.remove(md_path)


if __name__ == "__main__":
    unittest.main()
