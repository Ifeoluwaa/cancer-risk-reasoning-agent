"""Unit tests for Stage 9 causality reasoning tools.
"""

import unittest
from schemas.contracts import PatientProfile, RiskFactor, Contributor, CausalityPackage
from tools.causality import rank_contributors, identify_primary_drivers


class TestCausalityLayer(unittest.TestCase):
    """Test suite for deterministic causality reasoning in tools/causality.py."""

    def setUp(self) -> None:
        """Set up standard objects for testing."""
        self.profile = PatientProfile(
            session_id="session_456",
            age=52,
            sex="male",
            bmi=26.0,
            smoking_status="active",
            smoking_years=20,
            alcohol_use="moderate",
            physical_activity="medium",
            diet_quality="medium",
            sun_exposure="high",
            occupation="landscaping",
            environmental_exposure=[],
            family_history=True,
            known_mutations=["BRCA1"],
            previous_cancer_history=False,
        )

        self.factors = [
            RiskFactor(factor="UV/Sun Exposure", evidence_strength="medium", evidence_score=0.70, source_count=4),
            RiskFactor(factor="Tobacco Smoke Exposure", evidence_strength="high", evidence_score=0.95, source_count=12),
            RiskFactor(factor="Genetic/Familial Predisposition", evidence_strength="medium", evidence_score=0.72, source_count=5),
        ]

    def test_contributor_ranking_order_and_indexing(self) -> None:
        """Verifies correct sorting and 1-indexed ranking of contributors."""
        contributors = rank_contributors(self.factors)
        self.assertEqual(len(contributors), 3)

        # First ranked should be Tobacco Smoke Exposure (highest score 0.95)
        self.assertEqual(contributors[0].factor, "Tobacco Smoke Exposure")
        self.assertEqual(contributors[0].rank, 1)

        # Second ranked should be Genetic/Familial Predisposition (score 0.72)
        self.assertEqual(contributors[1].factor, "Genetic/Familial Predisposition")
        self.assertEqual(contributors[1].rank, 2)

        # Third ranked should be UV/Sun Exposure (score 0.70)
        self.assertEqual(contributors[2].factor, "UV/Sun Exposure")
        self.assertEqual(contributors[2].rank, 3)

    def test_contributor_ranking_personalized_reasons(self) -> None:
        """Verifies clinical reasons are generated and personalized based on the patient profile."""
        contributors = rank_contributors(self.factors, profile=self.profile)

        # Tobacco reason should mention smoking history
        self.assertIn("smoking 20 years", contributors[0].reason)

        # Genetic reason should mention BRCA1 mutation
        self.assertIn("mutations: BRCA1", contributors[1].reason)

        # UV reason should mention high sun exposure
        self.assertIn("high sun exposure", contributors[2].reason)

    def test_primary_driver_selection(self) -> None:
        """Verifies filtering of primary drivers based on rank thresholds."""
        contributors = rank_contributors(self.factors)

        # Threshold rank = 1
        drivers_t1 = identify_primary_drivers(contributors, threshold_rank=1)
        self.assertEqual(len(drivers_t1), 1)
        self.assertEqual(drivers_t1[0], "Tobacco Smoke Exposure")

        # Threshold rank = 2
        drivers_t2 = identify_primary_drivers(contributors, threshold_rank=2)
        self.assertEqual(len(drivers_t2), 2)
        self.assertEqual(drivers_t2[0], "Tobacco Smoke Exposure")
        self.assertEqual(drivers_t2[1], "Genetic/Familial Predisposition")

    def test_causality_package_generation(self) -> None:
        """Verifies instantiation and validation of the CausalityPackage schema."""
        contributors = rank_contributors(self.factors, profile=self.profile)
        primary_drivers = identify_primary_drivers(contributors, threshold_rank=1)

        package = CausalityPackage(
            ranked_contributors=contributors,
            primary_drivers=primary_drivers,
            causal_confidence="high"
        )

        self.assertIsInstance(package, CausalityPackage)
        self.assertEqual(package.primary_drivers, ["Tobacco Smoke Exposure"])
        self.assertEqual(package.causal_confidence, "high")
        self.assertEqual(len(package.ranked_contributors), 3)

    def test_empty_or_low_evidence_cases(self) -> None:
        """Verifies behavior when input factor list is empty or contains only low evidence."""
        # 1. Empty factors list
        contributors_empty = rank_contributors([])
        self.assertEqual(len(contributors_empty), 0)

        drivers_empty = identify_primary_drivers(contributors_empty)
        self.assertEqual(len(drivers_empty), 0)

        # 2. Low evidence baseline factor
        low_factors = [
            RiskFactor(factor="General Environmental Baseline", evidence_strength="low", evidence_score=0.25, source_count=2)
        ]
        contributors_low = rank_contributors(low_factors, profile=self.profile)
        self.assertEqual(len(contributors_low), 1)
        self.assertEqual(contributors_low[0].factor, "General Environmental Baseline")
        self.assertEqual(contributors_low[0].rank, 1)


if __name__ == "__main__":
    unittest.main()
