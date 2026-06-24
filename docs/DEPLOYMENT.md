# CRRA Deployment and Infrastructure Guide

This guide details instructions and setup configurations for deploying the Cancer Risk Reasoning Agent (CRRA) locally, using Docker containers, running on Google Cloud Run, and registering as an agent via the Google Agent Development Kit (ADK).

---

## 1. Local Development
To run the application locally without containers or cloud access:
1. Ensure your conda environment is activated.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
4. Access the web interface at `http://localhost:8501`.

---

## 2. Docker Deployment
The project contains a lightweight Docker configuration (`Dockerfile` and `.dockerignore`) tailored for building production-ready container images.

### A. Docker Build
To build the container image locally:
```bash
./deploy.sh build
```
Or run the manual Docker command:
```bash
docker build -t cancer-risk-reasoning-agent:local .
```

### B. Docker Run
To run the built container locally:
```bash
docker run -d -p 8501:8501 -e PORT=8501 --name crra-app cancer-risk-reasoning-agent:local
```
Navigate to `http://localhost:8501` to test the application running inside the container.

---

## 3. Cloud Run Deployment
Google Cloud Run provides a serverless platform to deploy containerized microservices.

### A. Prerequisites
1. Ensure you have the `gcloud` CLI installed and authenticated.
2. Enable required services in your target project:
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com
   ```

### B. Build and Push Container
Submit the codebase to Google Cloud Build to build and register the image inside Artifact Registry:
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/cancer-risk-reasoning-agent:latest .
```

### C. Deploy to Cloud Run
Execute the deployment using `gcloud run deploy`:
```bash
gcloud run deploy cancer-risk-reasoning-agent \
  --image gcr.io/YOUR_PROJECT_ID/cancer-risk-reasoning-agent:latest \
  --platform managed \
  --region us-central1 \
  --port 8501 \
  --allow-unauthenticated
```

---

## 4. Google ADK Integration
Google ADK (Agent Development Kit) allows orchestrating multi-agent applications under a unified runtime. 

### A. ADK Registration Flow
The ADK exposes agents as service endpoints. Under ADK:
1. **AdkApp Definition**: You define an `AdkApp` that registers tools, callbacks, and orchestration.
2. **Orchestrator Wrapper**:
   ```python
   from vertexai.preview import reasoning_engines
   from agents.orchestrator_agent import OrchestratorAgent

   # Define the ADK-compatible entrypoint
   class ADKCancerReasoningEngine:
       def __init__(self):
           self.orchestrator = OrchestratorAgent()

       def query(self, profile_dict: dict) -> dict:
           from schemas.contracts import PatientProfile
           profile = PatientProfile(**profile_dict)
           state = self.orchestrator.run(profile)
           return state.dict()
   ```
3. **Registration command**:
   ```bash
   agents-cli publish gemini-enterprise \
     --service-name "cancer-risk-reasoning-agent" \
     --region "us-central1"
   ```

---

## 5. ChromaDB Persistence Strategy
ChromaDB is configured to run in two modes:

1. **Ephemeral (In-memory) Mode**:
   - **How it works**: Default configuration (`persist_directory=None`). The database resides entirely in RAM and is automatically initialized/seeded on the first retrieval query via `_ensure_populated()`.
   - **Use Case**: Excellent for serverless Cloud Run and local developer testing. Eliminates the need for external disks or database service configurations, ensuring low-latency cold starts.
2. **Persistent Directory Mode**:
   - **How it works**: Passes a disk path to `PersistentClient(path=persist_directory)`.
   - **Volume Mounting on Cloud Run**: To persist index states across container recycles, configure Cloud Run Volume Mounts (e.g. Cloud Storage FUSE mount or Cloud Filestore NFS share) mapping `/data/chroma_db` to your container environment, and set `CHROMADB_PERSIST_DIR=/data/chroma_db` in your environment variables.

---

## 6. Logging and Observability
The Stage 18 Observability system automatically intercepts runs:
- **Workflow Traces**: Written as JSON Lines to `logs/workflow_traces.jsonl`.
- **Execution Logs**: Written as JSON to `logs/execution_logs.json`.
- **Cloud Run Compatibility**: The app prints standard errors to `stdout`/`stderr` which are automatically collected and aggregated by **Google Cloud Logging**.

To view logs in GCP:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cancer-risk-reasoning-agent" --limit=50
```

---

## 7. Troubleshooting

| Symptom | Diagnosis | Solution |
|---------|-----------|----------|
| Cloud Run service crashes on start | Port mismatch or health check failure | Verify that `--port` is set to `8501` or matches the `$PORT` environment variable. |
| ChromaDB fails to start | Missing compiler tools for build | Verify `build-essential` is installed in the Dockerfile. |
| PII / Redaction triggers on test sessions | Safety rule triggered | Ensure testing session IDs do not contain words like "red" or "yellow" unless testing safety routes. |
| File lock errors on ChromaDB | Multiple processes accessing sqlite | Avoid concurrent write processes on the persistent ChromaDB folder. |
