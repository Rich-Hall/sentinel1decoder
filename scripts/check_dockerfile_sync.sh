#!/bin/bash
# Simple script to check if the base stages in Dockerfile and .devcontainer/Dockerfile are in sync
# This helps ensure both environments use the same Python/Rust/system dependencies

set -e

ROOT_DOCKERFILE="Dockerfile"
DEV_DOCKERFILE=".devcontainer/Dockerfile"

if [ ! -f "$ROOT_DOCKERFILE" ] || [ ! -f "$DEV_DOCKERFILE" ]; then
    echo "Error: Could not find both Dockerfiles"
    exit 1
fi

# Extract the base stage from each Dockerfile (from "FROM python" to "ENV PATH" before COPY/other commands)
extract_base_stage() {
    local file=$1
    # Extract from "FROM python" until the first non-base-stage command (COPY, RUN pip install, etc.)
    awk '/^FROM python.*as base/,/^(COPY|RUN pip install|# Final stage|# Devcontainer-specific)/ {
        if (/^(COPY|RUN pip install|# Final stage|# Devcontainer-specific)/ && !/^FROM/) {
            exit
        }
        print
    }' "$file" | grep -v "^# Final stage" | grep -v "^# Devcontainer-specific"
}

ROOT_BASE=$(extract_base_stage "$ROOT_DOCKERFILE")
DEV_BASE=$(extract_base_stage "$DEV_DOCKERFILE")

# Normalize whitespace for comparison
ROOT_BASE_NORM=$(echo "$ROOT_BASE" | sed 's/[[:space:]]\+/ /g' | grep -v '^$')
DEV_BASE_NORM=$(echo "$DEV_BASE" | sed 's/[[:space:]]\+/ /g' | grep -v '^$')

if [ "$ROOT_BASE_NORM" = "$DEV_BASE_NORM" ]; then
    echo "✓ Base stages are in sync"
    exit 0
else
    echo "✗ Base stages are OUT OF SYNC!"
    echo ""
    echo "Differences found. Please ensure both Dockerfiles have identical base stages."
    echo ""
    echo "Root Dockerfile base stage:"
    echo "$ROOT_BASE"
    echo ""
    echo "Devcontainer Dockerfile base stage:"
    echo "$DEV_BASE"
    exit 1
fi
