# Security Architecture

## Purpose

Prevent unsafe outputs, prompt injection, and leakage of sensitive information.

---

# Security Agent Responsibilities

1. Detect PII
2. Detect prompt injection
3. Classify medical requests
4. Block unsafe workflows

---

# PII Detection

The following information must be removed before processing:

* Names
* Emails
* Phone numbers
* Addresses
* Account identifiers

The Security Agent should record all redacted fields.

---

# Prompt Injection Protection

Examples:

* Ignore previous instructions
* Bypass restrictions
* Diagnose cancer
* Recommend treatment regardless of policy

Detection results:

* Flag event
* Prevent downstream execution
* Route to safe response

---

# Request Classification

## Green

Allowed

Examples:

* Explain contributors
* Explain evidence
* Compare scenarios

Action:

* Continue workflow

---

## Yellow

Warning Required

Examples:

* Estimate my cancer risk
* Tell me my chances

Action:

* Return educational response
* Include warning

---

## Red

Blocked

Examples:

* Diagnose cancer
* Prescribe treatment
* Recommend medication

Action:

* Block workflow
* Return safe refusal

---

# Safety Rules

The system must never:

* Diagnose cancer
* Predict cancer probability
* Recommend treatment
* Replace healthcare professionals

The system may:

* Explain contributors
* Explain evidence
* Explain uncertainty
* Explore hypothetical scenarios

---

# Security Logging

Track:

* Request type
* Injection detection
* PII detection
* Safety status

Store logs for evaluation and auditing.
