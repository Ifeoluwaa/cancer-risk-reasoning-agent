# System Architecture Document

## System Overview

Cancer Risk Reasoning Agent (CRRA) is a multi-agent reasoning system that combines evidence retrieval, causal reasoning, counterfactual analysis, and scientific skepticism to help users understand contributors to future cancer risk.

## High-Level Workflow

START
→ Security Agent
→ Orchestrator Agent
→ Evidence Agent
→ Causality Agent
→ Counterfactual Agent
→ Skeptic Agent
→ Synthesis Agent
→ END

## Agent Responsibilities

### Security Agent

* Detect PII
* Detect prompt injection
* Classify medical requests

### Orchestrator Agent

* Manage workflow execution
* Dispatch tasks
* Aggregate outputs
* Validate workflow state

### Evidence Agent

* Retrieve evidence
* Rank evidence quality
* Extract risk factors

### Causality Agent

* Rank contributors
* Identify primary drivers

### Counterfactual Agent

* Generate alternative scenarios
* Compare scenarios

### Skeptic Agent

* Identify uncertainty
* Verify evidence
* Retrieve conflicting evidence
* Detect missing information

### Synthesis Agent

* Generate final report
* Communicate findings clearly

## RAG Architecture

Sources:

* PubMed Abstracts
* WHO Resources
* CDC Resources
* National Cancer Institute Resources
* American Cancer Society Resources

Pipeline:

Documents
→ Chunking
→ Embeddings
→ ChromaDB
→ Retrieval
→ Evidence Agent

## Context Engineering Strategy

Evidence Agent:

* Patient Profile
* Retrieved Documents

Causality Agent:

* Patient Profile
* Evidence Package

Counterfactual Agent:

* Patient Profile
* Ranked Contributors

Skeptic Agent:

* Evidence Package
* Causality Output
* Counterfactual Output

Synthesis Agent:

* All outputs

## Memory Strategy

Version 1 uses session memory only.

No long-term memory is stored.

## Security Architecture

Green:

* Explanation requests

Yellow:

* Risk estimation requests

Red:

* Diagnosis requests
* Treatment requests

PII is removed before processing.

Prompt injection attempts are blocked before reaching downstream agents.

## Deployment Architecture

Frontend
→ ADK Workflow
→ ChromaDB
→ Evaluation Layer

Target deployment:

* Google ADK
* Cloud Run
* ChromaDB
