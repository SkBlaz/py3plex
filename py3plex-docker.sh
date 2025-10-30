#!/bin/bash
# Helper script for running py3plex via Docker
# Usage: ./py3plex-docker.sh [py3plex arguments]
# Example: ./py3plex-docker.sh --version
#          ./py3plex-docker.sh create --nodes 100 --layers 3 --output /data/network.edgelist

# Docker image name
IMAGE_NAME="py3plex:latest"

# Data directory (relative to current directory)
DATA_DIR="$(pwd)/data"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if image exists, if not, prompt to build
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo "Docker image '$IMAGE_NAME' not found."
    echo "Would you like to build it now? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Building Docker image..."
        docker build -t "$IMAGE_NAME" .
        if [ $? -ne 0 ]; then
            echo "Error: Failed to build Docker image"
            exit 1
        fi
    else
        echo "Please build the image first: docker build -t $IMAGE_NAME ."
        exit 1
    fi
fi

# Create data directory if it doesn't exist
if [ ! -d "$DATA_DIR" ]; then
    echo "Creating data directory: $DATA_DIR"
    mkdir -p "$DATA_DIR"
fi

# Run py3plex in Docker with volume mount
# The --rm flag removes the container after execution
# The -v flag mounts the local data directory to /data in the container
docker run --rm -v "$DATA_DIR:/data" "$IMAGE_NAME" "$@"
