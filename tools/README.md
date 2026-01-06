# Quality Analysis Tools

This directory contains tools for analyzing code quality, detecting dead code, finding duplications, and maintaining clean module boundaries in py3plex.

## Quick Start

```bash
# Run all quality checks
python -m tools.quality.runner --tools all

# Run specific checks
python -m tools.quality.runner --tools import examples api

# Check module boundaries (strict, fails on violations)
python -m tools.quality.layer_checker .

# Check for regressions against baseline
python -m tools.quality.baseline
```

## Tools

### Import Graph Analyzer (`import_graph.py`)
Analyzes module dependencies to create a DAG of imports.

**Output:** `build/quality/import_graph.json`

**Use case:** Understand module structure, find circular dependencies, identify unused modules.

### Dead Code Detector (`dead_code.py`)
Detects potentially dead code using multi-signal scoring:
- Unreferenced symbols (ripgrep search)
- Not exported in `__all__`
- Not imported anywhere
- No test coverage

**Output:** `build/quality/dead_code.json`

**Score:** 0-1, higher = more likely dead
- ≥0.7: High confidence (consider removal)
- 0.4-0.7: Medium confidence (review)
- <0.4: Low confidence (likely false positive)

**Whitelist:** Add false positives to `tools/whitelist.yml`

### Redundancy Detector (`redundancy.py`)
Finds duplicate code at three levels:
1. **Exact:** Identical normalized code
2. **Near:** 80%+ token similarity
3. **Semantic:** Same signature + similar structure

**Output:** `build/quality/redundancy.json`

**Use case:** Find opportunities to consolidate helpers, reduce duplication.

### Public API Auditor (`api_audit.py`)
Audits the public API surface, tracking:
- Symbols exported from `__all__`
- Usage in examples
- Usage in documentation
- Internal usage count

Assigns stability tiers:
- **Core:** Used in docs, examples, heavily internal
- **Supported:** Used in docs or examples
- **Experimental:** Exported but not documented
- **Internal:** Not exported

**Output:** `build/quality/public_api.json`

### Examples Health Checker (`examples_health.py`)
Validates example scripts:
- Syntax check (compile)
- Import check
- Extracts APIs used

**Output:** `build/quality/examples_health.json`

**Use case:** Detect stale examples after API changes.

### Docs Health Checker (`docs_health.py`)
Scans documentation for code references:
- Extracts code blocks from RST/Markdown
- Finds py3plex symbol references
- Validates references (placeholder for full validation)

**Output:** `build/quality/docs_health.json`

### Layer Boundary Checker (`layer_checker.py`)
Enforces module layering rules from `pyproject.toml`:
- DSL must not import heavy algorithm modules
- Algorithms must not import DSL
- Datasets must not import visualization
- Uncertainty should be dependency-light

**Output:** `build/quality/layer_violations.json`

**CI:** Fails CI on any violations (strict enforcement).

### Baseline Comparison (`baseline.py`)
Compares current metrics against baseline:
- Grandfathers existing issues
- Blocks regressions above threshold
- Allows gradual improvement

**Thresholds:**
- Dead code: +5 allowed
- Redundancy: +3 allowed
- Layer violations: +0 (strict)

**Usage:**
```bash
# Update baseline (run once or after fixes)
python -m tools.quality.baseline --update-baseline

# Check for regressions (in CI)
python -m tools.quality.baseline
```

## Whitelist Configuration

`tools/whitelist.yml` contains symbols that appear dead but are actually used:

```yaml
plugin_entrypoints:
  - MyPlugin        # Loaded dynamically

cli_commands:
  - my_command      # Used via Click

reflection_used:
  - __version__     # Accessed via getattr

registries:
  - MyRegistry      # Auto-registered

side_effect_modules:
  - py3plex.logging_config  # Imported for side effects
```

## CI Integration

Quality checks run automatically on every PR via `.github/workflows/code-quality.yml`:

1. **Lint check:** Standard linting (existing)
2. **Quality gates:** New job that runs:
   - Import graph analysis
   - Examples health check
   - API audit
   - Layer boundary check (strict)

**Artifacts:** Quality reports uploaded as CI artifacts (30-day retention).

## Module Layering Rules

Defined in `pyproject.toml` under `[tool.py3plex.layering]`:

```toml
[tool.py3plex.layering]
dsl_forbidden_imports = [
    "py3plex.algorithms.statistics",
    "py3plex.algorithms.community_detection",
]
algorithms_forbidden_imports = [
    "py3plex.dsl",
]
datasets_forbidden_imports = [
    "py3plex.visualization",
]
uncertainty_forbidden_imports = [
    "py3plex.visualization",
]
```

**Rationale:**
- **DSL independence:** Keep DSL lightweight, avoid heavy algorithm dependencies
- **Separation of concerns:** Algorithms shouldn't depend on query language
- **Optional dependencies:** Keep visualization dependencies optional

## Output Format

All tools produce JSON with stable, deterministic output suitable for:
- CI/CD integration
- Diff-based change detection
- Automated analysis

**Location:** `build/quality/*.json`

**Git:** Reports are ignored (`.gitignore`), except `quality_baseline.json` which is tracked.

## Development

### Adding a New Tool

1. Create `tools/quality/new_tool.py`
2. Implement with `analyze()` and `save_to_json()` methods
3. Add to `runner.py` tool choices
4. Add tests to `tests/test_quality_tools.py`
5. Document in this README and AGENTS.md

### Testing

```bash
# Run quality tool tests
pytest tests/test_quality_tools.py -v

# Test on synthetic fixtures (fast)
pytest tests/test_quality_tools.py::test_dead_code_detector -v

# Test JSON stability
pytest tests/test_quality_tools.py::test_json_output_stable -v
```

### Best Practices

1. **Stable output:** Sort keys, deterministic ordering
2. **Conservative detection:** Prefer false negatives over false positives
3. **Clear actions:** Suggest specific remediation steps
4. **Fast execution:** Optimize for large codebases (299 Python files)
5. **Whitelist support:** Always provide escape hatch for false positives

## Documentation

**Primary docs:**
- `AGENTS.md` - "Code Quality and Crispness Workflow" section
- `docfiles/contributing.rst` - "Quality Gates and Code Maintenance" section

**Quick reference:**
- Module layering: `pyproject.toml` `[tool.py3plex.layering]`
- Whitelist: `tools/whitelist.yml`
- CI workflow: `.github/workflows/code-quality.yml`

## Metrics Summary (Current)

As of latest run:
- **Modules analyzed:** 292
- **Import edges:** 215
- **Examples checked:** 151 (100% healthy)
- **Dead code candidates:** 1,327 (0 high-confidence)
- **Layer violations:** 1 (to be addressed)

**Interpretation:**
- Conservative dead code detection (working as intended)
- Examples are well-maintained
- One layer violation identified for cleanup
