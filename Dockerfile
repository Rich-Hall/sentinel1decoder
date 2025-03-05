# Use the official Python 3.8 image from Docker Hub as a base
FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (if necessary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libatlas-base-dev \
    git \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file into the container and install the Python dependencies
COPY requirements.txt  requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Create an entrypoint script that installs the package in dev mode
RUN echo '#!/bin/bash\ncd /app && pip install -e . && exec "$@"' > /entrypoint.sh \
    && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
