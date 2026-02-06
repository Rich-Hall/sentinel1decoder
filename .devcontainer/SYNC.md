# Keeping Dockerfiles in Sync

The root `Dockerfile` and `.devcontainer/Dockerfile` share a common "base" stage that sets up:
- Python 3.11
- Rust toolchain
- System dependencies
- Virtual environment

## When to Update Both Files

**Update BOTH files when changing:**
- Python version (currently 3.11)
- Rust installation method or version
- System package dependencies (build-essential, curl, git, etc.)
- Environment variables (PYTHONDONTWRITEBYTECODE, RUSTUP_HOME, etc.)
- Virtual environment setup

**Only update the specific file for:**
- Root Dockerfile: Source code copying, package installation method
- Devcontainer Dockerfile: Dependency installation list, devcontainer-specific optimizations

## Current Base Stage Configuration

Both files should have identical base stages with:
```dockerfile
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    RUSTUP_HOME=/opt/rust \
    CARGO_HOME=/opt/rust

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable \
    && rustup default stable

ENV PATH="/opt/rust/bin:${PATH}"

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
```

## Future Improvement

Consider using Docker BuildKit's `--target` flag or a shared base image to eliminate duplication, but for now, manual sync with clear comments is the most maintainable approach.
