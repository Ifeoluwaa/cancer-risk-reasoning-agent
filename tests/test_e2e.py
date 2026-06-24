"""End-to-End (E2E) integration tests for the CRRA multi-agent reasoning pipeline.
"""

import unittest
from schemas.contracts import (
    PatientProfile,
    WorkflowState,
    SecurityPackage,
    EvidencePackage,
    CausalityPackage,
    CounterfactualPackage,
    SkepticPackage,
    FinalReport,
)
from agents.orchestrator_agent import OrchestratorAgent


class TestCRRAReasoningPipelineE2E(unittest.TestCase):
    """E2E integration test suite for validating workflow state, schema compliance, and routing."""

    def setUp(self) -> None:
        """Initialize the OrchestratorAgent."""
        self.orchestrator = OrchestratorAgent()

    def test_smoking_related_profile_e2e(self) -> None:
        """E2E test with a patient having standard tobacco smoking habits."""
        profile = PatientProfile(
            session_id="session_e2e_smoking",
            age=48,
            sex="male",
            bmi=24.0,
            smoking_status="active",
            smoking_years=20,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="engineer",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )

        state = self.orchestrator.run(profile)

        # 1. Verify workflow execution completed successfully
        self.assertEqual(state.status, "COMPLETED")
        self.assertEqual(state.current_step, "END")
        self.assertEqual(len(state.errors), 0)

        # 2. Verify schema compliance of intermediate packages
        self.assertIsInstance(state.security_package, SecurityPackage)
        self.assertIsInstance(state.evidence_package, EvidencePackage)
        self.assertIsInstance(state.causality_package, CausalityPackage)
        self.assertIsInstance(state.counterfactual_package, CounterfactualPackage)
        self.assertIsInstance(state.skeptic_package, SkepticPackage)

        # 3. Verify specific risk findings
        evidence_factors = [rf.factor for rf in state.evidence_package.risk_factors]
        self.assertIn("Tobacco Smoke Exposure", evidence_factors)

        # 4. Verify FinalReport schema and safety disclaimer
        self.assertIsInstance(state.final_report, FinalReport)
        self.assertTrue(len(state.final_report.top_contributors) > 0)
        self.assertIn("Tobacco Smoke Exposure", state.final_report.top_contributors)
        self.assertIn("Disclaimer:", state.final_report.safety_disclaimer)

    def test_genetic_risk_profile_e2e(self) -> None:
        """E2E test with a patient having family history and BRCA1 genetic mutations."""
        profile = PatientProfile(
            session_id="session_e2e_genetic",
            age=32,
            sex="female",
            bmi=21.5,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="teacher",
            environmental_exposure=[],
            family_history=True,
            known_mutations=["BRCA1"],
            previous_cancer_history=False,
        )

        state = self.orchestrator.run(profile)

        # 1. Verify workflow execution completed successfully
        self.assertEqual(state.status, "COMPLETED")
        self.assertEqual(state.current_step, "END")
        self.assertEqual(len(state.errors), 0)

        # 2. Verify schema compliance
        self.assertIsInstance(state.security_package, SecurityPackage)
        self.assertIsInstance(state.evidence_package, EvidencePackage)
        self.assertIsInstance(state.causality_package, CausalityPackage)
        self.assertIsInstance(state.final_report, FinalReport)

        # 3. Verify fallback risk factor extraction
        evidence_factors = [rf.factor for rf in state.evidence_package.risk_factors]
        self.assertIn("General Environmental Factors", evidence_factors)

        # 4. Verify FinalReport and safety disclaimer
        self.assertIn("General Environmental Factors", state.final_report.top_contributors)
        self.assertIn("not medical advice", state.final_report.safety_disclaimer.lower())

    def test_lifestyle_risk_profile_e2e(self) -> None:
        """E2E test with a patient presenting high BMI, alcohol habits, and sun exposure."""
        profile = PatientProfile(
            session_id="session_e2e_lifestyle",
            age=45,
            sex="female",
            bmi=27.2,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="moderate",
            physical_activity="low",
            diet_quality="medium",
            sun_exposure="high",
            occupation="landscaping",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )

        state = self.orchestrator.run(profile)

        # 1. Verify workflow execution completed successfully
        self.assertEqual(state.status, "COMPLETED")
        self.assertEqual(state.current_step, "END")

        # 2. Verify schema compliance
        self.assertIsInstance(state.security_package, SecurityPackage)
        self.assertIsInstance(state.evidence_package, EvidencePackage)
        self.assertIsInstance(state.final_report, FinalReport)

        cf_scenarios = [s.change for s in state.counterfactual_package.scenarios]
        self.assertTrue(any("activity" in s.lower() for s in cf_scenarios))
        self.assertTrue(any("diet" in s.lower() or "fiber" in s.lower() for s in cf_scenarios))

    def test_red_safety_routing_profile_e2e(self) -> None:
        """E2E test with a query containing trigger words causing RED safety block routing."""
        profile = PatientProfile(
            session_id="session_e2e_red_trigger",
            age=55,
            sex="male",
            bmi=25.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="medium",
            diet_quality="medium",
            sun_exposure="low",
            occupation="diagnose cancer treatment",  # Trigger red path
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )

        state = self.orchestrator.run(profile)

        # 1. Verify workflow completed terminal refusal successfully
        self.assertEqual(state.status, "COMPLETED")
        self.assertEqual(state.current_step, "END")

        # 2. Verify Security package is populated and is RED
        self.assertIsInstance(state.security_package, SecurityPackage)
        self.assertEqual(state.security_package.safety_status, "red")

        # 3. Verify intermediate reasoning packages are BLOCKED (not populated)
        self.assertIsNone(state.evidence_package)
        self.assertIsNone(state.causality_package)
        self.assertIsNone(state.counterfactual_package)
        self.assertIsNone(state.skeptic_package)
        self.assertIsNone(state.aggregated_analysis)

        # 4. Verify refusal report contains disclaimer and appropriate warnings
        self.assertIsInstance(state.final_report, FinalReport)
        self.assertEqual(len(state.final_report.top_contributors), 0)
        self.assertIn("blocked by the security system", state.final_report.evidence_summary)
        self.assertIn("Disclaimer: The requested query was classified as a diagnostic or treatment", state.final_report.safety_disclaimer)


if __name__ == "__main__":
    unittest.main()
