# CRRA Architectural Validation & Audit Report (Sprint 3.5)

This document presents a comprehensive review of the Cancer Risk Reasoning Agent (CRRA) architecture, covering structural logic, scoring consistency, agent interactions, variable coverage, dead code analysis, explainability tracing, and technical recommendations.

---

## 1. Duplicate Logic Audit

We audited the codebase to locate instances of duplicate reasoning, repeated formulas, or redundant checks:

* **Scoring and Weighting**: Evidence classification and quality weighting are centralized inside [`tools/evidence_ranking.py`](file:///Users/lovey/Desktop/Kaggle_Agent_exercise/cancer-risk-reasoning-agent/tools/evidence_ranking.py). Downstream stages (Causality, Counterfactual, and Skeptic) consume the computed `evidence_score` directly.
* **Interactions**: Synergy detection resides solely in [`tools/interaction.py`](file:///Users/lovey/Desktop/Kaggle_Agent_exercise/cancer-risk-reasoning-agent/tools/interaction.py). Other components utilize `evidence.interactions` from the stack/state rather than re-computing synergy rules.
* **Confidence Computation**: The logic is centralized in [`tools/skeptic.py`](file:///Users/lovey/Desktop/Kaggle_Agent_exercise/cancer-risk-reasoning-agent/tools/skeptic.py)'s `calculate_confidence()` function, which acts as the single source of truth for confidence scaling across the workspace.
* **Profile Retrieval**: A single helper function `_get_profile_from_stack()` in [`tools/skeptic.py`](file:///Users/lovey/Desktop/Kaggle_Agent_exercise/cancer-risk-reasoning-agent/tools/skeptic.py) retrieves patient data recursively from local frames to keep state access unified.

---

## 2. Scoring & Attribution Consistency Audit

Scoring follows a strict deterministic flow to prevent overwriting or mathematical contradictions:

```mermaid
graph TD
    A[Raw Retrieval / ChromaDB] -->|Base Score| B[Evidence Ranking / extract_risk_factors]
    B -->|Quality Multipliers applied| C[Attribution / calculate_attribution]
    C -->|Hereditary (1.25x) & Synergy Allocation| D[Ranked Contributors]
    D -->|Confidence Score formula| E[Skeptic Assessment]
    E -->|Confidence Levels: High/Medium/Low| F[Synthesis Report]
```

### Normalization and Propagation Strategy
1. **Evidence Layer**: The raw score for each risk factor is derived from retrieved documents. The maximum quality multiplier is applied (e.g. `1.20` for Clinical Guidelines, `0.80` for Case Reports).
2. **Attribution Layer**:
   - Multiplies risk scores by category weights (Hereditary: `1.25`, Lifestyle: `1.0`, Background: `0.75`).
   - Allocates synergistic interaction bonuses (co-exposures transfer `35%` of their combined base scores to the interaction term while subtracting a `15%` overlap from individual factors).
   - Normalizes all scores to sum to `100.0%` for relative attribution.
3. **Skeptic/Confidence Layer**: Integrates quantities, quality scores, grounding factors, and uncertainty deductions to map the final confidence to `high`, `medium`, or `low`.

---

## 3. PatientProfile Coverage Audit

We analyzed every field in the `PatientProfile` to identify active utilization and potential gaps:

| Field | Status | Purpose & Clinical Impact |
| :--- | :--- | :--- |
| `session_id` | **Active** | Manages tracing, observability, and bypass/safety flags (e.g., test mocks). |
| `age` | **Active** | Formulates age-senescence queries, triggers baseline risk scoring, and identifies potential cellular aging confounders. |
| `sex` | **Active** | Contextualizes genetic queries (e.g., gender-specific BRCA searches). |
| `bmi` | **Active** | Triggers obesity risk queries, metabolic interaction pathways, and counterfactual weight reduction recommendations. |
| `smoking_status` | **Active** | Triggers tobacco queries, synergistic interactions, and behavior cessation counterfactuals. |
| `smoking_years` | **Active** | Used to calculate cumulative exposure dose and personalize risk rationales. |
| `alcohol_use` | **Active** | Triggers mucosal damage and acetaldehyde exposure queries, and guides cessation recommendations. |
| `physical_activity`| **Active** | Evaluates exercise frequency, separating activity benefits from obesity confounders. |
| `diet_quality` | **Active** | Correlates dietary patterns to colon/rectal and baseline metabolic risks. |
| `sun_exposure` | **Active** | Triggers UV-exposure queries, melanoma risk matching, and UV protection counterfactuals. |
| `occupation` | **Indirect** | Collected on input; clinical risk estimation relies on structured fields like `environmental_exposure` (e.g., "asbestos") rather than raw occupational text strings to prevent false negatives. |
| `environmental_exposure` | **Active** | Triggers carcinogen dosimetry queries, synergistic co-exposure rules, and occupational safety advice. |
| `family_history` | **Active** | Triggers familial risk queries, genetic interaction weighting, and counseling recommendations. |
| `known_mutations` | **Active** | Maps genetic variant pathogenicity and locks high-baseline non-modifiable counterfactual warnings. |
| `previous_cancer_history` | **Active** | Establishes biological cancer survivorship baseline, adjusting non-modifiable recommendations. |

---

## 4. Cross-Agent Consistency & Explainability Audit

The clinical reasoning flows transparently through the multi-agent graph:

1. **EvidenceAgent** collects raw literature grounding for active factors.
2. **CausalityAgent** evaluates quality-weighted scores and establishes the primary risk drivers.
3. **CounterfactualAgent** generates behavioral interventions targeting modifiable drivers, explaining that non-modifiable drivers (age, genetic history) establish a baseline risk.
4. **SkepticAgent** reviews assumptions, reports missing info, audits study designs, and computes dynamic confidence.
5. **SynthesisAgent** compiles these findings into a unified, structured clinical report.

**Verification**: No clinical facts or risk attributions disappear between stages. Every recommendation in Section 4 is linked to a primary driver identified in Section 2.

---

## 5. Dead Code Audit

We searched for obsolete components, imports, and variables:
* **LLM Judges**: Stage 17 evaluation judges are present in the `evaluation/` directory. Although they do not run in the live patient request graph (which is expected because they run out-of-band as benchmark tests), they are maintained for developer evaluations.
* **Imports**: All imports in `agents/` and `tools/` are actively resolved and utilized.
* **Unused Variables**: Cleaned up minor unused imports and verified that no legacy branches interfere with current contracts.

---

## 6. Refactoring Summary

* **Readability**: Code comments in [`tools/skeptic.py`](file:///Users/lovey/Desktop/Kaggle_Agent_exercise/cancer-risk-reasoning-agent/tools/skeptic.py) and [`tools/attribution.py`](file:///Users/lovey/Desktop/Kaggle_Agent_exercise/cancer-risk-reasoning-agent/tools/attribution.py) were refreshed to detail the exact clinical weights and formulas used.
* **Simplification**: Unified recursive stack frames lookup to prevent profile parsing inconsistencies.

---

## 7. Remaining Technical Debt & Recommendations for Sprint 4

1. **Direct Occupation Processing**: In Sprint 4, implement a lightweight occupational-exposure mapper to link raw free-text occupations (e.g. "construction worker") to structured exposures (e.g. "asbestos").
2. **Confidence Resolution**: Incorporate semantic text quality checks of RAG retrievals to dynamically lower confidence if the retrieved chunks contain low-relevance filler text.
