"""test_observability.py

Unit tests for Stage 18 Observability and Debugging Infrastructure.
"""

import os
import unittest
import json
from evaluation.observability import TRACE_FILE, LOG_FILE, setup_observability
from agents.orchestrator_agent import OrchestratorAgent
from schemas.contracts import PatientProfile
from evaluation.benchmarks import CRRABenchmarkRunner
from evaluation.judge_runner import LLMJudgeRunner


class TestObservabilityInfrastructure(unittest.TestCase):
    """Test suite validating trace generation, log parsing, and persistence of executions."""

    @classmethod
    def setUpClass(cls) -> None:
        setup_observability()

    def setUp(self) -> None:
        # Clear existing logs/traces for isolated testing
        if os.path.exists(TRACE_FILE):
            os.remove(TRACE_FILE)
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
            
        self.orchestrator = OrchestratorAgent()

    def test_log_and_trace_generation_on_run(self) -> None:
        """Verify log and trace records are generated upon running a workflow."""
        profile = PatientProfile(
            session_id="session_obs_test",
            age=48,
            sex="male",
            bmi=24.0,
            smoking_status="active",
            smoking_years=10,
            alcohol_use="none",
            physical_activity="high",
            diet_quality="high",
            sun_exposure="low",
            occupation="engineer",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )

        state = self.orchestrator.run(profile)
        
        # 1. Assert trace file exists and is populated
        self.assertTrue(os.path.exists(TRACE_FILE))
        with open(TRACE_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        
        trace = json.loads(lines[0])
        self.assertEqual(trace["session_id"], "session_obs_test")
        self.assertEqual(trace["final_status"], "COMPLETED")
        self.assertIn("SecurityAgent", trace["routing_path"])
        self.assertIn("EvidenceAgent", trace["routing_path"])
        self.assertTrue(trace["duration_sec"] > 0)

        # Call retrieve_documents directly to generate the retrieval log entry
        from tools.retrieval import retrieve_documents
        retrieve_documents("tobacco", limit=1)

        # 2. Assert execution log file exists and contains start, node, and end events
        self.assertTrue(os.path.exists(LOG_FILE))
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            
        event_types = [log["type"] for log in logs]
        self.assertIn("workflow_start", event_types)
        self.assertIn("node_execution", event_types)
        self.assertIn("workflow_end", event_types)
        self.assertIn("retrieval_execution", event_types)

    def test_error_logging(self) -> None:
        """Verify that errors/exceptions are captured and logged."""
        # Cause an orchestration error by running the workflow with an invalid profile
        # WorkflowGraph will fail validation because PatientProfile fields will be wrong if we patch it
        # Let's run a profile with invalid state
        from schemas.contracts import WorkflowState
        from workflows.workflow_graph import WorkflowGraph
        
        graph = WorkflowGraph()
        # Create a state without patient profile to trigger ValueError in orchestration
        state = WorkflowState(session_id="err_session", status="COMPLETED") # Completed with missing security_package
        
        res_state = graph.run(state)
        self.assertEqual(res_state.status, "FAILED")
        self.assertTrue(len(res_state.errors) > 0)
            
        # Assert log captures the exception
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            
        err_events = [log for log in logs if log["type"] in ["workflow_error", "workflow_end"]]
        self.assertTrue(len(err_events) > 0)
        self.assertTrue(any("errors" in err and len(err["errors"]) > 0 for err in err_events))

    def test_evaluation_and_benchmark_logging(self) -> None:
        """Verify that benchmark runs and judge evaluations log their aggregate stats."""
        # Run benchmark
        bm_runner = CRRABenchmarkRunner()
        bm_runner.run_benchmark()
        
        # Run judge evaluation suite
        j_runner = LLMJudgeRunner()
        scratch_json = os.path.join(os.path.dirname(LOG_FILE), "scratch_obs.json")
        scratch_md = os.path.join(os.path.dirname(LOG_FILE), "scratch_obs.md")
        
        j_runner.run_evaluation_suite(scratch_json, scratch_md)
        
        # Verify files were generated
        self.assertTrue(os.path.exists(scratch_json))
        
        # Cleanup scratch evaluation files
        if os.path.exists(scratch_json):
            os.remove(scratch_json)
        if os.path.exists(scratch_md):
            os.remove(scratch_md)
            
        # Verify logs contain benchmark and evaluation events
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            
        event_types = [log["type"] for log in logs]
        self.assertIn("benchmark_execution", event_types)
        self.assertIn("evaluation_execution", event_types)

    def test_idempotent_observability_wrapping(self) -> None:
        """Verify that repeated setup_observability() calls do not cause infinite recursion."""
        from workflows.workflow_graph import WorkflowGraph
        import evaluation.observability as obs
        
        # 1. Assert sentinel attributes are present
        self.assertTrue(getattr(WorkflowGraph.run, "__observability_wrapped__", False))
        original_func = getattr(WorkflowGraph.run, "__original_func__", None)
        self.assertIsNotNone(original_func)
        self.assertNotEqual(WorkflowGraph.run, original_func)
        
        # 2. Simulate module reload by resetting the module-level _patched flag and globals
        obs._patched = False
        obs.original_graph_run = None
        
        # 3. Call setup_observability again
        obs.setup_observability()
        
        # 4. Verify sentinel and original functions are preserved (not double wrapped)
        self.assertTrue(getattr(WorkflowGraph.run, "__observability_wrapped__", False))
        self.assertEqual(getattr(WorkflowGraph.run, "__original_func__", None), original_func)
        
        # 5. Run the pipeline to verify that it executes successfully without causing RecursionError
        profile = PatientProfile(
            session_id="session_idempotent_test",
            age=30,
            sex="female",
            bmi=22.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="medium",
            diet_quality="medium",
            sun_exposure="low",
            occupation="engineer",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )
        state = self.orchestrator.run(profile)
        self.assertEqual(state.status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()
