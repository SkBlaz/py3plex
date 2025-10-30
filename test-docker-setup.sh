#!/bin/bash
# Test script for Docker setup
# This script validates that the Docker container can be built and basic commands work

set -e  # Exit on error

echo "==================================="
echo "Py3plex Docker Setup Test"
echo "==================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test 1: Check if Docker is installed
echo "Test 1: Checking Docker installation..."
if command -v docker &> /dev/null; then
    print_result 0 "Docker is installed"
else
    print_result 1 "Docker is not installed"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Test 2: Check if Dockerfile exists
echo ""
echo "Test 2: Checking if Dockerfile exists..."
if [ -f "Dockerfile" ]; then
    print_result 0 "Dockerfile exists"
else
    print_result 1 "Dockerfile not found"
    exit 1
fi

# Test 3: Check if .dockerignore exists
echo ""
echo "Test 3: Checking if .dockerignore exists..."
if [ -f ".dockerignore" ]; then
    print_result 0 ".dockerignore exists"
else
    print_result 1 ".dockerignore not found (not critical)"
fi

# Test 4: Check if docker-compose.yml exists
echo ""
echo "Test 4: Checking if docker-compose.yml exists..."
if [ -f "docker-compose.yml" ]; then
    print_result 0 "docker-compose.yml exists"
else
    print_result 1 "docker-compose.yml not found (optional)"
fi

# Test 5: Build Docker image
echo ""
echo "Test 5: Building Docker image (this may take several minutes)..."
if docker build -t py3plex-test:latest . > /tmp/docker-build.log 2>&1; then
    print_result 0 "Docker image built successfully"
else
    print_result 1 "Docker image build failed"
    echo "Build log:"
    tail -50 /tmp/docker-build.log
    exit 1
fi

# Test 6: Run --version command
echo ""
echo "Test 6: Running 'py3plex --version' in container..."
if docker run --rm py3plex-test:latest --version > /tmp/docker-version.log 2>&1; then
    VERSION=$(cat /tmp/docker-version.log)
    print_result 0 "Version command works: $VERSION"
else
    print_result 1 "Version command failed"
    cat /tmp/docker-version.log
fi

# Test 7: Run help command
echo ""
echo "Test 7: Running 'py3plex help' in container..."
if docker run --rm py3plex-test:latest help > /tmp/docker-help.log 2>&1; then
    print_result 0 "Help command works"
else
    print_result 1 "Help command failed"
    cat /tmp/docker-help.log
fi

# Test 8: Run selftest command
echo ""
echo "Test 8: Running 'py3plex selftest' in container..."
if docker run --rm py3plex-test:latest selftest > /tmp/docker-selftest.log 2>&1; then
    print_result 0 "Selftest passed"
else
    print_result 1 "Selftest failed"
    cat /tmp/docker-selftest.log
fi

# Test 9: Test volume mounting and file creation
echo ""
echo "Test 9: Testing volume mounting and file creation..."
mkdir -p /tmp/py3plex-test-data
if docker run --rm -v /tmp/py3plex-test-data:/data py3plex-test:latest \
    create --nodes 10 --layers 2 --output /data/test-network.edgelist > /tmp/docker-create.log 2>&1; then
    if [ -f "/tmp/py3plex-test-data/test-network.edgelist" ]; then
        print_result 0 "Volume mounting and file creation works"
        rm -rf /tmp/py3plex-test-data
    else
        print_result 1 "File was not created in mounted volume"
    fi
else
    print_result 1 "Create command failed"
    cat /tmp/docker-create.log
fi

# Cleanup
echo ""
echo "Cleaning up test image..."
docker rmi py3plex-test:latest > /dev/null 2>&1 || true

# Summary
echo ""
echo "==================================="
echo "Test Summary"
echo "==================================="
echo "Tests passed: $TESTS_PASSED"
echo "Tests failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    echo "The Docker setup is working correctly."
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    echo "Please review the errors above."
    exit 1
fi
