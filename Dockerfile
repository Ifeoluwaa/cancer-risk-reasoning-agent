# Use an official lightweight Python 3.9 image
FROM python:3.9-slim

# Set system-level environment variables to optimize Python performance
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501

# Set the working directory
WORKDIR /app

# Install system build dependencies required for compiling Python packages (e.g. ChromaDB dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements to leverage Docker's build cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application source files to the container
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Healthcheck to verify that the containerized Streamlit server is running properly
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c 'import urllib.request; urllib.request.urlopen("http://localhost:8501/_stcore/health")' || exit 1

# Start the Streamlit application, binding to 0.0.0.0 and the dynamically configured Cloud Run PORT
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0"]
