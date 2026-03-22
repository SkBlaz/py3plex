# GUI API Tests

This directory contains automated tests for the Py3plex GUI API.

## Test Files

### `test_health.py`
Basic health check test to verify the API is running correctly.

**What it tests:**
- API responds to health endpoint
- Returns correct status and version

**Run:**
```bash
pytest test_health.py
```

---

### `test_upload.py`
Tests file upload functionality.

**What it tests:**
- Upload endpoint accepts edgelist files
- Returns graph ID and confirmation message

**Run:**
```bash
pytest test_upload.py
```

---

### `test_multiedgelist_parsing.py` NEW
Comprehensive unit tests for multi-edgelist parsing improvements.

**What it tests:**
- Comment handling (lines starting with #)
- Simple 2-column edgelist support
- Edge weight parsing
- Default weight assignment
- MultiGraph to Graph conversion
- Empty line handling

**Run:**
```bash
pytest test_multiedgelist_parsing.py -v

# Or run directly:
python test_multiedgelist_parsing.py
```

**Coverage:** 6 test cases covering all friction points identified in the GUI user journey analysis.

---

### `test_user_journey_centrality.py` NEW
Integration test simulating complete user journey for multi-edgelist centrality analysis.

**What it tests:**
- Complete workflow: Upload → Summary → Centrality → Results
- Multi-layer network support
- All centrality metrics (degree, betweenness, closeness, eigenvector, pagerank)
- Job status polling and completion
- Error handling for missing graphs
- Multiple edgelist format variations

**Run:**
```bash
# Requires TestClient (installed with pytest)
pytest test_user_journey_centrality.py -v

# Note: Some tests may require Celery workers for full integration
# See gui/README.md for Docker setup instructions
```

**Use Cases Tested:**
1. Full user journey from upload to results
2. All centrality metrics on multi-layer networks
3. Various edgelist format variations
4. Error scenarios (missing graphs)

---

## Quick Start

### Install Dependencies

```bash
cd gui/api
pip install -e .
pip install pytest httpx pytest-asyncio pytest-timeout
```

### Run All Tests

```bash
# From repository root
pytest gui/ci/api-tests/ -v

# With coverage
pytest gui/ci/api-tests/ --cov=app --cov-report=term-missing
```

### Run Specific Tests

```bash
# Unit tests only (fast, no Docker needed)
pytest gui/ci/api-tests/test_multiedgelist_parsing.py

# Integration tests (may need Docker)
pytest gui/ci/api-tests/test_user_journey_centrality.py
```

---

## Test Categories

### Unit Tests
- **Fast** (~1 second)
- **No dependencies** (no Docker, Redis, or Celery)
- **Focused** on specific functions
- Files: `test_multiedgelist_parsing.py`

### Integration Tests  
- **Slower** (~5-30 seconds)
- **Requires services** (may need Docker stack)
- **End-to-end** workflows
- Files: `test_user_journey_centrality.py`, `test_upload.py`

### Smoke Tests
- **Very fast** (< 1 second)
- **Basic checks** only
- Files: `test_health.py`

---

## CI/CD Integration

These tests run automatically in GitHub Actions:

**Workflow:** `.github/workflows/gui-tests.yml`

**When:**
- Push to main/master/develop (if GUI files changed)
- Pull requests targeting main/master/develop
- Manual workflow dispatch

**Jobs:**
1. Quick validation (syntax, types)
2. Unit tests
3. Integration tests (full Docker stack)

---

## Troubleshooting

### Import Errors

Make sure you're in the right directory and have installed dependencies:

```bash
cd gui/api
pip install -e .
export PYTHONPATH="${PYTHONPATH}:/path/to/gui/api"
```

### Permission Errors

If tests fail with permission errors for `/data`:

```bash
# The code now handles this automatically by falling back to tempdir
# But you can also set an environment variable:
export DATA_DIR=/tmp/py3plex-test-data
```

### TestClient Errors

If you get errors about TestClient:

```bash
# Reinstall with correct versions
pip install "httpx>=0.25.0" "fastapi[all]>=0.109.0"
```

---

## Related Documentation

- **Interactive Demo:** `../demo_improvements.py`
- **GUI Setup:** `../README.md`
- **API Documentation:** Access at `http://localhost:8080/api/docs` when running

---

## Contributing

When adding new tests:

1. **Unit tests** for individual functions → `test_*_unit.py`
2. **Integration tests** for workflows → `test_*_journey.py`
3. Add docstrings explaining what is tested
4. Run locally before committing
5. Update this README if adding new test categories

---

**Last Updated:** 2025-11-10  
**Test Count:** 10+ test cases  
**Status:** All passing
