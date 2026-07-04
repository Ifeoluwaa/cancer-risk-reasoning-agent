import unittest
from schemas.contracts import PatientProfile, RiskFactor, EvidencePackage, Contributor
from tools.attribution import calculate_attribution


class TestRiskAttributionEngine(unittest.TestCase):
    """Test suite for the Patient-Specific Risk Attribution Engine (Sprint 3 Milestone 2)."""

    def setUp(self) -> None:
        """Set up patient profiles and risk factors for testing."""
        # 1. Healthy Profile
        self.profile_healthy = PatientProfile(
            session_id="session_healthy",
            age=28,
            sex="male",
            bmi=22.0,
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

        # 2. Smoking Profile (Lifestyle)
        self.profile_smoking = PatientProfile(
            session_id="session_smoking",
            age=50,
            sex="male",
            bmi=24.5,
            smoking_status="active",
            smoking_years=25,
            alcohol_use="heavy",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )

        # 3. BRCA Mutation Profile (Hereditary)
        self.profile_brca = PatientProfile(
            session_id="session_brca",
            age=35,
            sex="female",
            bmi=21.0,
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

    def test_healthy_profile_attribution_normalization(self) -> None:
        """Verifies that attribution percentages for a healthy profile sum to ~100%."""
        evidence = EvidencePackage(
            risk_factors=[
                RiskFactor(factor="General Environmental Baseline", evidence_strength="low", evidence_score=0.20, source_count=1)
            ],
            citations=[],
            retrieved_documents=[]
        )
        contributors = calculate_attribution(self.profile_healthy, evidence)
        self.assertEqual(len(contributors), 1)
        self.assertAlmostEqual(contributors[0].attribution_percentage, 100.0, places=1)
        self.assertEqual(contributors[0].classification, "Background Risk")

    def test_smoking_and_alcohol_lifestyle_attribution(self) -> None:
        """Verifies lifestyle weighting, normalization, and classification for smoker/alcohol profiles."""
        evidence = EvidencePackage(
            risk_factors=[
                RiskFactor(factor="Tobacco Smoke Exposure", evidence_strength="high", evidence_score=0.90, source_count=10),
                RiskFactor(factor="Alcohol Consumption Risk", evidence_strength="medium", evidence_score=0.70, source_count=5),
            ],
            citations=[],
            retrieved_documents=[],
            interactions=[]
        )
        contributors = calculate_attribution(self.profile_smoking, evidence)
        self.assertTrue(len(contributors) >= 2)
        
        # Verify normalization sum to ~100%
        total_pct = sum(c.attribution_percentage for c in contributors)
        self.assertAlmostEqual(total_pct, 100.0, places=1)

        # Tobacco should be ranked higher than alcohol
        self.assertEqual(contributors[0].factor, "Tobacco Smoke Exposure")
        self.assertEqual(contributors[0].classification, "Primary Driver")
        self.assertTrue(contributors[0].attribution_percentage > contributors[1].attribution_percentage)

    def test_brca_hereditary_weighting(self) -> None:
        """Verifies that hereditary risk factors receive elevated weighting."""
        evidence = EvidencePackage(
            risk_factors=[
                RiskFactor(factor="Genetic/Familial Predisposition", evidence_strength="high", evidence_score=0.85, source_count=8),
                RiskFactor(factor="UV/Sun Exposure", evidence_strength="low", evidence_score=0.30, source_count=2),
            ],
            citations=[],
            retrieved_documents=[],
            interactions=[]
        )
        contributors = calculate_attribution(self.profile_brca, evidence)
        
        # Genetic factors should get weighted by 1.25, UV by 0.75
        total_pct = sum(c.attribution_percentage for c in contributors)
        self.assertAlmostEqual(total_pct, 100.0, places=1)
        
        # Verify genetic factor is the Primary Driver
        genetic_contrib = next(c for c in contributors if "Genetic" in c.factor)
        self.assertEqual(genetic_contrib.classification, "Primary Driver")
        self.assertTrue(genetic_contrib.attribution_percentage > 70.0)


if __name__ == "__main__":
    unittest.main()
