# Dockerfile for py3plex - A library for analysis and visualization of heterogeneous networks
# This container includes py3plex and all its dependencies, and can be used as a CLI tool

FROM python:3.11-slim
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set metadata
LABEL maintainer="Blaž Škrlj <blaz.skrlj@ijs.si>"
LABEL description="Py3plex - A library for multilayer network analysis and visualization"
LABEL version="1.0.2"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
ARG PY3PLEX_EXTRAS=""

# Install system dependencies
# Note: We need build-essential for compiling some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project metadata and core sources first (for better layer caching)
COPY pyproject.toml README.md MANIFEST.in ./
COPY py3plex ./py3plex

# Install py3plex and its dependencies (optionally with extras: viz, algos, infomap, workflows, arrow, dev, tests)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && if [[ -n "${PY3PLEX_EXTRAS}" ]]; then \
         pip install --no-cache-dir ".[$PY3PLEX_EXTRAS]"; \
       else \
         pip install --no-cache-dir .; \
       fi

# Copy the rest of the repository (examples, docs) for interactive use inside the container
COPY . .

# Create a directory for user data/outputs
RUN mkdir -p /data
WORKDIR /data

# Set the entrypoint to the py3plex CLI
ENTRYPOINT ["py3plex"]

# Default command shows help
CMD ["help"]
