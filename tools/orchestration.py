"""orchestration.py

Orchestration tools for managing, tracing, and logging workflow status transitions.
"""

from typing import List
from schemas.contracts import WorkflowState, AggregatedAnalysis


def log_node_execution(
    session_id: str, node_name: str, status: str, errors: List[str]
) -> None:
    """Logs transition details and errors for a specific node execution.

    Args:
        session_id: The unique session identifier.
        node_name: The execution node/agent name.
        status: Node status (e.g. running, success, fail).
        errors: List of logged error messages.
    """
    log_line = (
        f"[Orchestrator LOG] Session: {session_id} | Node: {node_name} | "
        f"Status: {status} | Errors: {len(errors)}"
    )
    print(log_line)


def dispatch_tasks(state: WorkflowState) -> List[str]:
    """Determines the next execution steps or agent tasks to run based on the workflow state.

    Args:
        state: The current WorkflowState.

    Returns:
        A list of task/agent identifiers that are ready for execution.
    """
    if not state.patient_profile:
        return []

    if not state.security_package:
        return ["SecurityAgent"]

    # Handle RED safety classification (blocked requests)
    if state.security_package.safety_status == "red":
        if not state.final_report:
            return ["SafeRefusalNode"]
        return []

    # Standard clinical reasoning flow
    if not state.evidence_package:
        return ["EvidenceAgent"]

    if not state.causality_package:
        return ["CausalityAgent"]

    if not state.counterfactual_package:
        return ["CounterfactualAgent"]

    if not state.skeptic_package:
        return ["SkepticAgent"]

    if not state.aggregated_analysis:
        return ["OrchestrationAggregation"]

    if not state.final_report:
        return ["SynthesisAgent"]

    return []


def aggregate_outputs(state: WorkflowState) -> AggregatedAnalysis:
    """Aggregates outputs from the clinical reasoning agents in WorkflowState.

    Args:
        state: The current WorkflowState.

    Returns:
        An AggregatedAnalysis instance compiling the patient profile and all agent outputs.

    Raises:
        ValueError: If any intermediate packages are missing.
    """
    profile = None
    if state.security_package and state.security_package.clean_profile:
        profile = state.security_package.clean_profile
    elif state.patient_profile:
        profile = state.patient_profile

    if not profile:
        raise ValueError("Missing patient profile in workflow state.")

    if not state.evidence_package:
        raise ValueError("Missing evidence_package in workflow state.")

    if not state.causality_package:
        raise ValueError("Missing causality_package in workflow state.")

    if not state.counterfactual_package:
        raise ValueError("Missing counterfactual_package in workflow state.")

    if not state.skeptic_package:
        raise ValueError("Missing skeptic_package in workflow state.")

    return AggregatedAnalysis(
        patient_profile=profile,
        evidence_package=state.evidence_package,
        causality_package=state.causality_package,
        counterfactual_package=state.counterfactual_package,
        skeptic_package=state.skeptic_package,
    )


def validate_workflow_state(state: WorkflowState) -> bool:
    """Validates the logical consistency and safety constraints of the WorkflowState.

    Args:
        state: The active WorkflowState to validate.

    Returns:
        True if the state is logically consistent and valid.

    Raises:
        ValueError: If the workflow state contains logically inconsistent or missing data.
    """
    if not state.session_id:
        raise ValueError("WorkflowState must have a valid session_id.")

    allowed_statuses = {"PENDING", "RUNNING", "COMPLETED", "FAILED"}
    if state.status not in allowed_statuses:
        raise ValueError(f"WorkflowState status '{state.status}' is not one of {allowed_statuses}.")

    if state.status == "COMPLETED":
        if not state.security_package:
            raise ValueError("Completed WorkflowState must contain a security_package.")
        if not state.final_report:
            raise ValueError("Completed WorkflowState must contain a final_report.")

        # RED blocked request validation
        if state.security_package.safety_status == "red":
            if (state.evidence_package or state.causality_package or
                    state.counterfactual_package or state.skeptic_package or
                    state.aggregated_analysis):
                raise ValueError("Blocked RED request cannot contain intermediate analysis packages.")
        else:
            # GREEN / YELLOW successful flow validation
            if not state.evidence_package:
                raise ValueError("Completed successful WorkflowState is missing evidence_package.")
            if not state.causality_package:
                raise ValueError("Completed successful WorkflowState is missing causality_package.")
            if not state.counterfactual_package:
                raise ValueError("Completed successful WorkflowState is missing counterfactual_package.")
            if not state.skeptic_package:
                raise ValueError("Completed successful WorkflowState is missing skeptic_package.")
            if not state.aggregated_analysis:
                raise ValueError("Completed successful WorkflowState is missing aggregated_analysis.")

    return True

