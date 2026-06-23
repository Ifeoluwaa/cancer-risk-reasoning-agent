"""Security Agent implementation for CRRA.

Responsible for checking patient profile inputs, detecting PII/prompt injection,
and producing a sanitized PatientProfile wrapped in a SecurityPackage.
Supports custom safety mock responses for testing safety routing.
"""

from schemas.contracts import PatientProfile, SecurityPackage


class SecurityAgent:
    """Security Agent that performs input validation, PII scrubbing, and request classification."""

    def __init__(self) -> None:
        """Initialize the Security Agent."""
        pass

    def run(self, profile: PatientProfile) -> SecurityPackage:
        """Processes the input PatientProfile and returns safety classification and clean profile.

        Recognizes safety keywords in occupation or session_id fields to mock safety routing:
        - Contains 'red': safety_status = 'red'
        - Contains 'yellow': safety_status = 'yellow'
        - Default: safety_status = 'green'

        Args:
            profile: The raw incoming PatientProfile.

        Returns:
            A SecurityPackage with safety details and a sanitized PatientProfile.
        """
        # Determine safety status based on mock triggers in the profile
        trigger_text = f"{profile.occupation} {profile.session_id}".lower()

        safety_status = "green"
        prompt_injection_detected = False
        pii_detected = False
        redacted_fields = []
        medical_request_type = "explanation"

        if "red" in trigger_text:
            safety_status = "red"
            prompt_injection_detected = True
            medical_request_type = "diagnosis"
        elif "yellow" in trigger_text:
            safety_status = "yellow"
            medical_request_type = "risk_estimation"
        else:
            # Standard green path: PII checking
            # Mock PII redaction if name field placeholder appears in session_id or occupation
            if "name" in trigger_text or "email" in trigger_text:
                pii_detected = True
                redacted_fields = ["session_id" if "email" in profile.session_id else "occupation"]

        return SecurityPackage(
            safety_status=safety_status,
            prompt_injection_detected=prompt_injection_detected,
            pii_detected=pii_detected,
            redacted_fields=redacted_fields,
            medical_request_type=medical_request_type,
            clean_profile=profile,
        )
