"""Synthesis Agent implementation for CRRA.

Responsible for summarizing all analysis steps, listing citations and limitations,
and outputting the user-facing FinalReport with appropriate medical disclaimers.
"""

from schemas.contracts import AggregatedAnalysis, FinalReport


class SynthesisAgent:
    """Synthesis Agent that digests all analytical packages and produces a cohesive patient report."""

    def __init__(self) -> None:
        """Initialize the Synthesis Agent."""
        pass

    def run(self, analysis: AggregatedAnalysis) -> FinalReport:
        """Synthesizes the aggregated packages into a user-facing FinalReport.

        Args:
            analysis: The completed AggregatedAnalysis containing all previous agent packages.

        Returns:
            A FinalReport containing summaries, citations, limitations, and safety disclaimers.
        """
        from tools.synthesis import generate_final_report

        return generate_final_report(
            evidence=analysis.evidence_package,
            causality=analysis.causality_package,
            counterfactual=analysis.counterfactual_package,
            skeptic=analysis.skeptic_package,
            profile=analysis.patient_profile,
        )
