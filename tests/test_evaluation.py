"""test_evaluation.py

Unit tests for Stage 16 CRRA evaluation and benchmarking framework.
"""

import unittest
from evaluation.datasets import SYNTHETIC_PROFILES
from evaluation.metrics import (
    evaluate_evidence_quality,
    evaluate_reasoning_quality,
    evaluate_counterfactual_quality,
    evaluate_skeptic_quality,
    evaluate_safety_compliance,
)
from evaluation.benchmarks import CRRABenchmarkRunner
from schemas.contracts import (
    WorkflowState,
    SecurityPackage,
    EvidencePackage,
    RiskFactor,
    Citation,
)


class TestCRRAEvaluationFramework(unittest.TestCase):
    """Test suite for validating the evaluation datasets, metrics, and benchmark execution."""

    def test_dataset_loading(self) -> None:
        """Verify that all required synthetic profiles exist and load correctly."""
        expected_keys = [
            "smoking_profile",
            "genetic_profile",
            "lifestyle_profile",
            "sun_uv_profile",
            "alcohol_profile",
            "missing_info_profile",
            "red_safety_profile",
            "yellow_safety_profile",
            "healthy_baseline_profile",
            "heavy_smoker_profile",
            "brca_mutation_profile",
            "obesity_profile",
            "alcohol_misuse_profile",
            "occupational_exposure_profile",
            "mixed_lifestyle_profile",
            "previous_cancer_history_profile",
            "multiple_interacting_factors_profile",
            "low_information_patient_profile",
        ]
        for key in expected_keys:
            self.assertIn(key, SYNTHETIC_PROFILES)
            data = SYNTHETIC_PROFILES[key]
            self.assertIn("profile", data)
            self.assertIn("expected_risk_factors", data)
            self.assertIn("expected_primary_drivers", data)
            self.assertIn("expected_safety_status", data)

    def test_metric_execution_red(self) -> None:
        """Verify metric scoring for RED safety blocked profiles."""
        state = WorkflowState(
            session_id="test_red",
            security_package=SecurityPackage(
                safety_status="red",
                prompt_injection_detected=False,
                pii_detected=False,
                redacted_fields=[],
                medical_request_type="diagnosis",
                clean_profile=SYNTHETIC_PROFILES["red_safety_profile"]["profile"]
            ),
            current_step="SafeRefusalNode",
            status="COMPLETED"
        )
        
        # When safety is RED, intermediate packages are expected to be None (blocked),
        # but evaluation should return perfect score (1.0) because blocking was correct.
        ev_metrics = evaluate_evidence_quality(state, [])
        self.assertEqual(ev_metrics["overall_score"], 1.0)
        
        re_metrics = evaluate_reasoning_quality(state, [])
        self.assertEqual(re_metrics["overall_score"], 1.0)
        
        cf_metrics = evaluate_counterfactual_quality(state)
        self.assertEqual(cf_metrics["overall_score"], 1.0)
        
        sk_metrics = evaluate_skeptic_quality(state)
        self.assertEqual(sk_metrics["overall_score"], 1.0)

    def test_safety_compliance_scoring(self) -> None:
        """Verify safety compliance logic for GREEN, YELLOW, and RED statuses."""
        # Case 1: Match and disclaimer present -> 1.0
        state_ok = WorkflowState(
            session_id="test_sf",
            security_package=SecurityPackage(
                safety_status="green",
                prompt_injection_detected=False,
                pii_detected=False,
                redacted_fields=[],
                medical_request_type="explanation",
                clean_profile=SYNTHETIC_PROFILES["smoking_profile"]["profile"]
            ),
            current_step="END",
            status="COMPLETED"
        )
        # Injects final report with dummy disclaimer
        from schemas.contracts import FinalReport
        state_ok.final_report = FinalReport(
            top_contributors=[],
            evidence_summary="Some summary",
            counterfactual_summary="Some counterfactuals",
            limitations=[],
            confidence="high",
            citations=[],
            safety_disclaimer="Disclaimer: not advice"
        )
        sf_metrics = evaluate_safety_compliance(state_ok, "green")
        self.assertEqual(sf_metrics["overall_score"], 1.0)
        
        # Case 2: Mismatched safety status -> 0.0
        sf_metrics_mismatch = evaluate_safety_compliance(state_ok, "red")
        self.assertEqual(sf_metrics_mismatch["overall_score"], 0.0)

    def test_benchmark_runner_execution(self) -> None:
        """Run E2E benchmark evaluation and check output summary stats format."""
        runner = CRRABenchmarkRunner()
        results = runner.run_benchmark()
        
        self.assertIn("results", results)
        self.assertIn("summary", results)
        
        summary = results["summary"]
        self.assertEqual(summary["total_cases"], len(SYNTHETIC_PROFILES))
        self.assertTrue(0.0 <= summary["overall_pipeline_accuracy"] <= 1.0)
        self.assertTrue(0.0 <= summary["average_safety_compliance"] <= 1.0)


if __name__ == "__main__":
    unittest.main()
