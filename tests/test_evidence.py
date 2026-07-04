"""Unit tests for Stage 8 mock evidence pipeline.
"""

import unittest
from schemas.contracts import PatientProfile, RiskFactor, Citation, EvidencePackage
from tools.retrieval import retrieve_documents
from tools.evidence_ranking import (
    extract_risk_factors,
    extract_citations,
    rank_evidence,
    score_source_quality,
)


class TestEvidencePipeline(unittest.TestCase):
    """Test suite for the deterministic mock evidence pipeline."""

    def setUp(self) -> None:
        """Set up patient profiles for testing."""
        self.profile_heavy = PatientProfile(
            session_id="session_heavy",
            age=62,
            sex="male",
            bmi=29.1,
            smoking_status="active",
            smoking_years=40,
            alcohol_use="heavy",
            physical_activity="low",
            diet_quality="low",
            sun_exposure="high",
            occupation="agriculture",
            environmental_exposure=["pesticides"],
            family_history=True,
            known_mutations=["BRCA2"],
            previous_cancer_history=False,
        )

        self.profile_clean = PatientProfile(
            session_id="session_clean",
            age=25,
            sex="female",
            bmi=21.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="student",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )

    def test_mock_document_retrieval(self) -> None:
        """Verifies keyword-based document retrieval and limits."""
        # 1. Smoking query
        docs_smoke = retrieve_documents("What are the risk factors of tobacco smoking?")
        self.assertTrue(len(docs_smoke) > 0)
        self.assertTrue(any("tobacco" in d.lower() or "smoke" in d.lower() for d in docs_smoke))

        # 2. Limit query results
        docs_limit = retrieve_documents("tobacco", limit=1)
        self.assertEqual(len(docs_limit), 1)

        # 3. Alcohol query
        docs_alcohol = retrieve_documents("impact of alcohol consumption")
        self.assertTrue(len(docs_alcohol) > 0)
        self.assertTrue(any("alcohol" in d.lower() for d in docs_alcohol))

        # 4. Fallback default results
        docs_fallback = retrieve_documents("something totally unrelated to oncology")
        self.assertEqual(len(docs_fallback), 2)
        self.assertTrue(any("baseline" in d.lower() or "general" in d.lower() for d in docs_fallback))

    def test_source_quality_scoring(self) -> None:
        """Verifies source scoring logic behaves deterministically."""
        self.assertEqual(score_source_quality("Nature Reviews Cancer"), 0.95)
        self.assertEqual(score_source_quality("New England Journal of Medicine (NEJM)"), 0.95)
        self.assertEqual(score_source_quality("PubMed Abstract #145"), 0.90)
        self.assertEqual(score_source_quality("The Lancet Oncology"), 0.90)
        self.assertEqual(score_source_quality("WHO Guidelines"), 0.85)
        self.assertEqual(score_source_quality("Centers for Disease Control (CDC)"), 0.80)
        self.assertEqual(score_source_quality("National Cancer Institute (NCI)"), 0.80)
        self.assertEqual(score_source_quality("American Cancer Society (ACS)"), 0.75)
        self.assertEqual(score_source_quality("Personal Blog of a Physician"), 0.50)

    def test_evidence_ranking(self) -> None:
        """Verifies sorting of RiskFactor objects by score in descending order."""
        factors = [
            RiskFactor(factor="A", evidence_strength="low", evidence_score=0.3, source_count=1),
            RiskFactor(factor="B", evidence_strength="high", evidence_score=0.95, source_count=10),
            RiskFactor(factor="C", evidence_strength="medium", evidence_score=0.7, source_count=5),
        ]
        ranked = rank_evidence(factors)
        self.assertEqual(ranked[0].factor, "B")
        self.assertEqual(ranked[1].factor, "C")
        self.assertEqual(ranked[2].factor, "A")

    def test_risk_factor_extraction_grounded(self) -> None:
        """Verifies that risk factor extraction is grounded when documents are provided."""
        # Clean profile should only extract baseline
        factors_clean = extract_risk_factors(self.profile_clean)
        self.assertEqual(len(factors_clean), 1)
        self.assertEqual(factors_clean[0].factor, "General Environmental Baseline")

        # Heavy profile with no documents (pure profile extraction)
        factors_heavy_profile = extract_risk_factors(self.profile_heavy)
        factors_heavy_names = [f.factor for f in factors_heavy_profile]
        self.assertIn("Tobacco Smoke Exposure", factors_heavy_names)
        self.assertIn("Age-related Cellular Senescence", factors_heavy_names)
        self.assertIn("Genetic/Familial Predisposition", factors_heavy_names)
        self.assertIn("UV/Sun Exposure", factors_heavy_names)
        self.assertIn("Alcohol Consumption Risk", factors_heavy_names)

        # Heavy profile grounded by smoking and sun documents (should NOT include genetics or age or alcohol)
        mock_docs = [
            "PubMed: Tobacco smoking is highly linked to carcinomas.",
            "WHO: Sun exposure and UV radiation damage cellular structures."
        ]
        factors_grounded = extract_risk_factors(self.profile_heavy, documents=mock_docs)
        grounded_names = [f.factor for f in factors_grounded]
        self.assertIn("Tobacco Smoke Exposure", grounded_names)
        self.assertIn("UV/Sun Exposure", grounded_names)
        self.assertNotIn("Genetic/Familial Predisposition", grounded_names)
        self.assertNotIn("Age-related Cellular Senescence", grounded_names)
        self.assertNotIn("Alcohol Consumption Risk", grounded_names)

    def test_evidence_package_generation(self) -> None:
        """Verifies the creation of an EvidencePackage schema object."""
        docs = retrieve_documents("tobacco smoking age")
        factors = extract_risk_factors(self.profile_heavy, documents=docs)
        citations = extract_citations([f.factor for f in factors], documents=docs)

        ev_package = EvidencePackage(
            risk_factors=factors,
            citations=citations,
            retrieved_documents=docs
        )

        self.assertIsInstance(ev_package, EvidencePackage)
        self.assertEqual(ev_package.retrieved_documents, docs)
        self.assertTrue(len(ev_package.risk_factors) > 0)
        self.assertTrue(len(ev_package.citations) > 0)

    def test_dynamic_citation_generation(self) -> None:
        """Verifies dynamic citation parsing from custom document strings."""
        docs = [
            "Nature Clinical Oncology (2021): Cellular aging is correlated with genetic mutations.",
            "American Cancer Society Guideline (2023): Healthy diet reduces cancer incidence by 20%."
        ]
        citations = extract_citations([], documents=docs)
        
        self.assertEqual(len(citations), 2)
        self.assertEqual(citations[0].source, "Nature Clinical Oncology")
        self.assertEqual(citations[0].year, 2021)
        self.assertTrue(citations[0].title.startswith("Cellular aging"))

        self.assertEqual(citations[1].source, "American Cancer Society Guideline")
        self.assertEqual(citations[1].year, 2023)
        self.assertTrue(citations[1].title.startswith("Healthy diet"))

    def test_brca1_generates_genetic_factors(self) -> None:
        """Verifies that a patient with BRCA1 mutation generates genetic-related risk factors."""
        from agents.evidence_agent import EvidenceAgent
        profile = PatientProfile(
            session_id="test_genetic_brca1",
            age=30,
            sex="female",
            bmi=22.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="medium",
            diet_quality="medium",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=["BRCA1"],
            previous_cancer_history=False
        )
        agent = EvidenceAgent()
        pkg = agent.run(profile)
        factors = [f.factor for f in pkg.risk_factors]
        self.assertIn("Genetic/Familial Predisposition", factors)

    def test_asbestos_generates_environmental_factors(self) -> None:
        """Verifies that a patient with asbestos exposure generates environmental-related factors."""
        from agents.evidence_agent import EvidenceAgent
        profile = PatientProfile(
            session_id="test_env_asbestos",
            age=30,
            sex="male",
            bmi=22.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="medium",
            diet_quality="medium",
            sun_exposure="low",
            occupation="construction",
            environmental_exposure=["asbestos"],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False
        )
        agent = EvidenceAgent()
        pkg = agent.run(profile)
        factors = [f.factor for f in pkg.risk_factors]
        self.assertTrue(len(pkg.risk_factors) > 0)
        self.assertTrue(any("Environmental" in f or "Baseline" in f for f in factors))

    def test_smoking_generates_tobacco_factors(self) -> None:
        """Verifies that active smoking generates tobacco-related factors."""
        from agents.evidence_agent import EvidenceAgent
        profile = PatientProfile(
            session_id="test_smoke_active",
            age=30,
            sex="male",
            bmi=22.0,
            smoking_status="active",
            smoking_years=10,
            alcohol_use="none",
            physical_activity="medium",
            diet_quality="medium",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False
        )
        agent = EvidenceAgent()
        pkg = agent.run(profile)
        factors = [f.factor for f in pkg.risk_factors]
        self.assertIn("Tobacco Smoke Exposure", factors)

    def test_citations_originate_from_retrieved_documents(self) -> None:
        """Verifies that retrieved citations originate from parsed retrieved documents."""
        from agents.evidence_agent import EvidenceAgent
        profile = PatientProfile(
            session_id="test_citation_source",
            age=60,
            sex="male",
            bmi=22.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="medium",
            diet_quality="medium",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False
        )
        agent = EvidenceAgent()
        pkg = agent.run(profile)
        
        self.assertTrue(len(pkg.citations) > 0)
        self.assertTrue(len(pkg.retrieved_documents) > 0)
        for cit in pkg.citations:
            found = False
            for doc in pkg.retrieved_documents:
                if cit.source.lower() in doc.lower() or cit.title[:20].lower() in doc.lower():
                    found = True
                    break
            self.assertTrue(found, f"Citation source '{cit.source}' or title '{cit.title}' was not found in retrieved documents.")

    def test_brca1_appears_in_reasoning(self) -> None:
        """Verifies that BRCA1 is present in the final report/reasoning output."""
        from agents.orchestrator_agent import OrchestratorAgent
        profile = PatientProfile(
            session_id="test_brca1_reasoning",
            age=35,
            sex="female",
            bmi=22.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="medium",
            diet_quality="medium",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=["BRCA1"],
            previous_cancer_history=False
        )
        orchestrator = OrchestratorAgent()
        state = orchestrator.run(profile)
        
        self.assertIn("Genetic/Familial Predisposition", state.final_report.top_contributors)

    def test_asbestos_appears_in_reasoning(self) -> None:
        """Verifies that asbestos exposure is reflected in the final report/reasoning output."""
        from agents.orchestrator_agent import OrchestratorAgent
        profile = PatientProfile(
            session_id="test_asbestos_reasoning",
            age=35,
            sex="male",
            bmi=22.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="medium",
            diet_quality="medium",
            sun_exposure="low",
            occupation="construction",
            environmental_exposure=["asbestos"],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False
        )
        orchestrator = OrchestratorAgent()
        state = orchestrator.run(profile)
        
        self.assertIn("Environmental Carcinogen Exposure", state.final_report.top_contributors)

    def test_fallback_factor_not_added_when_valid_factors_exist(self) -> None:
        """Verifies that General Environmental Factors fallback is not added when genetic/environmental factors exist."""
        from agents.evidence_agent import EvidenceAgent
        profile = PatientProfile(
            session_id="test_no_fallback_when_valid_exist",
            age=35,
            sex="female",
            bmi=22.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="medium",
            diet_quality="medium",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=["BRCA1"],
            previous_cancer_history=False
        )
        agent = EvidenceAgent()
        pkg = agent.run(profile)
        factors = [f.factor for f in pkg.risk_factors]
        
        self.assertIn("Genetic/Familial Predisposition", factors)
        self.assertNotIn("General Environmental Factors", factors)

    def test_obesity_factor_extraction(self) -> None:
        """Verifies Obesity-related Cancer Risk extraction."""
        from agents.evidence_agent import EvidenceAgent
        profile = PatientProfile(
            session_id="test_obesity",
            age=30,
            sex="female",
            bmi=35.0,
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
            previous_cancer_history=False
        )
        agent = EvidenceAgent()
        pkg = agent.run(profile)
        factors = [f.factor for f in pkg.risk_factors]
        self.assertIn("Obesity-related Cancer Risk", factors)

    def test_physical_inactivity_factor_extraction(self) -> None:
        """Verifies Physical Inactivity factor extraction."""
        from agents.evidence_agent import EvidenceAgent
        profile = PatientProfile(
            session_id="test_inactivity",
            age=30,
            sex="female",
            bmi=22.0,
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
            previous_cancer_history=False
        )
        agent = EvidenceAgent()
        pkg = agent.run(profile)
        factors = [f.factor for f in pkg.risk_factors]
        self.assertIn("Physical Inactivity", factors)

    def test_poor_diet_factor_extraction(self) -> None:
        """Verifies Poor Dietary Pattern factor extraction."""
        from agents.evidence_agent import EvidenceAgent
        profile = PatientProfile(
            session_id="test_diet",
            age=30,
            sex="female",
            bmi=22.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="low",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False
        )
        agent = EvidenceAgent()
        pkg = agent.run(profile)
        factors = [f.factor for f in pkg.risk_factors]
        self.assertIn("Poor Dietary Pattern", factors)

    def test_previous_cancer_factor_extraction(self) -> None:
        """Verifies Previous Malignancy History factor extraction."""
        from agents.evidence_agent import EvidenceAgent
        profile = PatientProfile(
            session_id="test_prev_cancer",
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
            previous_cancer_history=True
        )
        agent = EvidenceAgent()
        pkg = agent.run(profile)
        factors = [f.factor for f in pkg.risk_factors]
        self.assertIn("Previous Malignancy History", factors)

    def test_multiple_simultaneous_factors(self) -> None:
        """Verifies multiple simultaneous factors are extracted and ranked correctly."""
        from agents.evidence_agent import EvidenceAgent
        profile = PatientProfile(
            session_id="test_multi",
            age=30,
            sex="female",
            bmi=32.0,
            smoking_status="active",
            smoking_years=10,
            alcohol_use="none",
            physical_activity="low",
            diet_quality="low",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=True
        )
        agent = EvidenceAgent()
        pkg = agent.run(profile)
        factors = [f.factor for f in pkg.risk_factors]
        self.assertIn("Tobacco Smoke Exposure", factors)
        self.assertIn("Obesity-related Cancer Risk", factors)
        self.assertIn("Physical Inactivity", factors)
        self.assertIn("Poor Dietary Pattern", factors)
        self.assertIn("Previous Malignancy History", factors)

        # Check ranking order by evidence score (dynamically boosted and adjusted)
        scores = {f.factor: f.evidence_score for f in pkg.risk_factors}
        self.assertAlmostEqual(scores["Tobacco Smoke Exposure"], 1.0)
        self.assertAlmostEqual(scores["Previous Malignancy History"], 0.7225)
        self.assertAlmostEqual(scores["Obesity-related Cancer Risk"], 0.83)
        self.assertAlmostEqual(scores["Physical Inactivity"], 0.66)
        self.assertAlmostEqual(scores["Poor Dietary Pattern"], 0.81)

        # Verify descending sort order in the package
        for i in range(len(pkg.risk_factors) - 1):
            self.assertTrue(pkg.risk_factors[i].evidence_score >= pkg.risk_factors[i+1].evidence_score)

    def test_sex_retrieval_context(self) -> None:
        """Verifies that sex context is appended to BRCA mutation query."""
        from agents.evidence_agent import EvidenceAgent
        profile_female = PatientProfile(
            session_id="test_female_brca",
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
            known_mutations=["BRCA1"],
            previous_cancer_history=False
        )
        agent = EvidenceAgent()
        # Mock retrieve_documents to assert the query content
        from unittest.mock import patch
        with patch("agents.evidence_agent.retrieve_documents") as mock_retrieve:
            mock_retrieve.return_value = []
            agent.run(profile_female)
            # Assert called with query containing female context
            args, kwargs = mock_retrieve.call_args
            self.assertIn("female genetic mutations BRCA", args[0])


if __name__ == "__main__":
    unittest.main()


