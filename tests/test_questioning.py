import unittest
from schemas.contracts import PatientProfile, EvidencePackage, SkepticPackage
from tools.questioning import generate_followup_questions
from tools.synthesis import generate_final_report


class TestAdaptiveClinicalQuestioning(unittest.TestCase):
    """Test suite for the Adaptive Clinical Questioning Engine (Sprint 3 Milestone 4)."""

    def setUp(self) -> None:
        """Set up patient profiles for testing."""
        # 1. Healthy Profile
        self.profile_healthy = PatientProfile(
            session_id="session_q_healthy",
            age=25,
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

        # 2. Smoking Profile
        self.profile_smoking = PatientProfile(
            session_id="session_q_smoking",
            age=45,
            sex="male",
            bmi=24.0,
            smoking_status="active",
            smoking_years=15,
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

        # 3. BRCA Profile
        self.profile_brca = PatientProfile(
            session_id="session_q_brca",
            age=32,
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
            known_mutations=["BRCA1"],
            previous_cancer_history=False,
        )

        # 4. Family History Profile
        self.profile_family = PatientProfile(
            session_id="session_q_family",
            age=38,
            sex="female",
            bmi=23.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=True,
            known_mutations=[],
            previous_cancer_history=False,
        )

        # 5. Obesity Profile
        self.profile_obese = PatientProfile(
            session_id="session_q_obese",
            age=50,
            sex="male",
            bmi=34.0,
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

        # 6. Mixed Profile (All factors active to test prioritization and max limit)
        self.profile_mixed = PatientProfile(
            session_id="session_q_mixed",
            age=55,
            sex="female",
            bmi=35.0,
            smoking_status="active",
            smoking_years=25,
            alcohol_use="heavy",
            physical_activity="low",
            diet_quality="low",
            sun_exposure="high",
            occupation="construction",
            environmental_exposure=["asbestos"],
            family_history=True,
            known_mutations=["BRCA2"],
            previous_cancer_history=True,
        )

        self.dummy_evidence = EvidencePackage(risk_factors=[], citations=[], retrieved_documents=[])

    def test_healthy_profile_receives_no_questions(self) -> None:
        """Verifies that a healthy profile does not receive any follow-up questions."""
        questions = generate_followup_questions(self.profile_healthy, self.dummy_evidence, [])
        self.assertEqual(len(questions), 0)

    def test_smoking_profile_questions(self) -> None:
        """Verifies smoking-specific questions, rationales, and qualitative impact labels."""
        questions = generate_followup_questions(self.profile_smoking, self.dummy_evidence, [])
        self.assertTrue(len(questions) > 0)
        q_texts = [q.question for q in questions]
        self.assertIn("How many cigarettes do you smoke per day?", q_texts)
        self.assertIn("How many years have you been smoking?", q_texts)
        self.assertIn("Have you made any quit attempts in the past year?", q_texts)
        
        # Verify rationales and impacts are populated
        for q in questions:
            self.assertTrue(len(q.rationale) > 0)
            self.assertIn(q.impact, ["Significantly improve confidence", "Moderately improve confidence"])

    def test_brca_profile_questions(self) -> None:
        """Verifies BRCA-specific questions regarding genetic confirmation and counseling."""
        questions = generate_followup_questions(self.profile_brca, self.dummy_evidence, [])
        q_texts = [q.question for q in questions]
        self.assertIn("Was your genetic mutation (e.g. BRCA1/BRCA2) clinically confirmed by a certified lab test?", q_texts)
        self.assertIn("Have you completed genetic counseling to discuss hereditary risk management?", q_texts)

    def test_family_history_profile_questions(self) -> None:
        """Verifies family-history-specific lineage questions."""
        questions = generate_followup_questions(self.profile_family, self.dummy_evidence, [])
        q_texts = [q.question for q in questions]
        self.assertIn("Which specific first-degree relatives have been diagnosed with cancer?", q_texts)
        self.assertIn("At what age were your relatives diagnosed with cancer?", q_texts)
        self.assertIn("What specific types of cancer were diagnosed in your family?", q_texts)

    def test_obesity_profile_questions(self) -> None:
        """Verifies obesity-specific weight trend, waist circumference, and exercise questions."""
        questions = generate_followup_questions(self.profile_obese, self.dummy_evidence, [])
        q_texts = [q.question for q in questions]
        self.assertIn("What is your current weight trend over the past 6 to 12 months?", q_texts)
        self.assertIn("What is your waist circumference?", q_texts)
        self.assertIn("What is your typical exercise frequency and intensity?", q_texts)

    def test_mixed_profile_limit_and_prioritization(self) -> None:
        """Verifies that mixed profiles cap follow-up questions at 5, prioritized by impact."""
        questions = generate_followup_questions(self.profile_mixed, self.dummy_evidence, [])
        self.assertEqual(len(questions), 5)
        
        # Verify Significant impact questions are placed first
        impacts = [q.impact for q in questions]
        # Sort impact checks (Significant should precede Moderate)
        for i in range(len(impacts) - 1):
            if impacts[i] == "Moderately improve confidence":
                self.assertNotEqual(impacts[i+1], "Significantly improve confidence")

    def test_report_compilation_formatting(self) -> None:
        """Verifies that synthesized report formatting displays the questions section correctly."""
        from schemas.contracts import CausalityPackage, CounterfactualPackage
        skeptic = SkepticPackage(
            confidence="medium",
            uncertainties=[],
            limitations=[],
            conflicting_evidence=[],
            missing_information=[],
            recommended_questions=generate_followup_questions(self.profile_smoking, self.dummy_evidence, [])
        )
        report = generate_final_report(
            self.dummy_evidence,
            CausalityPackage(ranked_contributors=[], primary_drivers=[], causal_confidence="medium"),
            CounterfactualPackage(scenarios=[], comparisons=[]),
            skeptic,
            profile=self.profile_smoking
        )
        self.assertIn("### 8. Recommended Follow-up Questions", report.counterfactual_summary)
        self.assertIn("How many cigarettes do you smoke per day?", report.counterfactual_summary)


if __name__ == "__main__":
    unittest.main()
