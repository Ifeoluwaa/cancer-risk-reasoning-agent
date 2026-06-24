"""Unit tests for Stage 7 orchestration helper functions.
"""

import unittest
from schemas.contracts import (
    PatientProfile,
    SecurityPackage,
    EvidencePackage,
    CausalityPackage,
    CounterfactualPackage,
    SkepticPackage,
    AggregatedAnalysis,
    FinalReport,
    WorkflowState,
    RiskFactor,
    Citation,
    Contributor,
    Scenario,
    Comparison,
    ConflictingEvidence,
)
from tools.orchestration import (
    dispatch_tasks,
    aggregate_outputs,
    validate_workflow_state,
)


class TestOrchestrationDeterministic(unittest.TestCase):
    """Test suite for orchestration helper logic in tools/orchestration.py."""

    def setUp(self) -> None:
        """Set up standard dummy objects for testing."""
        self.profile = PatientProfile(
            session_id="session_123",
            age=45,
            sex="female",
            bmi=24.5,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="light",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="medium",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )

        self.sec_pkg_green = SecurityPackage(
            safety_status="green",
            prompt_injection_detected=False,
            pii_detected=False,
            redacted_fields=[],
            medical_request_type="explanation",
            clean_profile=self.profile,
        )

        self.sec_pkg_red = SecurityPackage(
            safety_status="red",
            prompt_injection_detected=True,
            pii_detected=False,
            redacted_fields=[],
            medical_request_type="diagnosis",
            clean_profile=self.profile,
        )

        # Build dummy packages
        rf = RiskFactor(factor="Sun Exposure", evidence_strength="medium", evidence_score=0.6, source_count=2)
        cit = Citation(source="NEJM", title="UV Radiation Risks", year=2018)
        self.evidence_pkg = EvidencePackage(
            risk_factors=[rf],
            citations=[cit],
            retrieved_documents=["doc1"]
        )

        cont = Contributor(factor="Sun Exposure", rank=1, reason="UV damage triggers mutation")
        self.causality_pkg = CausalityPackage(
            ranked_contributors=[cont],
            primary_drivers=["Sun Exposure"],
            causal_confidence="medium"
        )

        sc = Scenario(scenario_id="S1", change="Wear sunscreen", expected_effect="medium", reasoning="Blocks UV rays")
        comp = Comparison(scenario_a="S1", scenario_b="S2", higher_impact="S1")
        self.counterfactual_pkg = CounterfactualPackage(
            scenarios=[sc],
            comparisons=[comp]
        )

        conf = ConflictingEvidence(factor="Sun Exposure", evidence="Some exposure is good for Vitamin D", source="Endocrine Journal")
        self.skeptic_pkg = SkepticPackage(
            confidence="high",
            uncertainties=["lack of precise exposure tracking"],
            limitations=["no direct bio-markers"],
            conflicting_evidence=[conf],
            missing_information=[]
        )

        self.aggregated_analysis = AggregatedAnalysis(
            patient_profile=self.profile,
            evidence_package=self.evidence_pkg,
            causality_package=self.causality_pkg,
            counterfactual_package=self.counterfactual_pkg,
            skeptic_package=self.skeptic_pkg
        )

        self.final_report = FinalReport(
            top_contributors=["Sun Exposure"],
            evidence_summary="Correlated with UV radiation",
            counterfactual_summary="Sunscreen helps",
            limitations=["exposure tracking"],
            confidence="medium",
            citations=[cit],
            safety_disclaimer="Not medical advice"
        )

    def test_dispatch_tasks_progression(self) -> None:
        """Verifies the progression of task dispatching for a green workflow state."""
        state = WorkflowState(session_id="session_123")

        # 0. No profile
        self.assertEqual(dispatch_tasks(state), [])

        # 1. Start with profile set
        state.patient_profile = self.profile
        self.assertEqual(dispatch_tasks(state), ["SecurityAgent"])

        # 2. After SecurityAgent
        state.security_package = self.sec_pkg_green
        self.assertEqual(dispatch_tasks(state), ["EvidenceAgent"])

        # 3. After EvidenceAgent
        state.evidence_package = self.evidence_pkg
        self.assertEqual(dispatch_tasks(state), ["CausalityAgent"])

        # 4. After CausalityAgent
        state.causality_package = self.causality_pkg
        self.assertEqual(dispatch_tasks(state), ["CounterfactualAgent"])

        # 5. After CounterfactualAgent
        state.counterfactual_package = self.counterfactual_pkg
        self.assertEqual(dispatch_tasks(state), ["SkepticAgent"])

        # 6. After SkepticAgent
        state.skeptic_package = self.skeptic_pkg
        self.assertEqual(dispatch_tasks(state), ["OrchestrationAggregation"])

        # 7. After Aggregation
        state.aggregated_analysis = self.aggregated_analysis
        self.assertEqual(dispatch_tasks(state), ["SynthesisAgent"])

        # 8. After FinalReport
        state.final_report = self.final_report
        self.assertEqual(dispatch_tasks(state), [])

    def test_dispatch_tasks_red_refusal(self) -> None:
        """Verifies task dispatching handles RED safety status correctly."""
        state = WorkflowState(
            session_id="session_123",
            patient_profile=self.profile,
            security_package=self.sec_pkg_red
        )

        # Should immediately dispatch SafeRefusalNode
        self.assertEqual(dispatch_tasks(state), ["SafeRefusalNode"])

        # After SafeRefusalNode sets final report, dispatch list should be empty
        state.final_report = self.final_report
        self.assertEqual(dispatch_tasks(state), [])

    def test_aggregate_outputs_success(self) -> None:
        """Verifies successful construction of AggregatedAnalysis."""
        state = WorkflowState(
            session_id="session_123",
            patient_profile=self.profile,
            security_package=self.sec_pkg_green,
            evidence_package=self.evidence_pkg,
            causality_package=self.causality_pkg,
            counterfactual_package=self.counterfactual_pkg,
            skeptic_package=self.skeptic_pkg
        )

        agg = aggregate_outputs(state)
        self.assertIsInstance(agg, AggregatedAnalysis)
        self.assertEqual(agg.patient_profile.session_id, "session_123")
        self.assertEqual(len(agg.evidence_package.risk_factors), 1)

    def test_aggregate_outputs_missing_fails(self) -> None:
        """Verifies that aggregate_outputs raises ValueError if any components are missing."""
        state = WorkflowState(
            session_id="session_123",
            patient_profile=self.profile,
            security_package=self.sec_pkg_green,
            evidence_package=self.evidence_pkg,
            # Missing causality_package
            counterfactual_package=self.counterfactual_pkg,
            skeptic_package=self.skeptic_pkg
        )

        with self.assertRaises(ValueError):
            aggregate_outputs(state)

    def test_validate_workflow_state_valid(self) -> None:
        """Verifies validation logic on valid workflow states."""
        # 1. PENDING status with only session_id is valid
        state_pending = WorkflowState(session_id="session_123", status="PENDING")
        self.assertTrue(validate_workflow_state(state_pending))

        # 2. RUNNING status with some elements
        state_running = WorkflowState(
            session_id="session_123",
            status="RUNNING",
            patient_profile=self.profile,
            security_package=self.sec_pkg_green
        )
        self.assertTrue(validate_workflow_state(state_running))

        # 3. Valid COMPLETED successful state
        state_completed_green = WorkflowState(
            session_id="session_123",
            status="COMPLETED",
            patient_profile=self.profile,
            security_package=self.sec_pkg_green,
            evidence_package=self.evidence_pkg,
            causality_package=self.causality_pkg,
            counterfactual_package=self.counterfactual_pkg,
            skeptic_package=self.skeptic_pkg,
            aggregated_analysis=self.aggregated_analysis,
            final_report=self.final_report
        )
        self.assertTrue(validate_workflow_state(state_completed_green))

        # 4. Valid COMPLETED blocked state (RED safety status, no intermediate packages)
        state_completed_red = WorkflowState(
            session_id="session_123",
            status="COMPLETED",
            patient_profile=self.profile,
            security_package=self.sec_pkg_red,
            final_report=self.final_report
        )
        self.assertTrue(validate_workflow_state(state_completed_red))

    def test_validate_workflow_state_invalid(self) -> None:
        """Verifies validation logic catches invalid/inconsistent states."""
        # 1. Missing session_id
        with self.assertRaises(ValueError):
            validate_workflow_state(WorkflowState(session_id="", status="PENDING"))

        # 2. Invalid status
        with self.assertRaises(ValueError):
            validate_workflow_state(WorkflowState(session_id="123", status="INVALID_STATUS"))

        # 3. COMPLETED but missing final_report
        state_no_report = WorkflowState(
            session_id="session_123",
            status="COMPLETED",
            patient_profile=self.profile,
            security_package=self.sec_pkg_green
        )
        with self.assertRaises(ValueError):
            validate_workflow_state(state_no_report)

        # 4. COMPLETED successful (green) state but missing intermediate packages
        state_missing_intermediate = WorkflowState(
            session_id="session_123",
            status="COMPLETED",
            patient_profile=self.profile,
            security_package=self.sec_pkg_green,
            # Missing evidence_package
            causality_package=self.causality_pkg,
            counterfactual_package=self.counterfactual_pkg,
            skeptic_package=self.skeptic_pkg,
            aggregated_analysis=self.aggregated_analysis,
            final_report=self.final_report
        )
        with self.assertRaises(ValueError):
            validate_workflow_state(state_missing_intermediate)

        # 5. COMPLETED blocked (red) state but contains unexpected intermediate packages
        state_red_with_intermediate = WorkflowState(
            session_id="session_123",
            status="COMPLETED",
            patient_profile=self.profile,
            security_package=self.sec_pkg_red,
            evidence_package=self.evidence_pkg, # Unexpected
            final_report=self.final_report
        )
        with self.assertRaises(ValueError):
            validate_workflow_state(state_red_with_intermediate)


if __name__ == "__main__":
    unittest.main()
