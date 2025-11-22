# Py3plex GUI

A production-ready web-based GUI for multilayer network analysis, visualization, and exploration.

## Quick Start

### Using the run.sh Script (Recommended)

The easiest way to start the GUI:

```bash
cd gui
./run.sh
```

Or if not executable:

```bash
bash run.sh
```

This will:
- Check Docker is running
- Verify required ports are available (8080, 8000, 5555, 6379, 5173)
- Create `.env` file from `.env.example` if needed
- Set up data directories
- Build and start all services
- Display access URLs

**Access the GUI:** http://localhost:8080

### run.sh Options

```bash
./run.sh          # Start all services (default)
./run.sh --logs   # Start and follow logs
./run.sh --dev    # Start in foreground mode
./run.sh --stop   # Stop all services
./run.sh --clean  # Stop and clean up all data
./run.sh --help   # Show help message
```

### Using Make (Alternative)

```bash
cd gui
make up           # Start all services
make logs         # View logs
make down         # Stop services
make help         # Show all commands
```

## Architecture

The GUI consists of multiple Docker services:

| Service    | Port | Description                              | Volume Mounts                          |
|------------|------|------------------------------------------|----------------------------------------|
| nginx      | 8080 | Reverse proxy (main access point)        | `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro` |
| frontend   | 5173 | React + TypeScript + Vite dev server     | `./frontend:/app`, `/app/node_modules` |
| api        | 8000 | FastAPI backend                          | `./data:/data`, `./api:/app`          |
| worker     | -    | Celery worker for async jobs             | `./data:/data`, `./api:/app`          |
| flower     | 5555 | Celery job monitoring UI                 | `./data:/data`, `./api:/app`          |
| redis      | 6379 | Redis cache and task queue               | `redis-data:/data` (named volume)     |

### Volume Mounts Explained

- **`./data:/data`** - Persistent storage for uploads, artifacts, and workspaces
- **`./api:/app`** - API code mounted for hot-reload during development
- **`./frontend:/app`** - Frontend code mounted for hot-reload with Vite HMR
- **`/app/node_modules`** - Anonymous volume to prevent host node_modules conflicts
- **`./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`** - Nginx configuration (read-only)

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
# API Configuration
API_WORKERS=2              # Number of API worker processes
MAX_UPLOAD_MB=512         # Maximum file upload size in MB

# Celery Worker Configuration  
CELERY_CONCURRENCY=2      # Number of concurrent Celery workers

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Data directories (inside containers)
DATA_DIR=/data

# Frontend Configuration
VITE_API_URL=http://localhost:8080/api
```

### Ports

Ensure these ports are available:
- **8080** - Main GUI (nginx)
- **8000** - API (direct access)
- **5555** - Flower monitoring
- **6379** - Redis
- **5173** - Frontend dev server (direct access)

## Features

- ✅ **Interactive Web Interface** - React-based UI with real-time updates
- ✅ **Network Visualization** - Layer-centric views with configurable layouts
- ✅ **Advanced Analysis** - Centrality metrics, community detection, and more
- ✅ **Multiple Formats** - Support for edgelist, GML, NetworkX pickle files
- ✅ **Async Processing** - Background job execution with progress tracking
- ✅ **Workspace Management** - Save and restore complete analysis sessions
- ✅ **Hot Reload** - Code changes automatically reflected (dev mode)

## Development

### Accessing Containers

```bash
make bash-api        # Open shell in API container
make bash-frontend   # Open shell in frontend container
make bash-worker     # Open shell in worker container
```

### Viewing Logs

```bash
make logs                    # All services
docker compose logs api      # Specific service
docker compose logs -f api   # Follow logs
```

### Running Tests

```bash
make test-api        # Run API tests
make e2e            # Run end-to-end tests (not yet implemented)
```

### Hot Reload

- **Frontend**: Vite HMR is enabled - changes to `./frontend/src` are instantly reflected
- **API**: Uvicorn auto-reload is enabled - changes to `./api/app` trigger restart
- **Nginx**: Changes to `nginx.conf` require container restart: `docker compose restart nginx`

## Data Persistence

Data is stored in the `./data` directory:

```
data/
├── uploads/       # User-uploaded network files
├── artifacts/     # Generated analysis results
└── workspaces/    # Saved workspace sessions
```

To reset data:
```bash
./run.sh --clean
# or
make clean
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8080

# Stop existing containers
docker compose down

# Or use run.sh which handles this automatically
./run.sh
```

### Services Not Starting

```bash
# Check service status
docker compose ps

# View service logs
docker compose logs <service-name>

# Rebuild containers
docker compose build --no-cache
docker compose up -d
```

### Frontend Not Loading

1. Check nginx is running: `docker compose ps nginx`
2. Check frontend is running: `docker compose ps frontend`
3. Access frontend directly: http://localhost:5173
4. Check nginx logs: `docker compose logs nginx`

### API Errors

1. Check API logs: `docker compose logs api`
2. Check worker logs: `docker compose logs worker`
3. Verify Redis is healthy: `docker compose ps redis`
4. Check API health: http://localhost:8000/api/health

## Requirements

- Docker & Docker Compose (>= 2.0)
- 4GB RAM minimum
- Available disk space for Docker images and data

## Additional Resources

- **API Documentation**: http://localhost:8080/api/docs (when running)
- **Job Monitoring**: http://localhost:5555 (Flower dashboard)
- **Main Documentation**: [../README.md](../README.md)
- **Ergonomics Guide**: [ERGONOMICS.md](ERGONOMICS.md)
- **Development Summary**: [SUMMARY.md](SUMMARY.md)
