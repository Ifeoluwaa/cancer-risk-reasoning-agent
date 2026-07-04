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
    """Test suite for patient-specific counterfactual reasoning in tools/counterfactuals.py."""

    def setUp(self) -> None:
        """Set up standard objects for testing."""
        self.profile_clean = PatientProfile(
            session_id="session_clean",
            age=30,
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

        self.profile_active = PatientProfile(
            session_id="session_active",
            age=55,
            sex="male",
            bmi=32.0,
            smoking_status="active",
            smoking_years=20,
            alcohol_use="heavy",
            physical_activity="low",
            diet_quality="low",
            sun_exposure="high",
            occupation="construction",
            environmental_exposure=["asbestos"],
            family_history=True,
            known_mutations=["BRCA1"],
            previous_cancer_history=True,
        )

    def test_satisfied_interventions_excluded(self) -> None:
        """Verifies that clean profile returns only wellness maintenance and no modifiable changes."""
        scenarios = generate_scenarios(self.profile_clean, [])
        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].scenario_id, "S_MAINTAIN")
        self.assertIn("Maintain current healthy lifestyle", scenarios[0].change)

    def test_modifiable_drivers_prioritized(self) -> None:
        """Verifies that modifiable drivers from primary_drivers are generated first."""
        # Active profile has all modifiable factors. Pass Obesity and Alcohol as primary drivers.
        scenarios = generate_scenarios(
            self.profile_active, 
            ["Obesity-related Cancer Risk", "Alcohol Consumption Risk"]
        )
        self.assertTrue(len(scenarios) > 0)
        # Check that S_WEIGHT_LOSS and S_ALCOHOL_STOP/LIMIT are first in the list
        first_few_ids = [s.scenario_id for s in scenarios[:3]]
        self.assertIn("S_WEIGHT_LOSS", first_few_ids)
        self.assertIn("S_ALCOHOL_STOP", first_few_ids)

    def test_non_modifiable_drivers_do_not_generate_scenarios(self) -> None:
        """Verifies that non-modifiable drivers do not generate impossible counterfactuals."""
        # Non-modifiable drivers alone
        scenarios = generate_scenarios(
            self.profile_active, 
            ["Age-related Cellular Senescence", "Genetic/Familial Predisposition", "Previous Malignancy History"]
        )
        # Should fall back to general modifiable unsatisfied factors in the profile (e.g. smoking, bmi, etc.)
        ids = [s.scenario_id for s in scenarios]
        self.assertNotIn("S_GENETIC_SCREEN", ids)
        self.assertNotIn("S_CELL_ANTIOXIDANT", ids)
        # Should include modifiable ones like smoking
        self.assertIn("S_SMOKE_STOP", ids)

    def test_patient_specific_explanatory_reasoning(self) -> None:
        """Verifies that reasoning fields contain selected reasons, risk reduction and non-modifiable notes."""
        scenarios = generate_scenarios(
            self.profile_active,
            ["Tobacco Smoke Exposure"]
        )
        self.assertTrue(len(scenarios) > 0)
        for s in scenarios:
            # Check selected explanation
            if s.scenario_id == "S_SMOKE_STOP":
                self.assertIn("Selected because you are an active smoker", s.reasoning)
                self.assertIn("halts the inhalation of carcinogens", s.reasoning)
            elif s.scenario_id == "S_SMOKE_HALF":
                self.assertIn("Selected because you are an active smoker", s.reasoning)
                self.assertIn("decreases the carcinogen exposure", s.reasoning.lower())
            # Check non-modifiable explanation since active profile has mutations, family history, etc.
            self.assertIn("Note: Your non-modifiable factors", s.reasoning)
            self.assertIn("establish a baseline risk", s.reasoning)

    def test_prioritization_explanation_in_reasoning(self) -> None:
        """Verifies that reasoning explains why higher-ranked interventions were prioritized."""
        scenarios = generate_scenarios(
            self.profile_active,
            ["Tobacco Smoke Exposure", "Obesity-related Cancer Risk"]
        )
        # S_WEIGHT_LOSS should explain why it is prioritized below Tobacco Smoke Exposure
        weight_loss_scenario = next(s for s in scenarios if s.scenario_id == "S_WEIGHT_LOSS")
        self.assertIn("prioritized below Tobacco Smoke Exposure", weight_loss_scenario.reasoning)

    def test_scenario_comparison(self) -> None:
        """Verifies pairwise scenario comparison outputs correct impact benefit details."""
        scenarios = [
            Scenario(scenario_id="S1", change="Stop smoking", expected_effect="high", reasoning="reason"),
            Scenario(scenario_id="S2", change="Reduce smoking", expected_effect="medium", reasoning="reason"),
        ]

        comparisons = compare_scenarios(scenarios)
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0].scenario_a, "S1")
        self.assertEqual(comparisons[0].scenario_b, "S2")
        self.assertIn("higher expected risk reduction benefit", comparisons[0].higher_impact)

    def test_counterfactual_package_creation(self) -> None:
        """Verifies successful CounterfactualPackage schema creation."""
        scenarios = generate_scenarios(self.profile_active, ["Tobacco Smoke Exposure"])
        comparisons = compare_scenarios(scenarios)

        package = create_counterfactual_package(scenarios, comparisons)
        self.assertIsInstance(package, CounterfactualPackage)
        self.assertEqual(len(package.scenarios), len(scenarios))
        self.assertEqual(len(package.comparisons), len(comparisons))


if __name__ == "__main__":
    unittest.main()
