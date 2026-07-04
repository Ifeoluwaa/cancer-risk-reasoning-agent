import unittest
from schemas.contracts import PatientProfile, RiskFactor, EvidencePackage, CausalityPackage, CounterfactualPackage, Citation
from tools.evidence_ranking import classify_evidence_quality, get_quality_multiplier, extract_risk_factors, extract_citations
from tools.skeptic import calculate_confidence, verify_evidence
from tools.synthesis import generate_final_report


class TestEvidenceQualityReasoning(unittest.TestCase):
    """Test suite for the Evidence Quality & Guideline-Aware Reasoning Engine."""

    def test_evidence_hierarchy_classification(self) -> None:
        """Verifies correct classification of retrieved documents into evidence hierarchy levels."""
        self.assertEqual(classify_evidence_quality("WHO Guidelines (2022): Tobacco use..."), "Clinical Guideline")
        self.assertEqual(classify_evidence_quality("IARC Monograph 114: processed meat..."), "Clinical Guideline")
        self.assertEqual(classify_evidence_quality("A systematic review and meta-analysis of cohort studies..."), "Systematic Review / Meta-analysis")
        self.assertEqual(classify_evidence_quality("A randomized controlled trial evaluating diet..."), "Randomized Controlled Trial")
        self.assertEqual(classify_evidence_quality("NEJM prospective cohort study of sun exposure..."), "Prospective Cohort")
        self.assertEqual(classify_evidence_quality("Case report of unusual skin mutation..."), "Case Report")
        self.assertEqual(classify_evidence_quality("General overview of baseline risk factors..."), "Background Reference")

    def test_quality_multipliers_ranking(self) -> None:
        """Verifies that stronger evidence has higher quality multipliers than weaker evidence."""
        self.assertTrue(get_quality_multiplier("Clinical Guideline") > get_quality_multiplier("Randomized Controlled Trial"))
        self.assertTrue(get_quality_multiplier("Systematic Review / Meta-analysis") > get_quality_multiplier("Prospective Cohort"))
        self.assertTrue(get_quality_multiplier("Prospective Cohort") > get_quality_multiplier("Case Report"))

    def test_dynamic_evidence_score_adjustment(self) -> None:
        """Verifies that risk factor evidence scores scale appropriately based on supporting document quality."""
        profile = PatientProfile(
            session_id="session_quality_score_adj",
            age=45,
            sex="female",
            bmi=32.0,
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
        
        # Scenario A: Obesity supported by Clinical Guideline (WHO Guidelines)
        docs_guideline = ["WHO Guidelines (2022): Obesity is associated with cancer."]
        factors_guideline = extract_risk_factors(profile, docs_guideline)
        obesity_g = next(f for f in factors_guideline if f.factor == "Obesity-related Cancer Risk")
        
        # Scenario B: Obesity supported by Case Report
        docs_case_report = ["Case report of metabolic obesity findings."]
        factors_case = extract_risk_factors(profile, docs_case_report)
        obesity_c = next(f for f in factors_case if f.factor == "Obesity-related Cancer Risk")
        
        # Guideline-supported score should be higher than case-report-supported score
        self.assertTrue(obesity_g.evidence_score > obesity_c.evidence_score)

    def test_dynamic_confidence_scoring_hierarchy(self) -> None:
        """Verifies that confidence levels reflect evidence quality (Guidelines/Meta-analyses boost, observational restricts)."""
        # Baseline setup
        rf = RiskFactor(factor="Tobacco Smoke Exposure", evidence_strength="high", evidence_score=0.90, source_count=5)
        evidence_guideline = EvidencePackage(
            risk_factors=[rf],
            citations=[
                Citation(source="WHO", title="Tobacco Guidelines", year=2022, evidence_quality="Clinical Guideline")
            ],
            retrieved_documents=["doc1", "doc2", "doc3", "doc4"]
        )
        causality = CausalityPackage(
            ranked_contributors=[],
            primary_drivers=["Tobacco Smoke Exposure"],
            causal_confidence="high"
        )
        
        # High-quality Guideline evidence
        conf_g = calculate_confidence(evidence_guideline, causality, [])
        self.assertEqual(conf_g, "high")
        
        # Low-quality Case Report evidence
        evidence_case = EvidencePackage(
            risk_factors=[rf],
            citations=[
                Citation(source="PubMed", title="A case report", year=2021, evidence_quality="Case Report")
            ],
            retrieved_documents=["doc1"]
        )
        conf_c = calculate_confidence(evidence_case, causality, ["Uncertainty"])
        self.assertEqual(conf_c, "medium")

    def test_skeptic_critique_weaker_evidence(self) -> None:
        """Verifies that SkepticAgent critiques evidence quality if no high-quality/randomized evidence is retrieved."""
        # Evidence relying only on case reports
        rf = RiskFactor(factor="Physical Inactivity", evidence_strength="medium", evidence_score=0.50, source_count=2)
        evidence = EvidencePackage(
            risk_factors=[rf],
            citations=[
                Citation(source="Journal", title="Case report of inactivity", year=2021, evidence_quality="Case Report")
            ],
            retrieved_documents=["doc1"]
        )
        
        limitations = verify_evidence(evidence)
        # Should include observational / randomized critique
        self.assertTrue(any("Reasoning relies primarily on observational literature" in l for l in limitations))


if __name__ == "__main__":
    unittest.main()
