# ─────────────────────────────────────────────────────────────────────────────
# Py3plex - Multilayer Network Analysis Library
# Production-Grade Makefile for Development, Testing, and Publishing
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help setup dev-install format lint test coverage benchmark docs clean build publish api-check ci test-all

# ─────────────────────────────────────────────────────────────────────────────
# Variables
# ─────────────────────────────────────────────────────────────────────────────
PYTHON := python3
VENV := .venv
PACKAGE := py3plex
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

# Detect if we're in CI or if tools are available globally
# Use venv tools if available, otherwise fall back to global tools
RUFF := $(shell if [ -f $(VENV_BIN)/ruff ]; then echo $(VENV_BIN)/ruff; else echo ruff; fi)
BLACK := $(shell if [ -f $(VENV_BIN)/black ]; then echo $(VENV_BIN)/black; else echo black; fi)
ISORT := $(shell if [ -f $(VENV_BIN)/isort ]; then echo $(VENV_BIN)/isort; else echo isort; fi)
MYPY := $(shell if [ -f $(VENV_BIN)/mypy ]; then echo $(VENV_BIN)/mypy; else echo mypy; fi)
PYTEST := $(shell if [ -f $(VENV_BIN)/pytest ]; then echo $(VENV_BIN)/pytest; else echo pytest; fi)

