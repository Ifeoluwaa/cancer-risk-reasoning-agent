# Product Requirements Document (PRD)

## Project Name

Cancer Risk Reasoning Agent (CRRA)

## Problem Statement

Many healthcare AI systems focus on prediction, diagnosis, or treatment recommendations. These approaches can be unsafe, difficult to validate, and often fail to explain why a conclusion was reached.

Users need a system that helps them understand which factors contribute most to future cancer risk, what evidence supports those factors, how alternative lifestyle choices may influence those contributors, and where uncertainty exists.

## Goal

Build a multi-agent reasoning system that:

* Identifies major cancer risk contributors
* Retrieves supporting evidence
* Explains causal reasoning
* Generates counterfactual scenarios
* Critiques its own conclusions
* Produces an evidence-grounded report

## Non-Goals

The system will not:

* Diagnose cancer
* Predict cancer probability
* Recommend treatment
* Prescribe medication
* Replace healthcare professionals

## Target Users

* Individuals interested in understanding cancer risk contributors
* Healthcare educators
* Researchers studying agentic AI systems
* AI engineers evaluating multi-agent reasoning architectures

## Core Features

### Evidence Retrieval

Retrieve trusted evidence from curated sources.

### Risk Factor Identification

Identify relevant cancer risk contributors.

### Causal Reasoning

Rank contributors by importance.

### Counterfactual Analysis

Evaluate alternative scenarios.

### Scientific Skepticism

Challenge conclusions and identify uncertainty.

### Report Generation

Generate an understandable final report.

## Success Criteria

* Evidence is grounded and cited
* Major contributors are correctly identified
* Counterfactuals are logical and explainable
* Uncertainty is surfaced
* Safety requirements are maintained
* Final reports are understandable by non-experts
