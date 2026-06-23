# Implementation Plan

## Philosophy

Follow a specification-first workflow.

Build incrementally.

Validate each stage before proceeding.

---

# Stage 0 — Documentation

Create:

* PROJECT_VISION.md
* PRD.md
* BDD.md
* ARCHITECTURE.md
* AGENT_CONTRACTS.md
* SECURITY.md
* EVALUATION.md
* RISK_REGISTER.md
* IMPLEMENTATION_PLAN.md

Output:

Complete specification package.

---

# Stage 1 — Project Skeleton

Goal:

Create project structure only.

Tasks:

* Folder structure
* Agent folders
* Workflow folder
* Tool folder
* Evaluation folder
* Schema folder

No logic.

Deliverable:

Compileable project skeleton.

---

# Stage 2 — Schema Layer

Goal:

Create all Pydantic schemas.

Tasks:

* PatientProfile
* SecurityPackage
* EvidencePackage
* CausalityPackage
* CounterfactualPackage
* SkepticPackage
* AggregatedAnalysis
* WorkflowState
* FinalReport

Deliverable:

Validated contracts.

---

# Stage 3 — Agent Skeletons

Goal:

Create placeholder agents.

Tasks:

* Security Agent
* Orchestrator Agent
* Evidence Agent
* Causality Agent
* Counterfactual Agent
* Skeptic Agent
* Synthesis Agent

Use mock outputs.

Deliverable:

Working agent structure.

---

# Stage 4 — Workflow Graph

Goal:

Create ADK workflow.

Tasks:

* Security
* Orchestrator
* Evidence
* Causality
* Counterfactual
* Skeptic
* Synthesis

Use mock outputs.

Deliverable:

End-to-end workflow execution.

---

# Stage 5 — Tool Layer

Goal:

Create tool interfaces.

Tasks:

* retrieval.py
* evidence_ranking.py
* counterfactuals.py
* safety.py
* validation.py
* orchestration.py

Deliverable:

Tool contracts.

---

# Stage 6 — Security Implementation

Goal:

Implement Security Agent.

Tasks:

* PII detection
* Prompt injection detection
* Request classification

Deliverable:

Operational security layer.

---

# Stage 7 — Orchestrator Implementation

Goal:

Implement workflow coordination.

Tasks:

* Dispatch tasks
* Aggregate outputs
* Validate state

Deliverable:

Operational orchestration.

---

# Stage 8 — Evidence Agent Implementation

Goal:

Implement evidence reasoning.

Tasks:

* Mock retrieval
* Evidence ranking
* Risk factor extraction

Deliverable:

EvidencePackage generation.

---

# Stage 9 — Causality Agent

Goal:

Implement contributor ranking.

Deliverable:

CausalityPackage generation.

---

# Stage 10 — Counterfactual Agent

Goal:

Implement scenario generation.

Deliverable:

CounterfactualPackage generation.

---

# Stage 11 — Skeptic Agent

Goal:

Implement self-critique.

Deliverable:

SkepticPackage generation.

---

# Stage 12 — Synthesis Agent

Goal:

Implement report generation.

Deliverable:

FinalReport generation.

---

# Stage 13 — End-to-End Testing

Goal:

Verify workflow execution.

Deliverable:

System test report.

---

# Stage 14 — RAG Infrastructure

Goal:

Create retrieval system.

Tasks:

* Document ingestion
* Chunking
* Embeddings
* ChromaDB

Deliverable:

Operational retrieval pipeline.

---

# Stage 15 — Evidence Agent + RAG

Goal:

Replace mock retrieval.

Tasks:

* Connect ChromaDB
* Generate citations

Deliverable:

Evidence-grounded reasoning.

---

# Stage 16 — Evaluation Harness

Goal:

Create benchmark framework.

Deliverable:

Automated evaluation suite.

---

# Stage 17 — LLM-as-Judge

Goal:

Create judge framework.

Deliverable:

Automated scoring.

---

# Stage 18 — Observability

Goal:

Implement:

* Logging
* Tracing
* Evaluation logs

Deliverable:

Debuggable system.

---

# Stage 19 — User Interface

Goal:

Build user experience.

Features:

* Profile entry
* Results dashboard
* Evidence view
* Counterfactual view
* Skeptic view

Deliverable:

Functional UI.

---

# Stage 20 — Deployment

Goal:

Prepare production demo.

Target Stack:

* Google ADK
* Cloud Run
* ChromaDB

Deliverable:

Deployable application.

---

# Definition of Done

The project is complete when:

* Workflow executes end-to-end
* RAG is operational
* Evaluation suite passes
* Safety requirements pass
* UI functions correctly
* Deployment succeeds
* Documentation is complete
