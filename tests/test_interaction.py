import unittest
from schemas.contracts import (
    PatientProfile,
    RiskFactor,
    EvidencePackage,
    CausalityPackage,
    CounterfactualPackage,
    SkepticPackage,
)
from tools.interaction import detect_interactions
from tools.synthesis import generate_final_report
from agents.orchestrator_agent import OrchestratorAgent


class TestRiskInteractionEngine(unittest.TestCase):
    """Test suite for the Risk Interaction Engine (Sprint 3 Milestone 1)."""

    def test_smoking_and_asbestos_interaction(self) -> None:
        """Verifies synergism detection and reasoning for Smoking + Asbestos."""
        profile = PatientProfile(
            session_id="interaction_smoke_asbestos",
            age=45,
            sex="male",
            bmi=24.0,
            smoking_status="active",
            smoking_years=20,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="construction",
            environmental_exposure=["asbestos"],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )
        # Dummy factors to check interaction
        factors = [
            RiskFactor(factor="Tobacco Smoke Exposure", evidence_strength="high", evidence_score=0.85, source_count=10),
            RiskFactor(factor="Environmental Carcinogen Exposure", evidence_strength="medium", evidence_score=0.70, source_count=5)
        ]
        interactions = detect_interactions(profile, factors)
        
        # Check interaction detected correctly
        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0].name, "Tobacco Smoke + Asbestos Synergism")
        self.assertEqual(interactions[0].strength, "high")
        self.assertIn("Tobacco Smoke Exposure", interactions[0].participating_factors)
        self.assertIn("Environmental Carcinogen Exposure", interactions[0].participating_factors)

        # Execute full orchestrator to verify prioritization, causality, and reports
        orchestrator = OrchestratorAgent()
        state = orchestrator.run(profile)
        self.assertEqual(state.status, "COMPLETED")
        
        # Verify confidence is boosted to high due to high-strength interaction
        self.assertEqual(state.final_report.confidence, "high")

        # Verify final report details
        self.assertIn("Tobacco Smoke + Asbestos Synergism", state.final_report.evidence_summary)
        self.assertIn("Smoking cessation is the highest-priority intervention because it disrupts one of the strongest interaction pathways", state.final_report.counterfactual_summary)
        self.assertIn("Evidence Limitation: Synergistic interaction between smoking and asbestos is supported only in high-exposure occupational cohorts", state.final_report.counterfactual_summary)

    def test_smoking_only_no_interaction(self) -> None:
        """Verifies no Tobacco Smoke + Asbestos interaction is detected if asbestos is missing."""
        profile = PatientProfile(
            session_id="interaction_smoke_only",
            age=45,
            sex="male",
            bmi=24.0,
            smoking_status="active",
            smoking_years=20,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )
        factors = [
            RiskFactor(factor="Tobacco Smoke Exposure", evidence_strength="high", evidence_score=0.85, source_count=10)
        ]
        interactions = detect_interactions(profile, factors)
        self.assertEqual(len(interactions), 0)

    def test_asbestos_only_no_interaction(self) -> None:
        """Verifies no Tobacco Smoke + Asbestos interaction is detected if smoking is missing."""
        profile = PatientProfile(
            session_id="interaction_asbestos_only",
            age=45,
            sex="male",
            bmi=24.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="construction",
            environmental_exposure=["asbestos"],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )
        factors = [
            RiskFactor(factor="Environmental Carcinogen Exposure", evidence_strength="high", evidence_score=0.85, source_count=5)
        ]
        interactions = detect_interactions(profile, factors)
        self.assertEqual(len(interactions), 0)

    def test_brca_and_family_history_interaction(self) -> None:
        """Verifies genetic synergism detection and reasoning for BRCA + Family History."""
        profile = PatientProfile(
            session_id="interaction_brca_fh",
            age=35,
            sex="female",
            bmi=22.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=True,
            known_mutations=["BRCA1"],
            previous_cancer_history=False,
        )
        factors = [
            RiskFactor(factor="Genetic/Familial Predisposition", evidence_strength="medium", evidence_score=0.72, source_count=5)
        ]
        interactions = detect_interactions(profile, factors)
        
        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0].name, "BRCA Mutation + Familial Pedigree Susceptibility")
        self.assertEqual(interactions[0].strength, "high")

        orchestrator = OrchestratorAgent()
        state = orchestrator.run(profile)
        self.assertEqual(state.status, "COMPLETED")
        self.assertEqual(state.final_report.confidence, "medium")
        self.assertIn("BRCA Mutation + Familial Pedigree Susceptibility", state.final_report.evidence_summary)
        self.assertIn("Genetic interaction and pedigree penetrance models assume standard inheritance patterns", state.final_report.counterfactual_summary)

    def test_obesity_and_inactivity_interaction(self) -> None:
        """Verifies metabolic overlap detection and reasoning for Obesity + Inactivity."""
        profile = PatientProfile(
            session_id="interaction_obese_inactive",
            age=50,
            sex="female",
            bmi=32.5,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="low",
            diet_quality="high",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )
        factors = [
            RiskFactor(factor="Obesity-related Cancer Risk", evidence_strength="medium", evidence_score=0.65, source_count=4),
            RiskFactor(factor="Physical Inactivity", evidence_strength="low", evidence_score=0.45, source_count=2)
        ]
        interactions = detect_interactions(profile, factors)
        
        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0].name, "Obesity + Inactivity Metabolic Overlap")
        self.assertEqual(interactions[0].strength, "medium")

        orchestrator = OrchestratorAgent()
        state = orchestrator.run(profile)
        self.assertEqual(state.status, "COMPLETED")
        self.assertIn("Obesity + Inactivity Metabolic Overlap", state.final_report.evidence_summary)
        self.assertIn("Overlapping metabolic pathway interactions are supported by observational studies", state.final_report.counterfactual_summary)

    def test_healthy_profile_no_interactions(self) -> None:
        """Verifies a healthy profile has zero detected interactions."""
        profile = PatientProfile(
            session_id="interaction_healthy",
            age=25,
            sex="male",
            bmi=21.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )
        factors = [
            RiskFactor(factor="General Environmental Baseline", evidence_strength="low", evidence_score=0.20, source_count=1)
        ]
        interactions = detect_interactions(profile, factors)
        self.assertEqual(len(interactions), 0)


if __name__ == "__main__":
    unittest.main()
