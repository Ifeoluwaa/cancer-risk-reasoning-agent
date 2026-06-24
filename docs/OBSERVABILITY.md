# CRRA Observability and Debugging Infrastructure

This document outlines the logging, workflow tracing, and benchmarking logs architecture for the Cancer Risk Reasoning Agent (CRRA).

## Observability Architecture

To respect strict separation of concerns and avoid invasive changes to clinical reasoning core components, Stage 18 uses **monkey-patched wrapper interceptors** loaded at runtime. This allows 100% additive tracing of all workflow executions, document retrievals, errors, and evaluation suites.

---

## Log & Trace Files

All logs and traces are saved locally inside the artifacts directory:
- **Workflow Traces (JSON Lines)**: `/Users/lovey/.gemini/antigravity-ide/brain/fa7ddcd5-6da4-4707-b164-7e561336d922/logs/workflow_traces.jsonl`
- **Execution Logs (JSON Array)**: `/Users/lovey/.gemini/antigravity-ide/brain/fa7ddcd5-6da4-4707-b164-7e561336d922/logs/execution_logs.json`

---

## Trace Schema

Each entry in `workflow_traces.jsonl` follows this structure:

```json
{
  "session_id": "session_e2e_smoking",
  "timestamp": "2026-06-24T18:10:00.123456",
  "duration_sec": 0.045,
  "routing_path": [
    "SecurityAgent",
    "EvidenceAgent",
    "CausalityAgent",
    "CounterfactualAgent",
    "SkepticAgent",
    "SynthesisAgent"
  ],
  "final_status": "COMPLETED",
  "errors": []
}
```

---

## Execution Logs Schema

`execution_logs.json` accumulates structured event records:

### 1. Workflow Start/End
```json
{
  "timestamp": "2026-06-24T18:10:00.123456",
  "type": "workflow_start",
  "session_id": "session_e2e_smoking"
}
```

### 2. Node Execution
```json
{
  "timestamp": "2026-06-24T18:10:00.128910",
  "type": "node_execution",
  "session_id": "session_e2e_smoking",
  "node_name": "EvidenceAgent",
  "status": "success",
  "errors": []
}
```

### 3. Retrieval Execution (ChromaDB queries)
```json
{
  "timestamp": "2026-06-24T18:10:00.135000",
  "type": "retrieval_execution",
  "query": "tobacco smoking age",
  "limit": 3,
  "retrieved_count": 2,
  "error": null
}
```

### 4. Evaluation Execution (Benchmarks & Judges)
```json
{
  "timestamp": "2026-06-24T18:10:05.999999",
  "type": "evaluation_execution",
  "benchmark_case": "smoking_profile",
  "session_id": "eval_smoking",
  "metric_scores": {
    "safety": 1.0,
    "evidence": 1.0,
    "reasoning": 0.7,
    "counterfactual": 1.0,
    "skeptic": 1.0
  },
  "judge_scores": {
    "Evidence Quality": 5.0,
    "Reasoning Quality": 4.0,
    "Counterfactual Quality": 5.0,
    "Skeptic Quality": 5.0,
    "Safety Compliance": 5.0,
    "Report Clarity": 5.0
  },
  "aggregated_score": 0.94
}
```

---

## Debugging Workflows

1. **Locate Failures**: Read `workflow_traces.jsonl` to identify any traces where `"final_status"` is `"FAILED"`.
2. **Review Node Transitions**: Filter `execution_logs.json` for records of type `"node_execution"` matching the failed `"session_id"`. Look for statuses labeled `"fail"` and inspect their `"errors"` array.
3. **Verify Database Queries**: Check records of type `"retrieval_execution"` or `"retrieval_error"` to see if queries to ChromaDB failed or returned empty results.
