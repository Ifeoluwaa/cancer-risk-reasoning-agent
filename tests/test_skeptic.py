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
)
from tools.skeptic import (
    find_uncertainties,
    verify_evidence,
    retrieve_conflicting_evidence,
    detect_missing_information,
    create_skeptic_package,
)


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
        # Contains high strength (tobacco) -> only self-reported warning
        lim_high = verify_evidence(self.evidence_high)
        self.assertIn("Occupational history is self-reported and lacks precise quantitative dosimetry.", lim_high)
        self.assertEqual(len(lim_high), 1)

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


if __name__ == "__main__":
    unittest.main()
