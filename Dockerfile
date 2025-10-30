# Dockerfile for py3plex - A library for analysis and visualization of heterogeneous networks
# This container includes py3plex and all its dependencies, and can be used as a CLI tool

FROM python:3.11-slim

# Set metadata
LABEL maintainer="Blaž Škrlj <blaz.skrlj@ijs.si>"
LABEL description="Py3plex - A library for multilayer network analysis and visualization"
LABEL version="0.95a"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

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

# Copy requirements and setup files first (for better layer caching)
COPY requirements.txt setup.py pyproject.toml MANIFEST.in ./
COPY py3plex/__init__.py ./py3plex/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Install py3plex in editable mode
RUN pip install --no-cache-dir -e .

# Create a directory for user data/outputs
RUN mkdir -p /data
WORKDIR /data

# Set the entrypoint to the py3plex CLI
ENTRYPOINT ["py3plex"]

# Default command shows help
CMD ["help"]
