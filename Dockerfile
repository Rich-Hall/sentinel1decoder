# Use the official Python 3.11 image from Docker Hub as a base
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Create an entrypoint script that installs the package in dev mode
RUN echo '#!/bin/bash\nsource /opt/venv/bin/activate\ncd /app && maturin develop && exec "$@"' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/bin/bash"]
