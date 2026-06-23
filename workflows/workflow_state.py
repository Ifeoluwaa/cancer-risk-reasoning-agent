"""Workflow state utilities for CRRA.

Wraps the core WorkflowState schema and provides functions for initialization.
"""

from schemas.contracts import WorkflowState, PatientProfile


def initialize_state(session_id: str, profile: PatientProfile) -> WorkflowState:
    """Initializes the workflow state container.

    Args:
        session_id: The unique session identifier.
        profile: The patient profile input.

    Returns:
        A WorkflowState object ready for execution.
    """
    return WorkflowState(
        session_id=session_id,
        patient_profile=profile,
        current_step="START",
        status="PENDING",
    )
