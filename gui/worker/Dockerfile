ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}

# Set metadata
LABEL maintainer="Py3plex GUI"
LABEL description="Celery worker for Py3plex GUI"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    graphviz \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (same as API + flower for monitoring)
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    celery==5.3.4 \
    redis==5.0.1 \
    flower==2.0.1 \
    pydantic==2.5.3 \
    networkx==3.2.1 \
    matplotlib==3.8.2 \
    numpy==1.26.3 \
    scipy==1.11.4 \
    scikit-learn==1.5.0 \
    python-louvain==0.16

# Set working directory
WORKDIR /app

# Copy application code
COPY ./api/app ./app

# Copy and install py3plex from repository root
COPY ../ /tmp/py3plex
RUN pip install -e /tmp/py3plex

# Create data directory
RUN mkdir -p /data/uploads /data/artifacts /data/workspaces

# Default command (can be overridden in docker-compose)
CMD ["celery", "-A", "app.workers.celery_app", "worker", "-Q", "default", "-O", "fair", "--loglevel=info"]
