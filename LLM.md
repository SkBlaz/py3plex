# Py3plex - LLM Context Summary

**Last Updated**: 2025-10-28  
**Purpose**: Comprehensive context file for LLMs and maintainers working with the py3plex repository  
**Repository**: Multilayer network analysis library with visualization, algorithms, and statistical tools

---

## 🎯 Quick Status

| Metric | Status | Details |
|--------|--------|---------|
| **Code Quality** | ✅ Excellent (8.5/10) | Production-ready, comprehensive testing |
| **Type Coverage** | ✅ 65.9% | Mypy clean, automated tracking |
| **Doc Coverage** | ✅ 50.9% | Sphinx docs, API reference |
| **Test Status** | ✅ All Passing | 40+ test files, property-based tests |
| **CI/CD** | ✅ Green | Tests, benchmarks, verification, fuzzing |
| **Active TODOs** | 3 items | See priority list below |

---

## 🚨 Active TODOs (Priority Order)

### 1. Test Coverage Enhancement (High Priority)
- **Goal**: Measure and increase to 50%+ code coverage
- **Current**: Good core coverage, untested edge cases
- **Action**:
  ```bash
  pytest --cov=py3plex --cov-report=html
  # Focus on: py3plex/algorithms/, error handling, visualization edge cases
  ```
- **Tools**: pytest-cov for measurement
- **Strategy**: Target modules with <30% coverage first

### 2. Refactor Remaining Long Functions (Medium Priority)
- **Targets**:
  - `hairball_plot()` in `visualization/hairball.py` (164 lines)
  - `draw_multiedges()` in `visualization/multilayer.py` (120 lines)
- **Goal**: Break into helper functions (<100 lines each)
- **Impact**: Improved maintainability, testability

### 3. Complete Type Hints (Low Priority)
- **Target**: Remaining methods in `core/multinet.py`
- **Status**: 7 core methods completed, others can be added incrementally
- **Impact**: Better IDE support, fewer type-related bugs

---

## 📋 Recent Changes (Last 5)

### 2025-10-25: Link Fixes & Documentation
- Fixed 8 broken internal links in LLM.md (emoji-decorated headers)
- All 61 internal navigation links now working
- Documentation coverage: 30.7% → 50.9% (+188 functions, +24 classes)

### 2025-10-24: Type Coverage Tracking (Issue #211)
- Added `docs/check_type_coverage.py` script (302 lines)
- GitHub Actions workflow for automated tracking
- Current baseline: 65.91% precisely typed (17,444/26,465 LOC)

### 2025-10-23: Code Quality Improvements
- Performance profiling module: `py3plex/profiling.py` (335 lines)
- Property-based testing: `tests/test_algorithm_properties.py` (10 tests)
- Function refactoring: `draw_multilayer_default()` 194→117 lines

### 2025-10-22: Formal Verification & Fuzzing
- CrossHair + icontract integration (8 modules verified)
- Atheris-based fuzzing infrastructure (`fuzzing/` directory)
- 15+ core invariants verified symbolically

