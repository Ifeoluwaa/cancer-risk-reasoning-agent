"""Unit tests for the Stage 19 Streamlit UI helper functions and routing logic.
"""

import unittest
from app import map_form_to_profile, execute_pipeline
from schemas.contracts import PatientProfile


class TestWebUIIntegration(unittest.TestCase):
    """Verifies form mapping, workflow integration, and safety routing within the UI module."""

    def test_map_form_to_profile_defaults(self) -> None:
        """Verifies that empty form inputs correctly resolve to default profile values."""
        inputs = {}
        profile = map_form_to_profile(inputs)

        self.assertTrue(profile.session_id.startswith("ui_"))
        self.assertEqual(profile.age, 45)
        self.assertEqual(profile.sex, "male")
        self.assertEqual(profile.bmi, 24.5)
        self.assertEqual(profile.smoking_status, "never")
        self.assertEqual(profile.smoking_years, 0)
        self.assertEqual(profile.environmental_exposure, [])
        self.assertEqual(profile.known_mutations, [])
        self.assertFalse(profile.family_history)
        self.assertFalse(profile.previous_cancer_history)

    def test_map_form_to_profile_custom(self) -> None:
        """Verifies that custom form inputs are correctly parsed and mapped."""
        inputs = {
            "session_id": "test_session_99",
            "age": 60,
            "sex": "female",
            "bmi": 28.5,
            "smoking_status": "active",
            "smoking_years": 30,
            "alcohol_use": "moderate",
            "physical_activity": "low",
            "diet_quality": "low",
            "sun_exposure": "high",
            "occupation": "construction worker",
            "environmental_exposure": "asbestos, radon, lead",
            "known_mutations": "BRCA1, BRCA2",
            "family_history": True,
            "previous_cancer_history": True,
        }

        profile = map_form_to_profile(inputs)

        self.assertEqual(profile.session_id, "test_session_99")
        self.assertEqual(profile.age, 60)
        self.assertEqual(profile.sex, "female")
        self.assertEqual(profile.bmi, 28.5)
        self.assertEqual(profile.smoking_status, "active")
        self.assertEqual(profile.smoking_years, 30)
        self.assertEqual(profile.environmental_exposure, ["asbestos", "radon", "lead"])
        self.assertEqual(profile.known_mutations, ["BRCA1", "BRCA2"])
        self.assertTrue(profile.family_history)
        self.assertTrue(profile.previous_cancer_history)

    def test_execute_pipeline_green(self) -> None:
        """Verifies that a standard green profile runs the entire reasoning sequence successfully."""
        inputs = {
            "session_id": "test_ui_green",
            "age": 50,
            "sex": "male",
            "bmi": 23.0,
            "smoking_status": "never",
            "smoking_years": 0,
            "alcohol_use": "none",
            "physical_activity": "high",
            "diet_quality": "high",
            "sun_exposure": "low",
            "occupation": "software developer",
            "environmental_exposure": "",
            "known_mutations": "",
            "family_history": False,
            "previous_cancer_history": False,
        }

        profile = map_form_to_profile(inputs)
        state = execute_pipeline(profile)

        self.assertEqual(state.status, "COMPLETED")
        self.assertEqual(state.security_package.safety_status, "green")
        self.assertIsNotNone(state.final_report)
        self.assertGreater(len(state.final_report.top_contributors), 0)

    def test_execute_pipeline_yellow_warning(self) -> None:
        """Verifies that a profile containing 'yellow' triggers the warning and completes execution."""
        inputs = {
            "session_id": "test_ui_yellow",
            "age": 50,
            "sex": "male",
            "bmi": 23.0,
            "smoking_status": "never",
            "smoking_years": 0,
            "alcohol_use": "none",
            "physical_activity": "high",
            "diet_quality": "high",
            "sun_exposure": "low",
            "occupation": "software developer",
            "environmental_exposure": "",
            "known_mutations": "",
            "family_history": False,
            "previous_cancer_history": False,
        }

        profile = map_form_to_profile(inputs)
        state = execute_pipeline(profile)

        self.assertEqual(state.status, "COMPLETED")
        self.assertEqual(state.security_package.safety_status, "yellow")
        self.assertTrue(any("WARNING:" in err for err in state.errors))
        self.assertIsNotNone(state.final_report)

    def test_execute_pipeline_red_refusal(self) -> None:
        """Verifies that a profile containing 'red' is refused and returns the safety refusal report."""
        inputs = {
            "session_id": "test_ui_red",
            "age": 50,
            "sex": "male",
            "bmi": 23.0,
            "smoking_status": "never",
            "smoking_years": 0,
            "alcohol_use": "none",
            "physical_activity": "high",
            "diet_quality": "high",
            "sun_exposure": "low",
            "occupation": "software developer",
            "environmental_exposure": "",
            "known_mutations": "",
            "family_history": False,
            "previous_cancer_history": False,
        }

        profile = map_form_to_profile(inputs)
        state = execute_pipeline(profile)

        self.assertEqual(state.status, "COMPLETED")
        self.assertEqual(state.security_package.safety_status, "red")
        self.assertEqual(state.current_step, "END")
        self.assertIsNotNone(state.final_report)
        self.assertEqual(len(state.final_report.top_contributors), 0)
        self.assertTrue("blocked" in state.final_report.evidence_summary.lower())
        self.assertTrue("Please consult a qualified medical professional" in state.final_report.safety_disclaimer)


if __name__ == "__main__":
    unittest.main()
