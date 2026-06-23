"""Orchestrator Agent implementation for CRRA.

Acts as a controller only. Delegates the multi-agent graph execution sequence
and safety-based routing to WorkflowGraph.
"""

from schemas.contracts import PatientProfile, WorkflowState
from workflows.workflow_state import initialize_state
from workflows.workflow_graph import WorkflowGraph


class OrchestratorAgent:
    """Orchestrator Agent that acts as a workflow controller, delegating execution to the WorkflowGraph."""

    def __init__(self) -> None:
        """Initialize the Orchestrator controller with the WorkflowGraph."""
        self.graph = WorkflowGraph()

    def run(self, profile: PatientProfile) -> WorkflowState:
        """Executes the complete multi-agent workflow via the WorkflowGraph.

        Args:
            profile: The incoming raw PatientProfile.

        Returns:
            A WorkflowState container populated with the execution results.
        """
        # Create initial state
        state = initialize_state(session_id=profile.session_id, profile=profile)

        # Delegate execution to the graph
        return self.graph.run(state)
