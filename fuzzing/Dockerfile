# Dockerfile for fuzzing py3plex with AddressSanitizer (ASAN)
#
# This container provides an environment for fuzzing C/C++ components
# of py3plex with memory error detection enabled.
#
# Build:
#   docker build -t py3plex-fuzzing -f fuzzing/Dockerfile .
#
# Run:
#   docker run -it py3plex-fuzzing
#   # Inside container:
#   ./fuzzing/run_fuzzing.sh 300

FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3 \
    python3-dev \
    python3-pip \
    git \
    cmake \
    clang \
    llvm \
    && rm -rf /var/lib/apt/lists/*

# Set environment for ASAN builds
ENV CFLAGS="-fsanitize=address -fno-omit-frame-pointer -g"
ENV CXXFLAGS="-fsanitize=address -fno-omit-frame-pointer -g"
ENV LDFLAGS="-fsanitize=address"
ENV ASAN_OPTIONS="detect_leaks=1:verbosity=1:symbolize=1"

# Set working directory
WORKDIR /src/py3plex

# Copy the repository
COPY . .

# Upgrade pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# Install py3plex in editable mode with dev dependencies
RUN pip3 install -e ".[dev]" --no-binary :all:

# Install fuzzing tools
RUN pip3 install atheris hypothesis

# Create fuzzing output directory
RUN mkdir -p fuzzing/crashes

# Default command: run fuzzing
CMD ["bash", "-c", "./fuzzing/run_fuzzing.sh 300"]

# Usage examples:
#
# 1. Build the container:
#    docker build -t py3plex-fuzzing -f fuzzing/Dockerfile .
#
# 2. Run quick test (5 minutes):
#    docker run py3plex-fuzzing
#
# 3. Run longer campaign (1 hour):
#    docker run py3plex-fuzzing ./fuzzing/run_fuzzing.sh 3600
#
# 4. Interactive session:
#    docker run -it py3plex-fuzzing bash
#    # Then run fuzzers manually:
#    python3 fuzzing/fuzz_load_network.py fuzzing/seeds/ -max_total_time=300
#
# 5. Mount local directory for crash analysis:
#    docker run -v $(pwd)/fuzzing/crashes:/src/py3plex/fuzzing/crashes \
#               py3plex-fuzzing ./fuzzing/run_fuzzing.sh 600
#
# 6. Run with custom ASAN options:
#    docker run -e ASAN_OPTIONS="detect_leaks=1:verbosity=2" \
#               py3plex-fuzzing
