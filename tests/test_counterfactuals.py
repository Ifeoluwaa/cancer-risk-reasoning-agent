"""Unit tests for Stage 10 counterfactual reasoning tools.
"""

import unittest
from schemas.contracts import PatientProfile, Scenario, Comparison, CausalityPackage, CounterfactualPackage
from tools.counterfactuals import (
    generate_scenarios,
    compare_scenarios,
    create_counterfactual_package,
)


class TestCounterfactualLayer(unittest.TestCase):
    """Test suite for deterministic counterfactual reasoning in tools/counterfactuals.py."""

    def setUp(self) -> None:
        """Set up standard objects for testing."""
        self.profile_normal = PatientProfile(
            session_id="session_cf_1",
            age=40,
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
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )

        self.profile_high_bmi = PatientProfile(
            session_id="session_cf_2",
            age=40,
            sex="female",
            bmi=28.5,
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

    def test_scenario_generation_by_drivers(self) -> None:
        """Verifies scenario generation matching various risk drivers."""
        # 1. Tobacco Smoke Exposure
        scenarios_tobacco = generate_scenarios(self.profile_normal, ["Tobacco Smoke Exposure"])
        ids_tobacco = [s.scenario_id for s in scenarios_tobacco]
        self.assertIn("S_SMOKE_STOP", ids_tobacco)
        self.assertIn("S_SMOKE_HALF", ids_tobacco)
        self.assertEqual(scenarios_tobacco[0].expected_effect, "high")

        # 2. UV/Sun Exposure
        scenarios_sun = generate_scenarios(self.profile_normal, ["UV/Sun Exposure"])
        ids_sun = [s.scenario_id for s in scenarios_sun]
        self.assertIn("S_SUN_PROTECT", ids_sun)
        self.assertIn("S_SUN_LIMIT", ids_sun)

        # 3. Alcohol Consumption Risk
        scenarios_alcohol = generate_scenarios(self.profile_normal, ["Alcohol Consumption Risk"])
        ids_alcohol = [s.scenario_id for s in scenarios_alcohol]
        self.assertIn("S_ALCOHOL_STOP", ids_alcohol)
        self.assertIn("S_ALCOHOL_LIMIT", ids_alcohol)

        # 4. Age-related Cellular Senescence
        scenarios_age = generate_scenarios(self.profile_normal, ["Age-related Cellular Senescence"])
        ids_age = [s.scenario_id for s in scenarios_age]
        self.assertIn("S_CELL_ANTIOXIDANT", ids_age)

        # 5. Genetic/Familial Predisposition
        scenarios_genetic = generate_scenarios(self.profile_normal, ["Genetic/Familial Predisposition"])
        ids_genetic = [s.scenario_id for s in scenarios_genetic]
        self.assertIn("S_GENETIC_SCREEN", ids_genetic)

    def test_scenario_comparison(self) -> None:
        """Verifies pairwise scenario comparison outputs correct impact benefit details."""
        scenarios = [
            Scenario(scenario_id="S1", change="Stop smoking", expected_effect="high", reasoning="reason"),
            Scenario(scenario_id="S2", change="Reduce smoking", expected_effect="medium", reasoning="reason"),
            Scenario(scenario_id="S3", change="Increase exercise", expected_effect="medium", reasoning="reason"),
        ]

        comparisons = compare_scenarios(scenarios)
        self.assertEqual(len(comparisons), 2)

        # First comparison: high (S1) vs medium (S2) -> S1 is higher impact
        self.assertEqual(comparisons[0].scenario_a, "S1")
        self.assertEqual(comparisons[0].scenario_b, "S2")
        self.assertIn("higher expected risk reduction benefit", comparisons[0].higher_impact)

        # Second comparison: medium (S2) vs medium (S3) -> comparable benefits
        self.assertEqual(comparisons[1].scenario_a, "S2")
        self.assertEqual(comparisons[1].scenario_b, "S3")
        self.assertIn("comparable expected risk reduction benefits", comparisons[1].higher_impact)

    def test_counterfactual_package_creation(self) -> None:
        """Verifies successful CounterfactualPackage schema creation."""
        scenarios = generate_scenarios(self.profile_normal, ["Tobacco Smoke Exposure"])
        comparisons = compare_scenarios(scenarios)

        package = create_counterfactual_package(scenarios, comparisons)
        self.assertIsInstance(package, CounterfactualPackage)
        self.assertEqual(len(package.scenarios), len(scenarios))
        self.assertEqual(len(package.comparisons), len(comparisons))

    def test_empty_driver_cases(self) -> None:
        """Verifies correct fallback scenarios for high BMI and healthy BMI with empty drivers."""
        # Healthy BMI fallback -> fitness + diet
        scenarios_fallback = generate_scenarios(self.profile_normal, [])
        ids_fallback = [s.scenario_id for s in scenarios_fallback]
        self.assertIn("S_FITNESS", ids_fallback)
        self.assertIn("S_DIET", ids_fallback)

        # High BMI fallback -> weight loss proposal included
        scenarios_bmi = generate_scenarios(self.profile_high_bmi, [])
        ids_bmi = [s.scenario_id for s in scenarios_bmi]
        self.assertIn("S_WEIGHT_LOSS", ids_bmi)

    def test_multi_driver_cases(self) -> None:
        """Verifies scenario generation when multiple risk drivers are provided simultaneously."""
        scenarios = generate_scenarios(self.profile_normal, ["Tobacco Smoke Exposure", "UV/Sun Exposure"])
        ids = [s.scenario_id for s in scenarios]
        self.assertIn("S_SMOKE_STOP", ids)
        self.assertIn("S_SUN_PROTECT", ids)

        # Check signature compatibility with CausalityPackage
        caus_pkg = CausalityPackage(
            ranked_contributors=[],
            primary_drivers=["Tobacco Smoke Exposure", "UV/Sun Exposure"],
            causal_confidence="medium"
        )
        scenarios_pkg = generate_scenarios(self.profile_normal, caus_pkg)
        ids_pkg = [s.scenario_id for s in scenarios_pkg]
        self.assertEqual(ids, ids_pkg)


if __name__ == "__main__":
    unittest.main()
