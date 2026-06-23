# Agent Contracts

## Purpose

This document defines the structured JSON contracts exchanged between agents. All agents must communicate through structured schemas rather than free-form text.

---

# PatientProfile

Input to the system.

Fields:

* session_id: str
* age: int
* sex: str
* bmi: float
* smoking_status: str
* smoking_years: int
* alcohol_use: str
* physical_activity: str
* diet_quality: str
* sun_exposure: str
* occupation: str
* environmental_exposure: list[str]
* family_history: bool
* known_mutations: list[str]
* previous_cancer_history: bool

---

# SecurityPackage

Produced by Security Agent.

Fields:

* safety_status: green | yellow | red
* prompt_injection_detected: bool
* pii_detected: bool
* redacted_fields: list[str]
* medical_request_type: str
* clean_profile: PatientProfile

---

# EvidencePackage

Produced by Evidence Agent.

Fields:

* risk_factors: list
* citations: list
* retrieved_documents: list

Risk Factor Structure:

* factor: str
* evidence_strength: high | medium | low
* evidence_score: float
* source_count: int

Citation Structure:

* source: str
* title: str
* year: int

---

# CausalityPackage

Produced by Causality Agent.

Fields:

* ranked_contributors: list
* primary_drivers: list[str]
* causal_confidence: high | medium | low

Contributor Structure:

* factor: str
* rank: int
* reason: str

---

# CounterfactualPackage

Produced by Counterfactual Agent.

Fields:

* scenarios: list
* comparisons: list

Scenario Structure:

* scenario_id: str
* change: str
* expected_effect: high | medium | low
* reasoning: str

Comparison Structure:

* scenario_a: str
* scenario_b: str
* higher_impact: str

---

# SkepticPackage

Produced by Skeptic Agent.

Fields:

* confidence: high | medium | low
* uncertainties: list[str]
* limitations: list[str]
* conflicting_evidence: list
* missing_information: list[str]

---

# AggregatedAnalysis

Produced by Orchestrator.

Fields:

* patient_profile
* evidence_package
* causality_package
* counterfactual_package
* skeptic_package

---

# FinalReport

Produced by Synthesis Agent.

Fields:

* top_contributors
* evidence_summary
* counterfactual_summary
* limitations
* confidence
* citations
* safety_disclaimer
