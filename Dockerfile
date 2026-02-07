# Shared base stage - contains common setup used by both CI and devcontainer
# This ensures both environments stay in sync
#
# SYNC NOTE: The "base" stage below should match the "base" stage in .devcontainer/Dockerfile.
# When updating Python version, Rust setup, or system dependencies, update BOTH files.
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    RUSTUP_HOME=/opt/rust \
    CARGO_HOME=/opt/rust

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Rust with stable toolchain
# --default-toolchain stable already sets it as default, no need for rustup default stable
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable

ENV PATH="/opt/rust/bin:${PATH}"

# Set the working directory
WORKDIR /app

# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Final stage for CI/root Dockerfile - includes source code and package installation
FROM base

# Copy project files
COPY . .

# Install Python dependencies and the package in editable mode
RUN pip install --no-cache-dir -e ".[dev]"

# Create an improved entrypoint script that conditionally rebuilds Rust extension
RUN echo '#!/bin/bash\n\
set -e\n\
source /opt/venv/bin/activate\n\
cd /app\n\
# Rebuild Rust extension if explicitly requested or if running in CI\n\
# In CI, always rebuild; in interactive use, only if REBUILD_RUST is set\n\
if [ -n "$REBUILD_RUST" ] || [ -n "$CI" ]; then\n\
    echo "Building Rust extension with maturin..."\n\
    maturin develop\n\
fi\n\
exec "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
