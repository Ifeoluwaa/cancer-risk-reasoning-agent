#!/usr/bin/env bash
# deploy.sh
# Deployment helper script for building CRRA container and deploying to Google Cloud Run.
# (Generates commands/actions without performing live cloud deployment).

set -euo pipefail

# Configuration defaults
SERVICE_NAME="cancer-risk-reasoning-agent"
IMAGE_TAG="gcr.io/your-gcp-project-id/cancer-risk-reasoning-agent:latest"
REGION="us-central1"
PORT="8501"

echo "=========================================================="
echo "      CRRA Cloud Run Deployment Script Builder            "
echo "=========================================================="

usage() {
    echo "Usage: $0 [build|deploy-dry-run|help]"
    echo ""
    echo "Commands:"
    echo "  build            Builds the Docker container locally."
    echo "  deploy-dry-run   Prints the gcloud command that would be run for Cloud Run."
    echo "  help             Shows this help manual."
}

if [ $# -lt 1 ]; then
    usage
    exit 1
fi

COMMAND="$1"

case "$COMMAND" in
    build)
        echo "[+] Building Docker image locally: $SERVICE_NAME..."
        docker build -t "$SERVICE_NAME:local" .
        echo "[✓] Local build complete. Run the container with:"
        echo "    docker run -p 8501:8501 -e PORT=8501 $SERVICE_NAME:local"
        ;;
    deploy-dry-run)
        echo "[+] Generating dry-run deployment variables..."
        echo "Service Name:      $SERVICE_NAME"
        echo "Target Image:      $IMAGE_TAG"
        echo "Region:            $REGION"
        echo "Service Port:      $PORT"
        echo ""
        echo "To execute deployment, run the following commands:"
        echo "1. Build and push image to Artifact Registry:"
        echo "   gcloud builds submit --tag $IMAGE_TAG ."
        echo ""
        echo "2. Deploy to Cloud Run:"
        echo "   gcloud run deploy $SERVICE_NAME \\"
        echo "     --image $IMAGE_TAG \\"
        echo "     --platform managed \\"
        echo "     --region $REGION \\"
        echo "     --port $PORT \\"
        echo "     --allow-unauthenticated"
        ;;
    help|*)
        usage
        ;;
esac
