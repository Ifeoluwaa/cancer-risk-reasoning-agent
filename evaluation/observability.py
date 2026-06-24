"""observability.py

Observability, tracing, and logging infrastructure. Intercepts execution at runtime.
"""

import time
import json
import os
from datetime import datetime
from typing import List, Dict, Any

from schemas.contracts import WorkflowState

# Paths
ARTIFACT_DIR = "/Users/lovey/.gemini/antigravity-ide/brain/fa7ddcd5-6da4-4707-b164-7e561336d922"
LOG_DIR = os.path.join(ARTIFACT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

TRACE_FILE = os.path.join(LOG_DIR, "workflow_traces.jsonl")
LOG_FILE = os.path.join(LOG_DIR, "execution_logs.json")


def write_jsonl(path: str, data: Dict[str, Any]) -> None:
    """Helper to write a dictionary as a JSON Line."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


def write_log(data: Dict[str, Any]) -> None:
    """Helper to append a log dictionary to a JSON array logfile."""
    existing = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing = json.loads(content)
        except Exception:
            existing = []
    existing.append(data)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


# References to original functions
original_graph_run = None
original_log_node = None
original_retrieve_docs = None
original_run_benchmark = None
original_run_evaluation_suite = None

_patched = False


# Interceptors
def wrapped_log_node_execution(
    session_id: str, node_name: str, status: str, errors: List[str]
) -> None:
    if original_log_node:
        original_log_node(session_id, node_name, status, errors)
    # Log node transition
    write_log({
        "timestamp": datetime.now().isoformat(),
        "type": "node_execution",
        "session_id": session_id,
        "node_name": node_name,
        "status": status,
        "errors": errors,
    })


def wrapped_graph_run(self, state: WorkflowState) -> WorkflowState:
    session_id = state.session_id
    start_time = time.time()
    start_iso = datetime.now().isoformat()

    # Log workflow start
    write_log({
        "timestamp": start_iso,
        "type": "workflow_start",
        "session_id": session_id,
    })

    try:
        if original_graph_run:
            result_state = original_graph_run(self, state)
        else:
            result_state = state
        status = result_state.status
        errors = result_state.errors
    except Exception as e:
        status = "FAILED"
        errors = [str(e)]
        write_log({
            "timestamp": datetime.now().isoformat(),
            "type": "workflow_error",
            "session_id": session_id,
            "error": str(e),
        })
        raise e
    finally:
        end_time = time.time()
        end_iso = datetime.now().isoformat()
        duration = end_time - start_time

        # Log workflow end
        write_log({
            "timestamp": end_iso,
            "type": "workflow_end",
            "session_id": session_id,
            "status": status,
            "duration_sec": duration,
            "errors": errors,
        })

        # Calculate routing path
        routing_path = ["SecurityAgent"]
        if result_state.security_package:
            if result_state.security_package.safety_status == "red":
                routing_path.append("SafeRefusalNode")
            else:
                routing_path.extend([
                    "EvidenceAgent",
                    "CausalityAgent",
                    "CounterfactualAgent",
                    "SkepticAgent",
                    "SynthesisAgent",
                ])

        # Write Trace Record
        trace_record = {
            "session_id": session_id,
            "timestamp": start_iso,
            "duration_sec": duration,
            "routing_path": routing_path,
            "final_status": status,
            "errors": errors,
        }
        write_jsonl(TRACE_FILE, trace_record)

    return result_state


def wrapped_retrieve_documents(query: str, limit: int = 3) -> List[str]:
    try:
        if original_retrieve_docs:
            docs = original_retrieve_docs(query, limit)
        else:
            docs = []
        error = None
    except Exception as e:
        docs = []
        error = str(e)
        write_log({
            "timestamp": datetime.now().isoformat(),
            "type": "retrieval_error",
            "query": query,
            "error": str(e),
        })
        raise e
    finally:
        write_log({
            "timestamp": datetime.now().isoformat(),
            "type": "retrieval_execution",
            "query": query,
            "limit": limit,
            "retrieved_count": len(docs),
            "error": error,
        })
    return docs


def wrapped_run_benchmark(self) -> Dict[str, Any]:
    if original_run_benchmark:
        res = original_run_benchmark(self)
    else:
        res = {}
    write_log({
        "timestamp": datetime.now().isoformat(),
        "type": "benchmark_execution",
        "total_cases": res.get("summary", {}).get("total_cases", 0),
        "summary": res.get("summary", {}),
    })
    return res


def wrapped_run_evaluation_suite(
    self, results_json_path: str, report_md_path: str
) -> Dict[str, Any]:
    if original_run_evaluation_suite:
        res = original_run_evaluation_suite(self, results_json_path, report_md_path)
    else:
        res = {}
    # Log detailed evaluation executions
    for name, data in res.items():
        write_log({
            "timestamp": datetime.now().isoformat(),
            "type": "evaluation_execution",
            "benchmark_case": name,
            "session_id": data["profile_session_id"],
            "metric_scores": {
                "safety": data["stage16_metrics"]["safety"]["overall_score"],
                "evidence": data["stage16_metrics"]["evidence"]["overall_score"],
                "reasoning": data["stage16_metrics"]["reasoning"]["overall_score"],
                "counterfactual": data["stage16_metrics"]["counterfactual"]["overall_score"],
                "skeptic": data["stage16_metrics"]["skeptic"]["overall_score"],
            },
            "judge_scores": {
                k: v["score"] for k, v in data["stage17_judges"].items()
            },
            "aggregated_score": data["stage16_metrics"]["overall_score"],
        })
    return res


def wrap_agent_run(agent_class, node_name: str) -> None:
    original_run = agent_class.run

    def wrapped_run(self, *args, **kwargs):
        session_id = "unknown"
        if args:
            first_arg = args[0]
            if hasattr(first_arg, "session_id"):
                session_id = first_arg.session_id
            elif hasattr(first_arg, "patient_profile") and first_arg.patient_profile:
                session_id = first_arg.patient_profile.session_id

        wrapped_log_node_execution(session_id, node_name, "success", [])
        return original_run(self, *args, **kwargs)

    agent_class.run = wrapped_run


def setup_observability() -> None:
    """Safely apply runtime monkey-patches, avoiding circular imports."""
    global _patched, original_graph_run, original_log_node, original_retrieve_docs, original_run_benchmark, original_run_evaluation_suite
    if _patched:
        return

    from workflows.workflow_graph import WorkflowGraph
    import tools.orchestration
    import tools.retrieval
    from evaluation.benchmarks import CRRABenchmarkRunner
    from evaluation.judge_runner import LLMJudgeRunner
    
    # Import agents to wrap their run methods
    from agents.security_agent import SecurityAgent
    from agents.evidence_agent import EvidenceAgent
    from agents.causality_agent import CausalityAgent
    from agents.counterfactual_agent import CounterfactualAgent
    from agents.skeptic_agent import SkepticAgent
    from agents.synthesis_agent import SynthesisAgent

    original_graph_run = WorkflowGraph.run
    original_log_node = tools.orchestration.log_node_execution
    original_retrieve_docs = tools.retrieval.retrieve_documents
    original_run_benchmark = CRRABenchmarkRunner.run_benchmark
    original_run_evaluation_suite = LLMJudgeRunner.run_evaluation_suite

    # Wrap graph and tools
    WorkflowGraph.run = wrapped_graph_run
    tools.orchestration.log_node_execution = wrapped_log_node_execution
    tools.retrieval.retrieve_documents = wrapped_retrieve_documents
    CRRABenchmarkRunner.run_benchmark = wrapped_run_benchmark
    LLMJudgeRunner.run_evaluation_suite = wrapped_run_evaluation_suite

    # Wrap agents
    wrap_agent_run(SecurityAgent, "SecurityAgent")
    wrap_agent_run(EvidenceAgent, "EvidenceAgent")
    wrap_agent_run(CausalityAgent, "CausalityAgent")
    wrap_agent_run(CounterfactualAgent, "CounterfactualAgent")
    wrap_agent_run(SkepticAgent, "SkepticAgent")
    wrap_agent_run(SynthesisAgent, "SynthesisAgent")

    _patched = True
