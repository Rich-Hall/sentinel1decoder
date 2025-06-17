#!/bin/bash

# Get the directory where the script is located
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Container name
CONTAINER_NAME="python-dev-container"

echo "Building dev container..."
docker build -t "$CONTAINER_NAME" .

echo "Starting dev container..."
docker run -it --rm \
    --name "$CONTAINER_NAME" \
    -v "$PROJECT_DIR:/app" \
    -p 8000:8000 \
    -w /app \
    "$CONTAINER_NAME"
