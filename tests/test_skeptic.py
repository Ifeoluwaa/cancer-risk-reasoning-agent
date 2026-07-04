"""Unit tests for Stage 11 skeptic reasoning tools.
"""

import unittest
from schemas.contracts import (
    PatientProfile,
    EvidencePackage,
    CausalityPackage,
    SkepticPackage,
    ConflictingEvidence,
    RiskFactor,
    CounterfactualPackage,
)
from tools.skeptic import (
    find_uncertainties,
    verify_evidence,
    retrieve_conflicting_evidence,
    detect_missing_information,
    create_skeptic_package,
)
from agents.skeptic_agent import SkepticAgent



class TestSkepticLayer(unittest.TestCase):
    """Test suite for deterministic skeptic auditing in tools/skeptic.py."""

    def setUp(self) -> None:
        """Set up standard objects for testing."""
        self.profile_minimal = PatientProfile(
            session_id="session_sk_1",
            age=30,
            sex="male",
            bmi=24.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="low",
            diet_quality="medium",
            sun_exposure="low",
            occupation="office",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )

        self.rf_tobacco = RiskFactor(factor="Tobacco Smoke Exposure", evidence_strength="high", evidence_score=0.95, source_count=12)
        self.rf_sun = RiskFactor(factor="UV/Sun Exposure", evidence_strength="medium", evidence_score=0.70, source_count=4)
        self.rf_alcohol = RiskFactor(factor="Alcohol Consumption Risk", evidence_strength="medium", evidence_score=0.65, source_count=3)
        self.rf_baseline = RiskFactor(factor="General Environmental Baseline", evidence_strength="low", evidence_score=0.25, source_count=2)

        self.evidence_high = EvidencePackage(
            risk_factors=[self.rf_tobacco, self.rf_sun],
            citations=[],
            retrieved_documents=[]
        )

        self.evidence_low = EvidencePackage(
            risk_factors=[self.rf_baseline],
            citations=[],
            retrieved_documents=[]
        )

        self.causality_high = CausalityPackage(
            ranked_contributors=[],
            primary_drivers=["Tobacco Smoke Exposure"],
            causal_confidence="high"
        )

        self.causality_low = CausalityPackage(
            ranked_contributors=[],
            primary_drivers=["General Environmental Baseline"],
            causal_confidence="low"
        )

    def test_uncertainty_detection(self) -> None:
        """Verifies detection of uncertainties based on evidence and causality packages."""
        # 1. High confidence, but missing genetics
        unc_1 = find_uncertainties(self.evidence_high, self.causality_high)
        self.assertIn("Causal link assumes default baseline without custom germline variant screening.", unc_1)

        # 2. Low confidence, missing genetics
        unc_2 = find_uncertainties(self.evidence_low, self.causality_low)
        self.assertIn("Causal link assumes default baseline without custom germline variant screening.", unc_2)
        self.assertIn("Causal confidence is low due to weak evidence scoring in primary drivers.", unc_2)

    def test_evidence_verification(self) -> None:
        """Verifies evidence limits and self-reported warnings extraction."""
        lim_high = verify_evidence(self.evidence_high)
        self.assertIn("Occupational history is self-reported and lacks precise quantitative dosimetry.", lim_high)
        self.assertEqual(len([l for l in lim_high if "Overall Critical Assessment:" not in l]), 1)

        # No high strength factors -> additional cohort limitations warning
        lim_low = verify_evidence(self.evidence_low)
        self.assertIn("All retrieved documents represent general epidemiological populations rather than high-relevance patient cohorts.", lim_low)

    def test_conflicting_evidence_generation(self) -> None:
        """Verifies retrieval of contradictory or nuanced epidemiological studies."""
        # Check tobacco and sun matches
        conf = retrieve_conflicting_evidence(self.evidence_high)
        factors = [c.factor for c in conf]
        self.assertIn("Tobacco Smoke Exposure", factors)
        self.assertIn("UV/Sun Exposure", factors)

        # Check alcohol match
        evidence_alc = EvidencePackage(risk_factors=[self.rf_alcohol], citations=[], retrieved_documents=[])
        conf_alc = retrieve_conflicting_evidence(evidence_alc)
        self.assertEqual(len(conf_alc), 1)
        self.assertEqual(conf_alc[0].factor, "Alcohol Consumption Risk")
        self.assertIn("Moderate cardioprotective claims", conf_alc[0].evidence)

    def test_detect_missing_information(self) -> None:
        """Verifies flagging of missing patient details (genetic, exposure, habits)."""
        # Missing genetics and environmental exposures
        missing = detect_missing_information(self.evidence_high, self.profile_minimal)
        self.assertIn("Genetic testing data (e.g. BRCA status is unconfirmed in general profiles)", missing)
        self.assertIn("Quantitative history of environmental exposure to industrial chemicals or radon.", missing)
        self.assertIn("Detailed dietary logs and cardiorespiratory fitness metrics.", missing)

    def test_skeptic_package_creation(self) -> None:
        """Verifies successful SkepticPackage schema instantiation."""
        package = create_skeptic_package(
            confidence="medium",
            uncertainties=["poorly quantified"],
            limitations=["self-reported"],
            conflicting_evidence=[],
            missing_information=[]
        )

        self.assertIsInstance(package, SkepticPackage)
        self.assertEqual(package.confidence, "medium")
        self.assertEqual(package.uncertainties, ["poorly quantified"])

    def test_dynamic_confidence_high(self) -> None:
        """Verifies that high-quality, high-quantity, grounded evidence yields HIGH confidence."""
        from tools.skeptic import calculate_confidence
        evidence = EvidencePackage(
            risk_factors=[
                RiskFactor(factor="Tobacco Smoke Exposure", evidence_strength="high", evidence_score=0.95, source_count=12),
                RiskFactor(factor="Genetic/Familial Predisposition", evidence_strength="medium", evidence_score=0.72, source_count=5),
            ],
            citations=[],
            retrieved_documents=["doc1", "doc2", "doc3", "doc4", "doc5", "doc6", "doc7", "doc8"]
        )
        causality = CausalityPackage(
            ranked_contributors=[],
            primary_drivers=["Tobacco Smoke Exposure"],
            causal_confidence="high"
        )
        # 0 active uncertainties (excluding fallback)
        conf = calculate_confidence(evidence, causality, ["Baseline environmental interactions are poorly quantified."])
        self.assertEqual(conf, "high")

    def test_dynamic_confidence_medium(self) -> None:
        """Verifies that moderate risk factors with some uncertainties yield MEDIUM confidence."""
        from tools.skeptic import calculate_confidence
        evidence = EvidencePackage(
            risk_factors=[
                RiskFactor(factor="Obesity-related Cancer Risk", evidence_strength="high", evidence_score=0.80, source_count=6),
            ],
            citations=[],
            retrieved_documents=["doc1", "doc2", "doc3", "doc4"]
        )
        causality = CausalityPackage(
            ranked_contributors=[],
            primary_drivers=["Obesity-related Cancer Risk"],
            causal_confidence="medium"
        )
        # 1 active uncertainty
        conf = calculate_confidence(evidence, causality, [
            "Causal link assumes default baseline without custom germline variant screening.",
            "Baseline environmental interactions are poorly quantified."
        ])
        self.assertEqual(conf, "medium")

    def test_dynamic_confidence_low(self) -> None:
        """Verifies that generic baseline risk with minimal docs and high uncertainties yields LOW confidence."""
        from tools.skeptic import calculate_confidence
        evidence = EvidencePackage(
            risk_factors=[
                RiskFactor(factor="General Environmental Baseline", evidence_strength="low", evidence_score=0.25, source_count=2),
            ],
            citations=[],
            retrieved_documents=["doc1"]
        )
        causality = CausalityPackage(
            ranked_contributors=[],
            primary_drivers=["General Environmental Baseline"],
            causal_confidence="low"
        )
        # 2 active uncertainties
        conf = calculate_confidence(evidence, causality, [
            "Causal link assumes default baseline without custom germline variant screening.",
            "Causal confidence is low due to weak evidence scoring in primary drivers.",
            "Baseline environmental interactions are poorly quantified."
        ])
        self.assertEqual(conf, "low")

    def test_dynamic_confidence_deterministic(self) -> None:
        """Verifies that identical inputs yield identical confidence levels (determinism)."""
        from tools.skeptic import calculate_confidence
        evidence = EvidencePackage(
            risk_factors=[
                RiskFactor(factor="Tobacco Smoke Exposure", evidence_strength="high", evidence_score=0.95, source_count=12),
            ],
            citations=[],
            retrieved_documents=["doc1", "doc2", "doc3", "doc4"]
        )
        causality = CausalityPackage(
            ranked_contributors=[],
            primary_drivers=["Tobacco Smoke Exposure"],
            causal_confidence="high"
        )
        conf1 = calculate_confidence(evidence, causality, [])
        conf2 = calculate_confidence(evidence, causality, [])
        self.assertEqual(conf1, conf2)

    def test_peer_review_strong_evidence(self) -> None:
        """Verifies peer review outputs for strong evidence (active smoker + BRCA1 + Asbestos)."""
        profile = PatientProfile(
            session_id="session_test_strong",
            age=55,
            sex="female",
            bmi=24.0,
            smoking_status="active",
            smoking_years=20,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="construction",
            environmental_exposure=["asbestos"],
            family_history=True,
            known_mutations=["BRCA1"],
            previous_cancer_history=False,
        )
        evidence = EvidencePackage(
            risk_factors=[
                RiskFactor(factor="Tobacco Smoke Exposure", evidence_strength="high", evidence_score=0.95, source_count=12),
                RiskFactor(factor="Genetic/Familial Predisposition", evidence_strength="medium", evidence_score=0.72, source_count=5),
                RiskFactor(factor="Environmental Carcinogen Exposure", evidence_strength="high", evidence_score=0.85, source_count=6)
            ],
            citations=[],
            retrieved_documents=["doc1", "doc2", "doc3", "doc4", "doc5", "doc6", "doc7", "doc8"]
        )
        causality = CausalityPackage(
            ranked_contributors=[],
            primary_drivers=["Tobacco Smoke Exposure", "Environmental Carcinogen Exposure"],
            causal_confidence="high"
        )
        
        # Test calling SkepticAgent with this context
        agent = SkepticAgent()
        pkg = agent.run(evidence, causality, CounterfactualPackage(scenarios=[], comparisons=[]), profile=profile)
        
        # Check overall critical assessment for strong drivers
        overall_critique = [l for l in pkg.limitations if "Overall Critical Assessment:" in l]
        self.assertTrue(len(overall_critique) > 0)
        self.assertIn("well grounded in multiple independent evidence sources", overall_critique[0])
        
        # Check missing patient info (intensity/dosimetry/family pedigree details)
        self.assertTrue(any("detailed family pedigree" in m.lower() for m in pkg.missing_information))
        self.assertTrue(any("detailed smoking intensity" in m.lower() for m in pkg.missing_information))

    def test_peer_review_weak_evidence(self) -> None:
        """Verifies peer review outputs for weak evidence (only fallback/generic)."""
        profile = PatientProfile(
            session_id="session_test_weak",
            age=30,
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
        evidence = EvidencePackage(
            risk_factors=[
                RiskFactor(factor="General Environmental Baseline", evidence_strength="low", evidence_score=0.25, source_count=2)
            ],
            citations=[],
            retrieved_documents=["doc1"]
        )
        causality = CausalityPackage(
            ranked_contributors=[],
            primary_drivers=["General Environmental Baseline"],
            causal_confidence="low"
        )
        
        agent = SkepticAgent()
        pkg = agent.run(evidence, causality, CounterfactualPackage(scenarios=[], comparisons=[]), profile=profile)
        
        # Check overall critical assessment for fallback
        overall_critique = [l for l in pkg.limitations if "Overall Critical Assessment:" in l]
        self.assertTrue(len(overall_critique) > 0)
        self.assertIn("generic environmental and baseline aging risk", overall_critique[0])
        
        # Check evidence limitation for fallback
        self.assertTrue(any("generic environmental baselines" in l.lower() for l in pkg.limitations))

    def test_peer_review_interacting_risk_factors(self) -> None:
        """Verifies confounder and alternative explanation detection for interacting risk factors (smoking + asbestos, obesity + inactivity)."""
        profile = PatientProfile(
            session_id="session_test_interacting",
            age=40,
            sex="male",
            bmi=32.0,
            smoking_status="active",
            smoking_years=20,
            alcohol_use="none",
            physical_activity="low",
            diet_quality="high",
            sun_exposure="low",
            occupation="construction",
            environmental_exposure=["asbestos"],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )
        evidence = EvidencePackage(
            risk_factors=[
                RiskFactor(factor="Tobacco Smoke Exposure", evidence_strength="high", evidence_score=0.95, source_count=12),
                RiskFactor(factor="Obesity-related Cancer Risk", evidence_strength="high", evidence_score=0.80, source_count=6),
                RiskFactor(factor="Environmental Carcinogen Exposure", evidence_strength="high", evidence_score=0.85, source_count=5),
                RiskFactor(factor="Physical Inactivity", evidence_strength="medium", evidence_score=0.60, source_count=3)
            ],
            citations=[],
            retrieved_documents=["doc1", "doc2", "doc3", "doc4"]
        )
        causality = CausalityPackage(
            ranked_contributors=[],
            primary_drivers=["Tobacco Smoke Exposure", "Obesity-related Cancer Risk"],
            causal_confidence="high"
        )
        
        agent = SkepticAgent()
        pkg = agent.run(evidence, causality, CounterfactualPackage(scenarios=[], comparisons=[]), profile=profile)
        
        # Check Potential Confounders are present
        self.assertTrue(any("synergistic interaction between tobacco smoke and asbestos" in u.lower() for u in pkg.uncertainties))
        self.assertTrue(any("obesity and low physical activity contribute via overlapping" in u.lower() for u in pkg.uncertainties))
        
        # Check Alternative Explanations are present
        self.assertTrue(any("smoking appears to be the dominant contributor; however, occupational asbestos" in u.lower() for u in pkg.uncertainties))
        self.assertTrue(any("obesity and low physical activity may jointly contribute" in u.lower() for u in pkg.uncertainties))


if __name__ == "__main__":
    unittest.main()
