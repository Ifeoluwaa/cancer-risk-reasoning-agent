"""validation.py

Validation tools for validating inputs and verifying schema contract compliance.
"""

from typing import Dict, Any
from pydantic import BaseModel, ValidationError
from schemas.contracts import PatientProfile


def validate_patient_profile(data: Dict[str, Any]) -> PatientProfile:
    """Validates raw JSON/dictionary profile input against the PatientProfile schema.

    Args:
        data: A dictionary containing patient inputs.

    Returns:
        A validated PatientProfile schema object.

    Raises:
        ValidationError: If the input data fails schema structure checks.
    """
    # Uses Pydantic's internal validation engine
    return PatientProfile(**data)


def validate_schema_instance(instance: BaseModel) -> bool:
    """Verifies that an instantiated model matches pydantic structural expectations.

    In future stages, this tool can perform extended sanity checks:
    1. Ensure no required fields are null/None.
    2. Confirm custom validation parameters (e.g. valid age ranges, non-negative numbers).

    Args:
        instance: The instantiated Pydantic BaseModel to inspect.

    Returns:
        True if valid, raises an exception or returns False otherwise.
    """
    try:
        # Check basic pydantic parsing integrity
        instance.model_validate(instance.model_dump())
        return True
    except (ValidationError, TypeError):
        return False
