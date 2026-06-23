# Risk Register

## Purpose

Identify major project risks and define mitigation strategies.

---

## Risk 1: Hallucinated Evidence

Description:

Agent cites unsupported information.

Impact:

High

Mitigation:

* Hybrid RAG
* Citations required
* Skeptic verification

---

## Risk 2: Diagnostic Advice

Description:

System generates diagnosis.

Impact:

Critical

Mitigation:

* Security Agent
* Safety prompts
* Evaluation checks

---

## Risk 3: Treatment Recommendation

Description:

System recommends treatment.

Impact:

Critical

Mitigation:

* Security Agent
* Red request classification
* Safety testing

---

## Risk 4: Prompt Injection

Description:

User attempts to bypass rules.

Impact:

High

Mitigation:

* Prompt injection detector
* Security gate
* Workflow blocking

---

## Risk 5: Missing Information

Description:

Insufficient user data.

Impact:

Medium

Mitigation:

* Skeptic Agent
* Missing information detection

---

## Risk 6: Retrieval Failure

Description:

Relevant evidence not retrieved.

Impact:

High

Mitigation:

* Retrieval evaluation
* Fallback uncertainty response

---

## Risk 7: Weak Contributor Ranking

Description:

Important contributors ranked incorrectly.

Impact:

Medium

Mitigation:

* Causality evaluation
* Synthetic benchmark suite

---

## Risk 8: Weak Counterfactual Analysis

Description:

Generated scenarios are unrealistic.

Impact:

Medium

Mitigation:

* Counterfactual benchmarks
* Human evaluation rubric

---

## Risk 9: Unsafe Final Report

Description:

Final report violates safety constraints.

Impact:

Critical

Mitigation:

* Synthesis guardrails
* Safety evaluation
* End-to-end testing

---

## Risk 10: Agent Contract Drift

Description:

Agents stop producing expected schemas.

Impact:

High

Mitigation:

* Pydantic validation
* Contract testing
* CI checks

---

## Risk 11: Cost Escalation

Description:

Excessive model calls increase cost.

Impact:

Medium

Mitigation:

* Parallel execution
* Model selection strategy
* Retrieval optimization

---

## Risk 12: Loss of User Trust

Description:

System appears overly confident.

Impact:

High

Mitigation:

* Skeptic Agent
* Confidence scores
* Limitation reporting
