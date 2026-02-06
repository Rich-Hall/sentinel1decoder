# Devcontainer-specific Dockerfile
# Optimized for development: installs dependencies but doesn't copy source
# (source is mounted as volume by devcontainer)
#
# SYNC NOTE: The base stage below should match the "base" stage in ../Dockerfile.
# When updating Python version, Rust setup, or system dependencies, update BOTH files.
# Consider this a temporary duplication until Docker supports cross-file stage references.

# Build the shared base stage (must match ../Dockerfile base stage exactly)
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

# Devcontainer-specific stage: extends base but doesn't copy source
FROM base

# Copy only dependency files for better layer caching
# Source code will be mounted as volume by devcontainer
COPY pyproject.toml ./

# Install Python dependencies (without package, for caching)
# The package itself will be installed via maturin develop in postCreateCommand
# This matches the dependencies in ../Dockerfile - keep in sync manually
RUN pip install --no-cache-dir \
    "maturin>=1.4.0" \
    "numpy>=1.24" \
    pandas \
    pytest \
    pytest-cov \
    pre-commit \
    "black==24.2" \
    "flake8==7.0" \
    autoflake \
    "isort==5.13.2" \
    "mypy==1.8.0" \
    jupyter \
    jupyterlab \
    ipywidgets \
    scipy \
    matplotlib \
    pandas-stubs

# Create an improved entrypoint script
# This will be overridden by devcontainer, but useful as fallback
RUN echo '#!/bin/bash\n\
set -e\n\
cd /app\n\
# Only rebuild if explicitly requested or if this is not a devcontainer\n\
if [ -n "$REBUILD_RUST" ] || [ -z "$REMOTE_CONTAINERS" ]; then\n\
    echo "Building Rust extension with maturin..."\n\
    maturin develop\n\
fi\n\
exec "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
