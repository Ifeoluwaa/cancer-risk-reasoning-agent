# The Cancer Risk Reasoning Agent (CRRA): An Explainable, Multi-Agent Decision Support System for Oncological Risk Profiling

## Abstract
Traditional Large Language Model (LLM) chatbots face severe limitations in clinical medicine, notably issues of hallucination, lack of causal reasoning, and the output of false precision (e.g., precise risk percentages unsupported by underlying epidemiological evidence). To address these issues, we present the Cancer Risk Reasoning Agent (CRRA), a modular, multi-agent clinical decision support prototype designed to estimate lifestyle, demographic, and familial cancer risk drivers. CRRA coordinates a sequenced multi-agent graph (Security -> Evidence -> Causality -> Counterfactual -> Skeptic -> Synthesis) with strict routing rules to guarantee safety, transparency, and explainability. By separating raw attribution calculations from patient-facing clinical communication, the system replaces numerical attribution percentages with clinically interpretable impact tiers and visual block bars, aligning with actual medical decision support guidelines. Furthermore, the system includes an independent skeptic review layer to audit assumptions, log limitations, and propose follow-up questions, preventing confirmation bias. System performance was validated against a benchmarking framework composed of 18 synthetic patient profiles, showing 100% safety compliance and robust explainability across diverse demographic contexts. CRRA demonstrates the viability of utilizing multi-agent graphs to deliver transparent, educational, and clinically grounded decision-support tools.

---

## 1. Introduction
Modern cancer prevention relies heavily on recognizing modifiable lifestyle and environmental exposures, alongside genetic predispositions. However, translating epidemiological consensus into personalized, patient-centered insights remains challenging. While Large Language Models (LLMs) excel at natural language understanding, traditional conversational LLMs are poorly suited for clinical consultation. They lack structured reasoning bounds, present risks of hallucinating scientific evidence, cannot easily model synergistic multi-factor interactions, and often present numerical risks with false precision—giving patients an unrealistic impression of mathematical certainty.

Explainable AI (XAI) is critical in medical informatics. Decisions must be transparent, traceable back to verified guidelines, and open to critique. To address these needs, we developed the Cancer Risk Reasoning Agent (CRRA) using a multi-agent orchestration architecture. By dividing complex clinical reasoning into specialized, coordinated agent nodes, we enforce safety boundaries, ground risk factors in structured academic literature, calculate causal risk attribution without user-facing false precision, simulate counterfactual interventions, and perform self-critical audits.

---

## 2. Problem Statement
The Cancer Risk Reasoning Agent (CRRA) is designed as a clinical decision-support and educational prototype to evaluate individual baseline cancer risk factors. It is explicitly constrained by the following design boundaries:
1. **Not a Diagnostic Tool**: CRRA does not diagnose active oncological conditions or predict absolute cancer probabilities.
2. **Not a Treatment Recommendation Engine**: It does not prescribe medications, recommend therapies, or dictate clinical interventions.
3. **Decision-Support and Educational Focus**: Its objective is to explain how specific patient exposures relate to established literature and how risk can be qualitatively mitigated through behavioral changes.

---

## 3. System Architecture
The system is built as a state-based multi-agent graph coordinate system utilizing Pydantic data contracts for all inter-node communication.

```
       [Raw Profile]
             │
             ▼
     ┌──────────────┐
     │Security Agent│ ──(RED/Refusal)──► [Safe Refusal Report]
     └──────┬───────┘
            │ (GREEN/YELLOW)
            ▼
     ┌──────────────┐
     │Clean Profile │
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │Evidence Agent│
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │Causality Agent│
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │Counterfactual│
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │Skeptic Agent │
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │SynthesisAgent│
     └──────┬───────┘
            │
            ▼
     [Clinical Report] & [Reasoning Trace]
```

