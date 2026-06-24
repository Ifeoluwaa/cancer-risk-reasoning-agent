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


if __name__ == "__main__":
    unittest.main()
