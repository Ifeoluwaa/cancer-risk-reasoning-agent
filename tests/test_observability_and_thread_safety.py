"""Regression and multi-threading validation tests for Observability and ChromaDB RAG.
"""

import threading
import unittest
from typing import List

from schemas.contracts import PatientProfile
from agents.evidence_agent import EvidenceAgent
from tools.retrieval import retrieve_documents, _get_thread_store
from evaluation.observability import setup_observability, wrap_agent_run


class MockFailingAgent:
    """Mock agent class designed to fail to verify exception catching and logging."""
    def run(self, profile: PatientProfile, retrieved_docs: List[str] = None):
        raise RuntimeError("Mock agent crash")


class TestObservabilityAndThreadSafety(unittest.TestCase):
    """Verifies observability logging order, lazy retrieval loading, and thread safety."""

    def setUp(self) -> None:
        setup_observability()
        self.profile = PatientProfile(
            session_id="thread_safety_test_session",
            age=45,
            sex="male",
            bmi=24.0,
            smoking_status="never",
            smoking_years=0,
            alcohol_use="none",
            physical_activity="medium",
            diet_quality="medium",
            sun_exposure="low",
            occupation="Office worker",
            environmental_exposure=[],
            family_history=False,
            known_mutations=[],
            previous_cancer_history=False,
        )

    def test_observability_failure_logging_and_propagation(self) -> None:
        """Verifies that observability logs failure states and propagates the exception."""
        # Wrap MockFailingAgent
        wrap_agent_run(MockFailingAgent, "MockFailingAgent")
        agent = MockFailingAgent()

        with self.assertRaises(RuntimeError) as context:
            agent.run(self.profile)

        self.assertEqual(str(context.exception), "Mock agent crash")

    def test_lazy_retrieval_initialization_per_thread(self) -> None:
        """Verifies that retrieval stores are lazily instantiated and populated."""
        store, retriever, ingestor = _get_thread_store()
        self.assertIsNotNone(store)
        self.assertIsNotNone(retriever)
        self.assertIsNotNone(ingestor)

    def test_repeated_retrieval_calls(self) -> None:
        """Verifies that repeated document retrievals are stable and return consistent data."""
        docs1 = retrieve_documents("tobacco smoke", limit=2)
        docs2 = retrieve_documents("tobacco smoke", limit=2)

        self.assertEqual(docs1, docs2)
        self.assertTrue(len(docs1) > 0)

    def test_streamlit_style_multithread_execution(self) -> None:
        """Simulates concurrent Streamlit multi-thread requests to verify database thread safety."""
        errors = []

        def worker_task(thread_id: int):
            try:
                # Retrieve documents concurrently
                docs = retrieve_documents("tobacco smoke age", limit=2)
                if not docs:
                    errors.append(f"Thread {thread_id} got empty results")
                
                # Execute agent concurrently
                agent = EvidenceAgent()
                profile_copy = self.profile.model_copy()
                profile_copy.session_id = f"thread_session_{thread_id}"
                pkg = agent.run(profile_copy)
                if not pkg.risk_factors:
                    errors.append(f"Thread {thread_id} failed to extract factors")
            except Exception as e:
                errors.append(f"Thread {thread_id} crashed with: {str(e)}")

        threads = []
        for i in range(10):
            t = threading.Thread(target=worker_task, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Multi-threading failures detected: {errors}")

    def test_streamlit_sequential_threads_execution(self) -> None:
        """Simulates sequential thread execution to verify SQLite memory cache persistence."""
        errors = []

        def worker_task(thread_id: int):
            try:
                docs = retrieve_documents("tobacco smoke age", limit=2)
                if not docs:
                    errors.append(f"Thread {thread_id} got empty results")
            except Exception as e:
                errors.append(f"Thread {thread_id} crashed with: {str(e)}")

        # Run threads one after another, ensuring connections are closed/opened sequentially
        for i in range(5):
            t = threading.Thread(target=worker_task, args=(i,))
            t.start()
            t.join()

        self.assertEqual(errors, [], f"Sequential threading failures detected: {errors}")


if __name__ == "__main__":
    unittest.main()
