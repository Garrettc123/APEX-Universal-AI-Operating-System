#!/bin/bash
# Local deployment script for APEX Universal AI Operating System

set -e

echo "🚀 APEX Deployment Script"
echo "=========================="

# Configuration
IMAGE_NAME="apex-ai-os"
CONTAINER_NAME="apex-ai-os-local"
PORT=8000

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

# Stop and remove existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🛑 Stopping existing container..."
    docker stop ${CONTAINER_NAME} || true
    docker rm ${CONTAINER_NAME} || true
fi

# Run the container
echo "🚀 Starting container..."
docker run -d \
    --name ${CONTAINER_NAME} \
    -p ${PORT}:8000 \
    -e DATABASE_URL="${DATABASE_URL:-}" \
    -e MONGODB_URI="${MONGODB_URI:-}" \
    -e REDIS_URL="${REDIS_URL:-}" \
    ${IMAGE_NAME}:latest

# Wait for the container to be healthy
echo "⏳ Waiting for application to be ready..."
sleep 5

# Health check
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:${PORT}/health > /dev/null; then
        echo "✅ Application is healthy and ready!"
        echo ""
        echo "🌐 Access the application at: http://localhost:${PORT}"
        echo "📊 Health endpoint: http://localhost:${PORT}/health"
        echo ""
        echo "📝 To view logs: docker logs -f ${CONTAINER_NAME}"
        echo "🛑 To stop: docker stop ${CONTAINER_NAME}"
        exit 0
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt ${RETRY_COUNT}/${MAX_RETRIES}..."
    sleep 2
done

echo "❌ Application failed to start properly"
echo "📝 Showing logs:"
docker logs ${CONTAINER_NAME}
exit 1