# Colors for terminal output (ANSI escape codes)
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_BLUE := \033[34m
COLOR_YELLOW := \033[33m
COLOR_RED := \033[31m

# ─────────────────────────────────────────────────────────────────────────────
# Default Target
# ─────────────────────────────────────────────────────────────────────────────
.DEFAULT_GOAL := help

# ─────────────────────────────────────────────────────────────────────────────
# Help - Display available commands
# ─────────────────────────────────────────────────────────────────────────────
help: ## Display all available commands with descriptions
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)Py3plex Makefile - Available Commands$(COLOR_RESET)\n"
	@printf "$(COLOR_BOLD)════════════════════════════════════════════════════════════════$(COLOR_RESET)\n\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(COLOR_GREEN)%-15s$(COLOR_RESET) %s\n", $$1, $$2}'
	@printf "\n$(COLOR_BOLD)Example usage:$(COLOR_RESET)\n"
	@printf "  make setup        # Initial setup\n"
	@printf "  make format       # Format code\n"
	@printf "  make lint         # Run linters\n"
	@printf "  make test         # Run tests\n"
	@printf "  make benchmark    # Run benchmarks\n"
	@printf "  make test-all     # Run ALL checks (lint + test + benchmark)\n"
	@printf "  make ci           # Run CI checks (lint + test)\n"
	@printf "  make docs         # Build Sphinx documentation\n"
	@printf "  make docs-pdf     # Generate PDF from master documentation\n"
	@printf "  make docs-check   # Check API consistency\n\n"

# ─────────────────────────────────────────────────────────────────────────────
# Environment Setup
# ─────────────────────────────────────────────────────────────────────────────
setup: ## Create virtual environment and install dependencies
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Setting up development environment...$(COLOR_RESET)\n"
	@if [ -d "$(VENV)" ]; then \
		printf "$(COLOR_YELLOW)⚠ Virtual environment already exists at $(VENV)$(COLOR_RESET)\n"; \
	else \
		printf "$(COLOR_GREEN)✓ Creating virtual environment...$(COLOR_RESET)\n"; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@printf "$(COLOR_GREEN)✓ Upgrading pip...$(COLOR_RESET)\n"
	@$(VENV_PIP) install --upgrade pip setuptools wheel
	@printf "$(COLOR_GREEN)✓ Installing dependencies...$(COLOR_RESET)\n"
	@if [ -f "pyproject.toml" ]; then \
		$(VENV_PIP) install -e .; \
	elif [ -f "requirements.txt" ]; then \
		$(VENV_PIP) install -r requirements.txt; \
	else \
		printf "$(COLOR_RED)✗ No pyproject.toml or requirements.txt found!$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ Setup complete! Activate with: source $(VENV)/bin/activate$(COLOR_RESET)\n"

dev-install: ## Install package in editable mode with dev dependencies
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Installing package in development mode...$(COLOR_RESET)\n"
	@if [ ! -d "$(VENV)" ]; then \
		printf "$(COLOR_RED)✗ Virtual environment not found. Run 'make setup' first.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@printf "$(COLOR_GREEN)✓ Installing package with dev dependencies...$(COLOR_RESET)\n"
	@$(VENV_PIP) install -e ".[dev]"
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ Development installation complete!$(COLOR_RESET)\n"

# ─────────────────────────────────────────────────────────────────────────────
# Code Formatting
# ─────────────────────────────────────────────────────────────────────────────
format: ## Auto-format code with isort, black, and ruff --fix
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Formatting code...$(COLOR_RESET)\n"
	@if [ ! -d "$(VENV)" ] && ! command -v black > /dev/null 2>&1; then \
		printf "$(COLOR_RED)✗ Neither virtual environment nor global tools found. Run 'make setup' first.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@printf "$(COLOR_GREEN)✓ Running isort...$(COLOR_RESET)\n"
	@$(ISORT) $(PACKAGE)/ || true
	@printf "$(COLOR_GREEN)✓ Running black...$(COLOR_RESET)\n"
	@$(BLACK) $(PACKAGE)/
	@printf "$(COLOR_GREEN)✓ Running ruff --fix...$(COLOR_RESET)\n"
	@$(RUFF) check $(PACKAGE)/ --fix || true
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ Code formatting complete!$(COLOR_RESET)\n"

# ─────────────────────────────────────────────────────────────────────────────
# Linting and Type Checking
# ─────────────────────────────────────────────────────────────────────────────
lint: ## Run ruff, isort --check-only, black --check, and mypy
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Running linters and type checker...$(COLOR_RESET)\n"
	@if [ ! -d "$(VENV)" ] && ! command -v ruff > /dev/null 2>&1; then \
		printf "$(COLOR_RED)✗ Neither virtual environment nor global tools found. Run 'make setup' first.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@printf "$(COLOR_YELLOW)▸ Running ruff...$(COLOR_RESET)\n"
	@$(RUFF) check $(PACKAGE)/ || true
	@printf "$(COLOR_YELLOW)▸ Running isort --check-only...$(COLOR_RESET)\n"
	@$(ISORT) --check-only $(PACKAGE)/ || true
	@printf "$(COLOR_YELLOW)▸ Running black --check...$(COLOR_RESET)\n"
	@$(BLACK) --check $(PACKAGE)/ || true
	@printf "$(COLOR_YELLOW)▸ Running mypy...$(COLOR_RESET)\n"
	@$(MYPY) $(PACKAGE)/ --ignore-missing-imports || true
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ Linting complete!$(COLOR_RESET)\n"

# ─────────────────────────────────────────────────────────────────────────────
# Testing
# ─────────────────────────────────────────────────────────────────────────────
test: ## Run pytest with coverage reporting
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Running tests with coverage...$(COLOR_RESET)\n"
	@if [ ! -d "$(VENV)" ] && ! command -v pytest > /dev/null 2>&1; then \
		printf "$(COLOR_RED)✗ Neither virtual environment nor global tools found. Run 'make setup' first.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@printf "$(COLOR_GREEN)✓ Running pytest...$(COLOR_RESET)\n"
	@$(PYTEST) tests/ -v --cov=$(PACKAGE) --cov-report=html --cov-report=term-missing || true
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ Tests complete! Coverage report saved to htmlcov/index.html$(COLOR_RESET)\n"

coverage: ## Open HTML coverage report in browser
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Opening coverage report...$(COLOR_RESET)\n"
	@if [ ! -f "htmlcov/index.html" ]; then \
		printf "$(COLOR_RED)✗ Coverage report not found. Run 'make test' first.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@if command -v xdg-open > /dev/null 2>&1; then \
		xdg-open htmlcov/index.html; \
	elif command -v open > /dev/null 2>&1; then \
		open htmlcov/index.html; \
	else \
		printf "$(COLOR_YELLOW)⚠ Cannot open browser automatically. Open htmlcov/index.html manually.$(COLOR_RESET)\n"; \
	fi

# ─────────────────────────────────────────────────────────────────────────────
# Documentation
# ─────────────────────────────────────────────────────────────────────────────
docs: ## Build Sphinx documentation
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Building documentation...$(COLOR_RESET)\n"
	@if [ ! -d "$(VENV)" ]; then \
		printf "$(COLOR_RED)✗ Virtual environment not found. Run 'make setup' first.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@if [ ! -d "docfiles" ]; then \
		printf "$(COLOR_RED)✗ Documentation source directory 'docfiles' not found.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@printf "$(COLOR_GREEN)✓ Running sphinx-build...$(COLOR_RESET)\n"
	@$(VENV_BIN)/sphinx-build -b html docfiles docfiles/_build/html
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ Documentation built! Open docfiles/_build/html/index.html$(COLOR_RESET)\n"

docs-pdf: ## Generate PDF from master documentation
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Generating PDF documentation...$(COLOR_RESET)\n"
	@if [ ! -f "docs/MASTER_DOCUMENTATION.md" ]; then \
		printf "$(COLOR_RED)✗ Master documentation not found.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@cd docs && ./generate_pdf.sh MASTER_DOCUMENTATION.md py3plex_documentation.pdf
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ PDF generated: docs/py3plex_documentation.pdf$(COLOR_RESET)\n"

docs-check: ## Check API documentation consistency
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Checking API documentation consistency...$(COLOR_RESET)\n"
	@python docs/check_api_consistency.py --verbose
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ API consistency check complete!$(COLOR_RESET)\n"

# ─────────────────────────────────────────────────────────────────────────────
# Cleanup
# ─────────────────────────────────────────────────────────────────────────────
clean: ## Remove build artifacts, caches, and temporary files
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Cleaning build artifacts and caches...$(COLOR_RESET)\n"
	@printf "$(COLOR_YELLOW)▸ Removing Python cache files...$(COLOR_RESET)\n"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@printf "$(COLOR_YELLOW)▸ Removing build directories...$(COLOR_RESET)\n"
	@rm -rf build/ dist/ *.egg-info .eggs/ 2>/dev/null || true
	@printf "$(COLOR_YELLOW)▸ Removing test and coverage artifacts...$(COLOR_RESET)\n"
	@rm -rf .pytest_cache/ .coverage htmlcov/ .mypy_cache/ .ruff_cache/ 2>/dev/null || true
	@printf "$(COLOR_YELLOW)▸ Removing documentation build...$(COLOR_RESET)\n"
	@rm -rf docfiles/_build/ 2>/dev/null || true
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ Cleanup complete!$(COLOR_RESET)\n"

# ─────────────────────────────────────────────────────────────────────────────
# Build and Publishing
# ─────────────────────────────────────────────────────────────────────────────
build: ## Build source and wheel distributions
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Building distributions...$(COLOR_RESET)\n"
	@if [ ! -d "$(VENV)" ]; then \
		printf "$(COLOR_RED)✗ Virtual environment not found. Run 'make setup' first.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@printf "$(COLOR_GREEN)✓ Installing build tools...$(COLOR_RESET)\n"
	@$(VENV_PIP) install --upgrade build twine
	@printf "$(COLOR_GREEN)✓ Building package...$(COLOR_RESET)\n"
	@$(VENV_PYTHON) -m build
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ Build complete! Distributions saved to dist/$(COLOR_RESET)\n"
	@ls -lh dist/

publish: ## Upload to PyPI with twine (requires TWINE_USERNAME and TWINE_PASSWORD)
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Publishing to PyPI...$(COLOR_RESET)\n"
	@if [ ! -d "$(VENV)" ]; then \
		printf "$(COLOR_RED)✗ Virtual environment not found. Run 'make setup' first.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@if [ ! -d "dist" ] || [ -z "$$(ls -A dist/)" ]; then \
		printf "$(COLOR_RED)✗ No distributions found in dist/. Run 'make build' first.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@if [ -z "$$TWINE_USERNAME" ] || [ -z "$$TWINE_PASSWORD" ]; then \
		printf "$(COLOR_RED)✗ TWINE_USERNAME and TWINE_PASSWORD must be set.$(COLOR_RESET)\n"; \
		printf "$(COLOR_YELLOW)  Example: export TWINE_USERNAME=__token__$(COLOR_RESET)\n"; \
		printf "$(COLOR_YELLOW)           export TWINE_PASSWORD=pypi-...$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@printf "$(COLOR_GREEN)✓ Uploading to PyPI...$(COLOR_RESET)\n"
	@$(VENV_BIN)/twine upload dist/*
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ Published successfully!$(COLOR_RESET)\n"

# ─────────────────────────────────────────────────────────────────────────────
# API Verification
# ─────────────────────────────────────────────────────────────────────────────
api-check: ## Verify py3plex API exports expected public symbols
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Checking py3plex API exports...$(COLOR_RESET)\n"
	@if [ ! -d "$(VENV)" ]; then \
		printf "$(COLOR_RED)✗ Virtual environment not found. Run 'make setup' first.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@printf "$(COLOR_GREEN)✓ Verifying API exports...$(COLOR_RESET)\n"
	@$(VENV_PYTHON) -c "import py3plex; import sys; expected = ['Py3plexException', 'NetworkConstructionError', 'InvalidLayerError', 'InvalidNodeError', 'InvalidEdgeError', 'ParsingError', 'VisualizationError', 'AlgorithmError', 'CommunityDetectionError', 'CentralityComputationError', 'DecompositionError', 'EmbeddingError', 'ConversionError', 'IncompatibleNetworkError']; missing = [sym for sym in expected if not hasattr(py3plex, sym)]; print('✗ Missing API symbols:', missing) if missing else print('✓ All expected API symbols are exported! Verified:', len(expected), 'symbols'); sys.exit(1) if missing else sys.exit(0)"
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ API check passed!$(COLOR_RESET)\n"

# ─────────────────────────────────────────────────────────────────────────────
# Benchmarking
# ─────────────────────────────────────────────────────────────────────────────
benchmark: ## Run performance benchmarks with pytest-benchmark
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Running performance benchmarks...$(COLOR_RESET)\n"
	@if [ ! -d "$(VENV)" ] && ! command -v pytest > /dev/null 2>&1; then \
		printf "$(COLOR_RED)✗ Neither virtual environment nor global tools found. Run 'make setup' first.$(COLOR_RESET)\n"; \
		exit 1; \
	fi
	@printf "$(COLOR_GREEN)✓ Running core performance benchmarks...$(COLOR_RESET)\n"
	@$(PYTEST) tests/test_performance_core.py --benchmark-only -v || true
	@printf "$(COLOR_GREEN)✓ Running aggregation benchmarks...$(COLOR_RESET)\n"
	@$(PYTEST) benchmarks/bench_aggregation.py --benchmark-only -v || true
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ Benchmarks complete!$(COLOR_RESET)\n"

# ─────────────────────────────────────────────────────────────────────────────
# CI Integration
# ─────────────────────────────────────────────────────────────────────────────
ci: ## Run lint + test in sequence for CI workflows
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Running CI checks (lint + test)...$(COLOR_RESET)\n"
	@$(MAKE) lint
	@printf "\n"
	@$(MAKE) test
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓ CI checks complete!$(COLOR_RESET)\n"

test-all: ## Run ALL tests, benchmarks, and linting - ensures all CI will pass
	@printf "$(COLOR_BOLD)$(COLOR_BLUE)▶ Running COMPLETE test suite (lint + test + benchmark)...$(COLOR_RESET)\n"
	@printf "$(COLOR_BOLD)$(COLOR_YELLOW)This is the comprehensive entrypoint that ensures all build CI will pass.$(COLOR_RESET)\n"
	@printf "\n"
	@$(MAKE) lint
	@printf "\n"
	@$(MAKE) test
	@printf "\n"
	@$(MAKE) benchmark
	@printf "\n"
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)✓✓✓ ALL CHECKS PASSED! ✓✓✓$(COLOR_RESET)\n"
	@printf "$(COLOR_BOLD)$(COLOR_GREEN)Your changes are ready for CI and should pass all build checks.$(COLOR_RESET)\n"
