# Changelog — Observability & Thread-Safety Fix

This document outlines the changes applied to resolve the falsified success logs and multi-threaded database connection conflicts in the CRRA runtime.

---

## 1. Observability Wrapper Correction

- **File**: `evaluation/observability.py`
- **Change**: Refactored `wrap_agent_run` to execute the original agent `run` method inside a `try-except` block.
- **Outcome**: The interceptor now logs success only *after* the wrapped function returns successfully. If an exception occurs, it correctly logs `"failed"`, appends the traceback/error details to the execution logs, and propagates the exception so that `WorkflowGraph` can abort and handle the state safely.

---

## 2. Thread-Safe ChromaDB Retrieval Initialization

- **File**: `tools/retrieval.py`
- **Change**: Removed static module-level initialization of `ChromaVectorStore`, `RAGRetriever`, and `RAGIngestor`. Replaced them with a thread-safe factory function `_get_thread_store()` utilizing `threading.local()`.
- **Outcome**: Each separate execution thread (e.g. concurrent user sessions in Streamlit) receives its own clean database and client instances, preventing SQLite connection sharing conflicts and eliminating the `no such table: collections` runtime crash.

---

## 3. Regression & Concurrency Tests

- **File**: `tests/test_observability_and_thread_safety.py`
- **Added Tests**:
  - `test_observability_failure_logging_and_propagation`: Confirms that agent node errors trigger failed logs and propagate correctly.
  - `test_lazy_retrieval_initialization_per_thread`: Confirms lazy loading of thread-local stores.
  - `test_repeated_retrieval_calls`: Confirms retrieval consistency across repeated query triggers.
  - `test_streamlit_style_multithread_execution`: Simulates 10 concurrent threads running retrievals and reasoning agents to verify SQLite connection thread safety.
