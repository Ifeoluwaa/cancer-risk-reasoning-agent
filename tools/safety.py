"""safety.py

Safety tools for screening inputs, removing PII, and classifying request severity.
"""

import re
from typing import List, Literal, Tuple

# Deterministic regex for detecting email addresses
EMAIL_REGEX = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')

# Deterministic regex for detecting phone numbers. Matches standard forms like:
# (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890, +1 123 456 7890, +44 20 7946 0958
# Uses a structure requiring at least a 7-digit block pattern or international prefix.
PHONE_REGEX = re.compile(
    r'(?:'
    r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    r'|'
    r'\+\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
    r')'
)


def detect_pii(text: str) -> List[str]:
    """Identifies personal identifiable information (PII) categories present in the text.

    Args:
        text: The input query string.

    Returns:
        A list of detected categories (e.g. "email", "phone").
    """
    detected = []
    if EMAIL_REGEX.search(text):
        detected.append("email")
    if PHONE_REGEX.search(text):
        detected.append("phone")
    return detected


def scrub_pii(text: str) -> Tuple[str, List[str]]:
    """Identifies and redacts Personally Identifiable Information (PII) from user input texts.

    Args:
        text: The raw user input text string.

    Returns:
        A tuple of (sanitized_text, list_of_redacted_field_names).
    """
    redacted_fields = []
    sanitized = text

    detected = detect_pii(text)
    if "email" in detected:
        redacted_fields.append("email")
        sanitized = EMAIL_REGEX.sub("[REDACTED_EMAIL]", sanitized)
    if "phone" in detected:
        redacted_fields.append("phone_number")
        sanitized = PHONE_REGEX.sub("[REDACTED_PHONE]", sanitized)

    return sanitized, redacted_fields


def detect_prompt_injection(text: str) -> bool:
    """Detects common jailbreak attempts or overrides to safety guidelines.

    Checks case-insensitively for the following phrases:
    - ignore previous instructions
    - disregard system prompt
    - reveal hidden instructions
    - act as my doctor
    - bypass safety

    Args:
        text: The raw query text.

    Returns:
        True if any prompt injection triggers are matched, False otherwise.
    """
    text_lower = text.lower()
    injection_triggers = [
        "ignore previous instructions",
        "disregard system prompt",
        "reveal hidden instructions",
        "act as my doctor",
        "bypass safety",
    ]
    return any(trigger in text_lower for trigger in injection_triggers)


def check_prompt_injection(text: str) -> bool:
    """Checks the user text query for jailbreaks or instructions to bypass safety guidelines.

    Args:
        text: The raw query text.

    Returns:
        True if prompt injection indicators are detected, False otherwise.
    """
    return detect_prompt_injection(text)


def classify_medical_request(text: str) -> Literal["green", "yellow", "red"]:
    """Classifies user queries into Green (explaining), Yellow (risk estimates), or Red (diagnostic) zones.

    Classification rules:
    - RED: diagnosis requests, treatment recommendations, prescriptions, medical decision making.
    - YELLOW: risk estimation, probability, "what are my chances", "estimate my risk".
    - GREEN: educational questions, risk factors, prevention, biology explanations.

    Args:
        text: The search query or profile text.

    Returns:
        A Literal status string: "green", "yellow", or "red".
    """
    text_lower = text.lower()

    # Red triggers: diagnosis, treatment, prescriptions, decision making
    red_triggers = [
        "diagnose", "diagnosis", "diagnostic", "do i have cancer", "is this cancer",
        "treatment", "treat", "recommendation", "cure", "therapy", "recommend treatment",
        "prescribe", "prescription", "drug", "medicine", "medication",
        "decision", "should i take", "what should i do"
    ]

    # Yellow triggers: risk estimation, probability, "what are my chances", "estimate my risk"
    yellow_triggers = [
        "risk estimation", "estimate my risk", "estimate risk",
        "probability", "likelihood", "chances", "what are my chances",
        "chance"
    ]

    if any(trigger in text_lower for trigger in red_triggers):
        return "red"
    if any(trigger in text_lower for trigger in yellow_triggers):
        return "yellow"

    return "green"