### Core Components
* **`PatientProfile`**: The input schema capturing patient age, sex, BMI, smoking status, alcohol use, physical activity, diet, sun exposure, occupation, environmental carcinogens, mutations, family history, and personal history.
* **`WorkflowState`**: A unified state container tracking session metadata, active workflow status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`), current graph execution steps, error lists, accumulated agent outputs, and the final synthesized report.
* **`WorkflowGraph`**: The central coordinator executing the agent nodes sequentially and performing conditional safety-based routing decisions.

---

## 4. Multi-Agent Reasoning Pipeline
The reasoning pipeline consists of six specialized agents executing in sequence:

### 4.1. SecurityAgent
* **Purpose**: Inspects inputs, sanitizes PII, detects jailbreaks/prompt injections, and routes the request.
* **Inputs**: Raw `PatientProfile`.
* **Outputs**: `SecurityPackage` containing safety status (`green`, `yellow`, `red`), redacted field lists, and a sanitized `clean_profile`.
* **Responsibilities**: Prevents system exploits and maps queries to clinical severity levels.
* **Current Implementation**: Screen fields via regex rules and session/occupation mock markers to classify clinical safety routes.

### 4.2. EvidenceAgent
* **Purpose**: Gathers literature grounding and citations for risk factors matching the patient profile.
* **Inputs**: Sanitized `PatientProfile`.
* **Outputs**: `EvidencePackage` containing identified risk factors (with strength/score details) and scientific academic citations.
* **Responsibilities**: Eliminates hallucinatory output by anchoring factors directly to retrieved medical literature databases.
* **Current Implementation**: Employs local semantic database retrieval (via ChromaDB embeddings) to map exposures to guideline records.

### 4.3. CausalityAgent
* **Purpose**: Prioritizes risk contributors and establishes primary causal risk drivers.
* **Inputs**: Sanitized `PatientProfile`, `EvidencePackage`.
* **Outputs**: `CausalityPackage` outlining a list of ranked `Contributor` objects and primary drivers.
* **Responsibilities**: Formulates causal explanations linking exposures to risk.
* **Current Implementation**: Sorts risk factors by evidence score and patient-specific metrics, calling the attribution module to compute weights.

### 4.4. CounterfactualAgent
* **Purpose**: Simulates what-if scenarios (lifestyle changes) to estimate risk reduction.
* **Inputs**: Sanitized `PatientProfile`, primary causal drivers.
* **Outputs**: `CounterfactualPackage` containing hypothetical intervention scenarios and pairwise impact comparisons.
* **Responsibilities**: Formulates actionable recommendations for modifiable risk drivers.
* **Current Implementation**: Filters non-modifiable factors (e.g. age, genetics) and generates priority-ordered recommendations.

### 4.5. SkepticAgent
* **Purpose**: Audits the reasoning pipeline for assumptions, limitations, and alternative explanations.
* **Inputs**: `EvidencePackage`, `CausalityPackage`, `CounterfactualPackage`.
* **Outputs**: `SkepticPackage` containing uncertainties, causal assumptions, missing data parameters, and recommended follow-up questions.
* **Responsibilities**: Acts as a self-critical layer to counter overconfidence and bias.
* **Current Implementation**: Analyzes exposure gaps and literature limitations, outputting structured critique lists.

### 4.6. SynthesisAgent
* **Purpose**: Consolidates all agent outputs into a unified, patient-centric report.
* **Inputs**: Compiled `AggregatedAnalysis`.
* **Outputs**: `FinalReport` containing narrative risk summaries, priorities, and citations.
* **Responsibilities**: Translates agent-level technical objects into understandable narratives.
* **Current Implementation**: Merges report strings, resolving references and formatting safety disclaimers.

---

## 5. Supporting Clinical Intelligence Modules

### 5.1. Evidence Quality Engine
Grading retrieved documents into evidence strength classes (High, Medium, Low) based on source origin (e.g., Randomized Controlled Trials, Systematic Reviews, Clinical Guidelines).

### 5.2. Interaction Engine
Detects co-exposures that multiply risk non-linearly (e.g., Asbestos exposure and active smoking multiplying risk by ~35% due to synergistic cellular damage).

### 5.3. Attribution Engine
Calculates patient-specific risk weight allocations using exposure metrics, baseline age weighting, and interaction offsets. Raw calculations are maintained internally to preserve logical rankings.

### 5.4. Confidence Engine
Evaluates report certainty by comparing citation strengths and skeptic limitation warnings.

### 5.5. Adaptive Questioning
Generates targeted clinical follow-up questions to fill profile gaps and increase reasoning confidence.

### 5.6. Clinical Impact Tier Engine
Converts raw percentage attributions into qualitative clinical categories (Very High, High, Moderate, Low, Minimal) and visual bars, eliminating numerical false precision.

---

## 6. Explainability Framework
Transparency is achieved through the following presentation features in the dashboard:
* **Interactive Contributor Cards**: Expandable blocks featuring badges for modifiability status, synergistic interactions, rationale, literature support, and counterfactual relevance.
* **Confidence Panel**: A clear visual confidence meter (`🟢🟢🟢`) paired with bullet-point reasons.
* **Reasoning Trace Viewer**: A dedicated tab illustrating the step-by-step pipeline execution, including checkmarks, plain-language annotations (What/Why/How), and actual inputs/outputs for every single stage.

---

## 7. Evaluation Methodology
The CRRA quality and safety are validated through a clinical evaluation framework:
* **Benchmark Dataset**: Consists of 18 synthetic profiles representing healthy baselines, heavy smokers, genetic mutations, lifestyle factors, and unsafe inputs.
* **Automated Regression Suite**: Executes the graph on all benchmark profiles, scoring outputs across six dimensions (Safety, Evidence Grounding, Causal Reasoning, Counterfactual Quality, Skeptic Completeness, and Explainability/Traceability).
* **Metrics**: Implements mathematical Jaccard overlaps and completeness checkers. Detailed benchmark output statistics are output automatically to `EVALUATION_REPORT.md`.

---

## 8. Results
* **Functional Correctness**: Complete reasoning pipeline executes successfully on all synthetic profiles.
* **100% Safety Compliance**: Blocked all diagnostic/treatment requests (RED route) and injected warnings for risk estimations (YELLOW route).
* **Automated Test Suite**: All 127 automated tests pass successfully, confirming zero regressions.
* **Explainability Coverage**: Verified 100% explainability trace completeness and contributor traceability.

---

## 9. Limitations
1. **Prototype Status**: Implemented as a research and educational prototype; not approved by any medical regulatory authority (e.g., FDA, EMA).
2. **Curated/Mock Evidence**: Retrieves from a curated local database mimicking clinical literature.
3. **Lack of Prospective Clinical Validation**: System has not been evaluated in active clinical trials.
4. **Synthetic Benchmarks**: The evaluation relies on synthetic benchmark data rather than real-world EHR records.

---

## 10. Future Work
* **Live Knowledge Graph Integration**: Connecting the EvidenceAgent to live PubMed, ClinVar, and WHO API endpoints.
* **Genomic Profile Parsing**: Expanding the `PatientProfile` to parse high-throughput sequencing data.
* **Clinician Feedback Loops**: Incorporating reinforcement learning interfaces for clinicians to flag and correct reasoning.
* **Longitudinal Reasoning**: Modeling changes in patient exposures and risk trajectories over time.

---

## 11. Conclusion
The Cancer Risk Reasoning Agent (CRRA) presents a modular, highly explainable alternative to conversational clinical AI. By organizing reasoning into a multi-agent graph with decoupled clinical calculation and communication layers, CRRA avoids false precision, enforces safety routing, and guarantees literature grounding. The prototype provides a valuable blueprint for transparent, educational, and modular clinical decision-support systems.
