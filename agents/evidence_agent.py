"""Evidence Agent implementation for CRRA.

Responsible for retrieving evidence, extracting risk factors,
and producing an EvidencePackage containing citations and risk factors.
"""

from typing import List
from schemas.contracts import PatientProfile, EvidencePackage, RiskFactor, Citation


class EvidenceAgent:
    """Evidence Agent that searches and ranks scientific evidence related to the patient profile."""

    def __init__(self) -> None:
        """Initialize the Evidence Agent."""
        pass

    def run(self, profile: PatientProfile, retrieved_docs: List[str]) -> EvidencePackage:
        """Retrieves and packages evidence and identified risk factors.

        Args:
            profile: The sanitized PatientProfile.
            retrieved_docs: The list of raw/retrieved document chunks or identifiers.

        Returns:
            An EvidencePackage containing identified risk factors and supporting citations.
        """
        # Formulate mock factors based on the profile
        factors = []
        citations = []

        if profile.smoking_status.lower() in ["active", "former"] or profile.smoking_years > 0:
            factors.append(
                RiskFactor(
                    factor="Tobacco Smoke Exposure",
                    evidence_strength="high",
                    evidence_score=0.95,
                    source_count=12,
                )
            )
            citations.append(
                Citation(
                    source="IARC Monograph",
                    title="Tobacco Smoke and Involuntary Smoking",
                    year=2004,
                )
            )

        if profile.age > 50:
            factors.append(
                RiskFactor(
                    factor="Age-related Cellular Senescence",
                    evidence_strength="high",
                    evidence_score=0.88,
                    source_count=8,
                )
            )
            citations.append(
                Citation(
                    source="Nature Reviews Cancer",
                    title="Ageing and cancer: the essential role of cellular senescence",
                    year=2011,
                )
            )

        # Default fallback factor if profile has no specific matches
        if not factors:
            factors.append(
                RiskFactor(
                    factor="General Environmental Factors",
                    evidence_strength="low",
                    evidence_score=0.30,
                    source_count=2,
                )
            )
            citations.append(
                Citation(
                    source="WHO Reports",
                    title="Global Health Risks",
                    year=2009,
                )
            )

        return EvidencePackage(
            risk_factors=factors,
            citations=citations,
            retrieved_documents=retrieved_docs or ["Mock document abstract from CDC/PubMed"],
        )
