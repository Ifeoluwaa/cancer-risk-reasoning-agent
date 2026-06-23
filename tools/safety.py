"""safety.py

Safety tools for screening inputs, removing PII, and classifying request severity.
"""

from typing import List, Literal, Tuple


def scrub_pii(text: str) -> Tuple[str, List[str]]:
    """Identifies and redacts Personally Identifiable Information (PII) from user input texts.

    In future stages, this tool will:
    1. Parse texts using regular expressions and Named Entity Recognition models.
    2. Replace names, emails, addresses, and phone numbers with redaction tags (e.g. [REDACTED_NAME]).
    3. Return the sanitized string and a log of redacted field categories.

    Args:
        text: The raw user input text string.

    Returns:
        A tuple of (sanitized_text, list_of_redacted_field_names).
    """
    redacted_fields = []
    sanitized = text

    # Minimal mock PII checks
    if "email" in text.lower():
        redacted_fields.append("email")
        sanitized = sanitized.replace("email", "[REDACTED_EMAIL]")
    if "phone" in text.lower():
        redacted_fields.append("phone_number")
        sanitized = sanitized.replace("phone", "[REDACTED_PHONE]")

    return sanitized, redacted_fields


def check_prompt_injection(text: str) -> bool:
    """Checks the user text query for jailbreaks or instructions to bypass safety guidelines.

    In future stages, this tool will:
    1. Compare incoming prompt text against heuristics/regex for instruction override.
    2. Optionally call a lightweight safety classifier model to flag malicious intent.

    Args:
        text: The raw query text.

    Returns:
        True if prompt injection indicators are detected, False otherwise.
    """
    text_lower = text.lower()
    # Mock checks for safety override triggers
    injection_triggers = [
        "ignore previous instructions",
        "bypass restriction",
        "override safety policy",
        "diagnose cancer anyway",
    ]
    return any(trigger in text_lower for trigger in injection_triggers)


def classify_medical_request(text: str) -> Literal["green", "yellow", "red"]:
    """Classifies user queries into Green (explaining), Yellow (risk estimates), or Red (diagnostic) zones.

    In future stages, this tool will:
    1. Query an LLM classifier to determine whether the user is asking for:
       - Green: Contributors of cancer risk, educational biology information.
       - Yellow: Risk estimation ("what are my chances?", "tell me my percentage risk").
       - Red: Diagnosis, treatment prescription, drug recommendations.

    Args:
        text: The search query or profile text.

    Returns:
        A Literal status string: "green", "yellow", or "red".
    """
    text_lower = text.lower()

    if "diagnose" in text_lower or "treatment" in text_lower or "prescribe" in text_lower or "red" in text_lower:
        return "red"
    elif "risk estimation" in text_lower or "estimate my risk" in text_lower or "yellow" in text_lower:
        return "yellow"
    else:
        return "green"
