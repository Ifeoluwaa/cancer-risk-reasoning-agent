"""Routing decisions for the CRRA workflow graph.

Routes the patient request based on the safety_status of the SecurityPackage.
"""

from typing import Literal
from schemas.contracts import SecurityPackage


def determine_safety_route(
    security_pkg: SecurityPackage,
) -> Literal["CONTINUE", "CONTINUE_WARNING", "REFUSE"]:
    """Determines the next path in the graph based on the safety status of the package.

    Args:
        security_pkg: The security package output by the SecurityAgent.

    Returns:
        A literal string route token: "CONTINUE", "CONTINUE_WARNING", or "REFUSE".
    """
    status = security_pkg.safety_status.upper()

    if status == "GREEN":
        return "CONTINUE"
    elif status == "YELLOW":
        return "CONTINUE_WARNING"
    elif status == "RED":
        return "REFUSE"
    else:
        # Default safety fallback in case of unrecognized status is to refuse
        return "REFUSE"