### 2025-10-21: Type Coverage & Testing
- Fixed all mypy errors: 43 → 0 errors
- Network conversion test suite (Issue #177, 8 tests)
- CLI logging conversion: 78 print statements → structured logging

**📦 Complete Changelog**: See [CHANGELOG.md](CHANGELOG.md) for full history

---

## 📖 Repository Overview

### Purpose & Scope
Py3plex is a Python library for multilayer network analysis, visualization, and statistical comparison. It targets research-scale networks (10³-10⁵ nodes) with:
- Multilayer/multiplex network data structures
- Community detection algorithms
- Statistical analysis and comparison
- Visualization tools (force-directed, hierarchical, custom layouts)

### Key Features
- **Core Data Structure**: `multi_layer_network` (NetworkX-based)
- **Algorithms**: Community detection, centrality, node ranking, embeddings
- **Visualization**: Multilayer layouts, hairball plots, Sankey diagrams
- **I/O**: Multiple formats (GraphML, GML, edgelist, pickle, CSV)
- **CLI**: Command-line interface for common operations
- **Statistical Tools**: Network comparison, hypothesis testing, effect sizes

---

## 🏗️ Architecture

### Directory Structure
```
py3plex/
├── core/              # Core data structures (multinet.py, parsers.py, converters.py)
├── algorithms/        # Network algorithms
│   ├── community_detection/
│   ├── statistics/
│   ├── node_ranking/
│   └── multilayer_algorithms/
├── visualization/     # Visualization tools (multilayer.py, hairball.py, colors.py)
├── wrappers/         # External tool wrappers (node2vec, embeddings)
├── io/               # I/O operations (schema.py, api.py)
└── cli.py            # Command-line interface

tests/                # 40+ test files
docs/                 # Sphinx documentation
examples/             # 50+ usage examples
```

### Key Files
1. **`py3plex/core/multinet.py`** (1223 lines) - Central data structure
2. **`py3plex/algorithms/statistics/multilayer_statistics.py`** - Statistical measures
3. **`py3plex/visualization/multilayer.py`** (859 lines) - Multilayer visualization
4. **`py3plex/cli.py`** (450 lines) - Command-line interface
5. **`py3plex/config.py`** - Configuration constants (colors, defaults)

### Data Flow
```
Input (CSV/GraphML/GML) 
  → Parser (core/parsers.py)
  → multi_layer_network (core/multinet.py)
  → Algorithms (algorithms/*)
  → Visualization (visualization/*)
  → Output (images, statistics, files)
```

---

## 🛠️ Development Environment

### Installation
```bash
# Git-only installation (PyPI deprecated)
pip install git+https://github.com/SkBlaz/py3plex.git

# Verify installation
py3plex selftest
```

### Testing & Quality
```bash
# Run everything (tests, benchmarks, linters)
make test-all

# Individual commands
make test       # pytest tests/
make benchmark  # performance benchmarks
make lint       # black, flake8, mypy
make format     # auto-format with black

# Coverage
pytest --cov=py3plex --cov-report=html

# Type coverage
make type-coverage

# Formal verification (CrossHair)
crosshair check py3plex/multinet/aggregation.py --per_path_timeout=20

# Fuzzing (optional, requires atheris)
make fuzz-quick  # 1-minute test
```

### CI/CD Workflows
- **tests.yml**: pytest on Python 3.8-3.12, Ubuntu/macOS/Windows
- **benchmarks.yml**: Performance tracking
- **code-quality.yml**: Black, flake8, mypy
- **doc-coverage.yml**: Documentation coverage tracking
- **type-coverage.yml**: Type annotation coverage
- **verify.yml**: Formal verification (CrossHair + icontract)
- **fuzzing.yml**: Atheris-based fuzz testing

---

## 📚 Core Concepts

### Multilayer Networks
- **Layers**: Different types of relationships (e.g., collaboration, friendship, citation)
- **Nodes**: Can exist in multiple layers
- **Edges**: Intra-layer (within layer) and inter-layer (between layers)
- **Supra-adjacency**: Unified matrix representation of all layers

### Key Algorithms
1. **Community Detection**: Louvain, label propagation, Infomap (AGPLv3)
2. **Centrality**: Degree, betweenness, closeness, PageRank, HITS
3. **Statistics**: Density, coupling strength, node activity, entropy
4. **Embeddings**: Node2Vec, Word2Vec wrappers
5. **Comparison**: Statistical tests, effect sizes, multiple comparison corrections

### Statistical Framework (2025-10-26)
New module: `py3plex/algorithms/statistics/stats_comparison.py`
- 5 statistical tests: permutation, t-test, Mann-Whitney U, ANOVA, Kruskal-Wallis
- Effect sizes: Cohen's d, eta-squared
- Multiple comparison corrections: Bonferroni, Holm, FDR
- 6 built-in metrics + custom metric support

---

## 🔍 Known Limitations & Best Practices

### Scalability
- **Target Scale**: 10³-10⁵ nodes (research-scale networks)
- **Force-directed layouts**: ~5k nodes max (use alternatives for larger)
- **Supra-adjacency matrices**: Sparse by default, 10k+ nodes need memory
- **Visualization**: O(n²) for some operations (alternatives suggested)

### Dependencies
- **Core**: NetworkX, NumPy, SciPy, matplotlib, scikit-learn
- **Optional**: plotly (viz), python-louvain (algos), infomap (AGPLv3)
- **Dev**: pytest, black, mypy, CrossHair, atheris

### Common Issues
1. **"Could not load network"**: Check CSV format (source, target, layer columns)
2. **"No module named 'tensorly'"**: Install optional dependency if needed
3. **Matplotlib backend issues**: Set `matplotlib.use('Agg')` for headless
4. **Pickle security**: Only load trusted .gpickle files (arbitrary code execution risk)

### Best Practices
- Use sparse matrices for large networks (automatic by default)
- Sample nodes for visualization (>1000 nodes)
- Use virtual environment for installation
- Run `make test-all` before committing
- Add type hints to new code
- Include docstrings with examples

---

## 🔒 Security & Licensing

### License
- **Main Library**: MIT (permissive, commercial-friendly)
- **Infomap**: AGPLv3 (viral, requires open-sourcing derived works)
- **Recommendation**: Use Louvain/label propagation for commercial projects

### Security Considerations
- **Pickle Loading**: `.gpickle` files can execute arbitrary code (document risk)
- **Path Traversal**: Validate file paths in CLI (low risk, added validation)
- **Resource Exhaustion**: No hard limits on network size (add for CLI if needed)
- **No eval()/exec()**: ✅ Safe from code injection

---

## 🧪 Testing & Verification

### Test Coverage
- **40+ test files** covering core, algorithms, I/O, CLI
- **Property-based tests**: Hypothesis-powered invariant validation
- **Network conversion**: 8 tests for format roundtrips
- **Fuzzing**: Atheris-based input validation (fuzzing/ directory)

### Formal Verification (CrossHair + icontract)
- **8 modules** with contracts (aggregation, stats, random generation, utils)
- **15+ invariants** verified symbolically
- **Optional**: icontract gracefully degrades if not installed
- **CI Integration**: Automated verification on push/PR

### Key Invariants Verified
- Node preservation in aggregation
- Non-negative weights
- Type safety (NetworkX graphs, numpy Generators)
- Density/activity bounds [0,1]
- Degree non-negativity
- Layout completeness

---

## 🤖 For LLM Assistants

### When Helping Users
1. **Installation**: Always suggest git-based installation, not PyPI
2. **CSV Format**: Verify source, target, layer columns
3. **Common Errors**: Check error message guide above
4. **NetworkX Export**: Use `network.core_network` or `to_nx_network()`

### When Making Changes
1. **Read First**: Check core/multinet.py for data structure patterns
2. **Follow Patterns**: Google-style docstrings, PEP 8 formatting
3. **Add Tests**: All new functionality needs tests
4. **Type Hints**: Add to new code (mypy must pass)
5. **Run Checks**: `make test-all` before committing

### Code Quality Standards
- ✅ Type hints: Use for new code
- ✅ Docstrings: Google-style with examples
- ✅ Testing: pytest for all new features
- ✅ Formatting: black (auto-format)
- ✅ Linting: flake8, mypy (zero errors)
- ✅ Functions: <100 lines (refactor if longer)

---

## 📞 Quick Reference

### Common Commands
```bash
# Installation & verification
pip install git+https://github.com/SkBlaz/py3plex.git
py3plex selftest

# Testing & quality
make test-all           # Run everything
pytest tests/           # Unit tests only
make benchmark          # Performance tests
make lint               # Linters
pytest --cov=py3plex    # Coverage report

# Development
make format             # Auto-format code
make type-coverage      # Type hint coverage
crosshair check py3plex # Formal verification

# CLI usage
py3plex --help
py3plex load network.csv --format multiedgelist
```

### Key Python Patterns
```python
# Create multilayer network
from py3plex.core import multinet
network = multinet.multi_layer_network()
network.load_network("data.csv", input_type="multiedgelist")

# Basic statistics
network.basic_stats()

# Visualization
from py3plex.visualization.multilayer import draw_multilayer_default
draw_multilayer_default(network.get_layers(), display=True)

# Export to NetworkX
nx_graph = network.core_network
```

---

## 📄 Additional Resources

- **Documentation**: https://skblaz.github.io/py3plex/
- **GitHub**: https://github.com/SkBlaz/py3plex
- **Examples**: https://github.com/SkBlaz/py3plex/tree/main/examples
- **Paper**: Škrlj et al. (2019), Applied Network Science
- **Full Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Master Documentation**: [MASTER_DOCUMENTATION.md](MASTER_DOCUMENTATION.md)

---

**Document Statistics**:
- **Length**: ~550 lines (was 4,418 - 88% reduction)
- **Focus**: Active TODOs, essential context, quick reference
- **Maintenance**: Update with significant changes only

---

*End of LLM Context Summary - For detailed history, see CHANGELOG.md*
