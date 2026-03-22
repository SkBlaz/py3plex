#!/bin/bash
# run.sh - Py3plex GUI Startup Script
# 
# This script starts the Py3plex GUI with all necessary configurations,
# mounts, and environment variables.
#
# Prerequisites:
# - Docker & Docker Compose (>= 2.0)
# - 4GB RAM minimum
# - Available ports: 8080 (GUI), 8000 (API), 5555 (Flower), 6379 (Redis), 5173 (Frontend Dev)
#
# Usage:
#   ./run.sh           - Start all services in detached mode
#   ./run.sh --logs    - Start and follow logs
#   ./run.sh --dev     - Start with verbose output (foreground)
#   ./run.sh --stop    - Stop all services
#   ./run.sh --clean   - Stop services and clean up volumes/data
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}${NC} $1"
}

print_error() {
    echo -e "${RED}${NC} $1"
}

# Check if Docker is running
check_docker() {
    print_info "Checking Docker..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if required ports are available
check_ports() {
    print_info "Checking if required ports are available..."
    local ports=(8080 8000 5555 6379 5173)
    local ports_in_use=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$port "; then
            ports_in_use+=($port)
        fi
    done
    
    if [ ${#ports_in_use[@]} -gt 0 ]; then
        print_warning "The following ports are already in use: ${ports_in_use[*]}"
        print_warning "This may be from a previous run. Attempting to stop existing containers..."
        docker compose down > /dev/null 2>&1 || true
        sleep 2
    fi
    print_success "Port check complete"
}

# Setup environment file
setup_env() {
    print_info "Setting up environment configuration..."
    if [ ! -f .env ]; then
        cp .env.example .env
        print_success "Created .env file from .env.example"
        print_info "You can edit .env to customize configuration"
    else
        print_success ".env file already exists"
    fi
}

# Create required data directories
setup_directories() {
    print_info "Setting up data directories..."
    mkdir -p data/uploads data/artifacts data/workspaces
    print_success "Data directories created"
}

# Start services
start_services() {
    local mode=$1
    
    print_info "Building and starting services..."
    print_info ""
    print_info "Services being started:"
    print_info "  • redis          - Redis cache (port 6379)"
    print_info "  • api            - FastAPI backend (port 8000)"
    print_info "  • worker         - Celery worker for async jobs"
    print_info "  • flower         - Job monitoring UI (port 5555)"
    print_info "  • frontend       - React/Vite dev server (port 5173)"
    print_info "  • nginx          - Reverse proxy (port 8080)"
    print_info ""
    print_info "Volumes mounted:"
    print_info "  • ./data         → /data (persistent data storage)"
    print_info "  • ./api          → /app (API code - hot reload enabled)"
    print_info "  • ./frontend     → /app (Frontend code - hot reload enabled)"
    print_info "  • ./nginx/nginx.conf → /etc/nginx/nginx.conf (nginx config)"
    print_info ""
    print_info "Environment variables (from .env):"
    print_info "  • API_WORKERS          - Number of API workers (default: 2)"
    print_info "  • MAX_UPLOAD_MB        - Max upload size in MB (default: 512)"
    print_info "  • CELERY_CONCURRENCY   - Celery worker concurrency (default: 2)"
    print_info "  • REDIS_URL            - Redis connection URL"
    print_info "  • VITE_API_URL         - Frontend API URL (default: http://localhost:8080/api)"
    print_info ""
    
    if [ "$mode" == "foreground" ]; then
        print_info "Starting in foreground mode (Ctrl+C to stop)..."
        docker compose up --build
    elif [ "$mode" == "logs" ]; then
        docker compose up --build -d
        print_success "Services started successfully!"
        print_info "Following logs (Ctrl+C to exit logs, services will continue running)..."
        docker compose logs -f
    else
        docker compose up --build -d
        print_success "Services started successfully!"
    fi
}

# Show access information
show_access_info() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_success "Py3plex GUI is now running!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "   Main GUI:        http://localhost:8080"
    echo "   Job Monitor:     http://localhost:5555"
    echo "   API Docs:        http://localhost:8080/api/docs"
    echo "   Frontend Dev:    http://localhost:5173 (direct)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    print_info "Useful commands:"
    echo "  make logs           - View all service logs"
    echo "  make bash-api       - Open shell in API container"
    echo "  make bash-frontend  - Open shell in frontend container"
    echo "  make down           - Stop all services"
    echo "  ./run.sh --stop     - Stop all services (same as above)"
    echo "  ./run.sh --clean    - Stop and clean all data"
    echo ""
    print_info "Service health check:"
    echo "  docker compose ps   - Check container status"
    echo ""
}

# Stop services
stop_services() {
    print_info "Stopping all services..."
    docker compose down
    print_success "All services stopped"
}

# Clean services and data
clean_services() {
    print_warning "This will stop all services and remove volumes and data!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Stopping services and cleaning up..."
        docker compose down -v --remove-orphans
        docker system prune -f
        print_info "Removing data directories..."
        rm -rf ./data/uploads/* ./data/artifacts/* ./data/workspaces/* 2>/dev/null || true
        print_success "Cleanup complete"
    else
        print_info "Cleanup cancelled"
    fi
}

# Show usage
usage() {
    echo "Py3plex GUI Runner"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  (no args)    Start all services in detached mode"
    echo "  --logs       Start services and follow logs"
    echo "  --dev        Start in foreground with verbose output"
    echo "  --stop       Stop all services"
    echo "  --clean      Stop services and clean up volumes/data"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Start GUI (recommended)"
    echo "  $0 --logs       # Start and watch logs"
    echo "  $0 --stop       # Stop GUI"
    echo ""
}

# Main execution
main() {
    local mode="detached"
    
    case "${1:-}" in
        --help|-h)
            usage
            exit 0
            ;;
        --stop)
            check_docker
            stop_services
            exit 0
            ;;
        --clean)
            check_docker
            clean_services
            exit 0
            ;;
        --logs)
            mode="logs"
            ;;
        --dev)
            mode="foreground"
            ;;
        "")
            mode="detached"
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
    
    # Pre-flight checks and setup
    check_docker
    check_ports
    setup_env
    setup_directories
    
    # Start services
    start_services "$mode"
    
    # Show access info (only for detached mode)
    if [ "$mode" == "detached" ]; then
        show_access_info
    fi
}

# Run main function
main "$@"
