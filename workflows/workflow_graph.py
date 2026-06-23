"""Workflow graph and execution engine for CRRA.

Coordinates agent sequence (Security -> Evidence -> Causality -> Counterfactual -> Skeptic -> Synthesis)
using routing rules to direct the flow or trigger a safe refusal block.
"""

from schemas.contracts import (
    WorkflowState,
    AggregatedAnalysis,
    FinalReport,
    SecurityPackage,
)
from agents.security_agent import SecurityAgent
from agents.evidence_agent import EvidenceAgent
from agents.causality_agent import CausalityAgent
from agents.counterfactual_agent import CounterfactualAgent
from agents.skeptic_agent import SkepticAgent
from agents.synthesis_agent import SynthesisAgent
from workflows.routing import determine_safety_route


class WorkflowGraph:
    """Executes the agents in the sequenced graph and performs safety routing."""

    def __init__(self) -> None:
        """Initialize all agent instances for node execution."""
        self.security_agent = SecurityAgent()
        self.evidence_agent = EvidenceAgent()
        self.causality_agent = CausalityAgent()
        self.counterfactual_agent = CounterfactualAgent()
        self.skeptic_agent = SkepticAgent()
        self.synthesis_agent = SynthesisAgent()

    def run(self, state: WorkflowState) -> WorkflowState:
        """Executes the graph sequence with safety-based conditional routing.

        Args:
            state: The initialized WorkflowState.

        Returns:
            The final completed/blocked WorkflowState.
        """
        state.status = "RUNNING"

        try:
            # 1. Security Check Node
            state.current_step = "SecurityAgent"
            security_pkg = self.security_agent.run(state.patient_profile)
            state.security_package = security_pkg

            # 2. Routing Decision
            route = determine_safety_route(security_pkg)

            if route == "REFUSE":
                return self._execute_safe_refusal(state)

            if route == "CONTINUE_WARNING":
                state.errors.append(
                    "WARNING: Yellow safety status. Request classified as risk estimation. "
                    "Educational insights will be provided, but diagnostic or prognostic advice is unavailable."
                )

            # Proceed with the clinical reasoning sequence
            clean_profile = security_pkg.clean_profile

            # 3. Evidence Node
            state.current_step = "EvidenceAgent"
            evidence_pkg = self.evidence_agent.run(
                clean_profile,
                retrieved_docs=["Mock CDC guidelines", "Mock PubMed abstract #14592"],
            )
            state.evidence_package = evidence_pkg

            # 4. Causality Node
            state.current_step = "CausalityAgent"
            causality_pkg = self.causality_agent.run(clean_profile, evidence_pkg)
            state.causality_package = causality_pkg

            # 5. Counterfactual Node
            state.current_step = "CounterfactualAgent"
            counterfactual_pkg = self.counterfactual_agent.run(
                clean_profile, causality_pkg.primary_drivers
            )
            state.counterfactual_package = counterfactual_pkg

            # 6. Skeptic Node
            state.current_step = "SkepticAgent"
            skeptic_pkg = self.skeptic_agent.run(
                evidence_pkg, causality_pkg, counterfactual_pkg
            )
            state.skeptic_package = skeptic_pkg

            # 7. Aggregation Step
            state.current_step = "OrchestrationAggregation"
            aggregated = AggregatedAnalysis(
                patient_profile=clean_profile,
                evidence_package=evidence_pkg,
                causality_package=causality_pkg,
                counterfactual_package=counterfactual_pkg,
                skeptic_package=skeptic_pkg,
            )
            state.aggregated_analysis = aggregated

            # 8. Synthesis Node
            state.current_step = "SynthesisAgent"
            report = self.synthesis_agent.run(aggregated)
            state.final_report = report

            # Finalize successfully
            state.current_step = "END"
            state.status = "COMPLETED"

        except Exception as e:
            state.status = "FAILED"
            state.errors.append(f"Orchestration failure at {state.current_step}: {str(e)}")

        return state

    def _execute_safe_refusal(self, state: WorkflowState) -> WorkflowState:
        """Executes the Safe Refusal Node when safety checks fail (RED status).

        Args:
            state: The active WorkflowState.

        Returns:
            The state with a safety disclaimer final report and blocked status.
        """
        state.current_step = "SafeRefusalNode"

        # Create refusal report
        refusal_report = FinalReport(
            top_contributors=[],
            evidence_summary="Request was blocked by the security system for safety reasons.",
            counterfactual_summary="No alternative scenarios can be generated for blocked requests.",
            limitations=["Safety assessment blocked processing due to non-educational topics."],
            confidence="low",
            citations=[],
            safety_disclaimer=(
                "Disclaimer: The requested query was classified as a diagnostic or treatment recommendation request. "
                "CRRA is designed for educational information about risk factors only. We cannot diagnose or "
                "recommend treatments. Please consult a qualified medical professional."
            ),
        )

        state.final_report = refusal_report
        state.status = "COMPLETED"  # Terminal status reached safely
        state.current_step = "END"
        return state
