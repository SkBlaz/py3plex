.PHONY: help up down logs restart build bash-api bash-worker bash-frontend test-api e2e clean

help:
	@echo "Py3plex GUI - Docker Compose Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Copy .env.example to .env"
	@echo ""
	@echo "Docker Operations:"
	@echo "  make up             - Start all services (build if needed)"
	@echo "  make down           - Stop all services and remove volumes"
	@echo "  make restart        - Restart all services"
	@echo "  make build          - Build all Docker images"
	@echo "  make logs           - Tail logs from all services"
	@echo ""
	@echo "Development:"
	@echo "  make bash-api       - Open bash in API container"
	@echo "  make bash-worker    - Open bash in worker container"
	@echo "  make bash-frontend  - Open bash in frontend container"
	@echo ""
	@echo "Testing:"
	@echo "  make test-api       - Run API tests"
	@echo "  make e2e            - Run end-to-end tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove all containers, volumes, and build artifacts"

setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
	else \
		echo ".env file already exists"; \
	fi

up: setup
	docker compose up --build -d
	@echo ""
	@echo " Py3plex GUI is starting..."
	@echo " Open http://localhost:8080 in your browser"
	@echo " Flower (job monitoring) at http://localhost:5555"
	@echo ""
	@echo "Run 'make logs' to view logs"

down:
	docker compose down -v

restart:
	docker compose restart

build:
	docker compose build

logs:
	docker compose logs -f

bash-api:
	docker compose exec api /bin/bash

bash-worker:
	docker compose exec worker /bin/bash

bash-frontend:
	docker compose exec frontend /bin/sh

test-api:
	docker compose exec api pytest /app/tests -v

e2e:
	@echo "Running end-to-end tests..."
	@echo "Not yet implemented"

clean:
	docker compose down -v --remove-orphans
	docker system prune -f
	rm -rf ./data/uploads/* ./data/artifacts/* ./data/workspaces/*
	@echo "Cleaned up all containers, volumes, and data"
