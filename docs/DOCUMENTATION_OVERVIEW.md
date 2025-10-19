# Py3plex Documentation Overview

## Purpose

This document provides an overview of the Py3plex documentation ecosystem, explaining what each documentation resource offers and when to use it.

## Documentation Resources

### 1. Master Documentation (MASTER_DOCUMENTATION.md)

**Location**: `docs/MASTER_DOCUMENTATION.md`

**Purpose**: Comprehensive, publication-quality documentation covering all aspects of Py3plex in a single, well-organized document.

**Best for**:
- Learning Py3plex from scratch
- Understanding core concepts and architecture
- Finding detailed API references with examples
- Getting started with interactive examples
- Contributing to the project

**Features**:
- ✅ Complete overview and "Why Py3plex?"
- ✅ Quick start with installation and minimal examples
- ✅ In-depth core module documentation
- ✅ Interactive Jupyter-ready examples
- ✅ Advanced usage patterns
- ✅ Contributing guidelines
- ✅ Full API reference with edge cases
- ✅ Citations and academic references

**Export**: Can be converted to PDF using `make docs-pdf` or `cd docs && ./generate_pdf.sh`

### 2. Sphinx Documentation

**Location**: `docfiles/*.rst` (source), `https://skblaz.github.io/py3plex/` (hosted)

**Purpose**: Auto-generated API reference with cross-references and search functionality.

**Best for**:
- Browsing API documentation with search
- Finding specific function/class documentation
- Viewing auto-generated API docs from docstrings
- Cross-referenced documentation navigation

**Build**: `make docs` or `cd docfiles && make html`

### 3. LLM Context File (LLM.md)

**Location**: `LLM.md`

**Purpose**: Comprehensive context for LLMs and maintainers, including development status, architecture decisions, and implementation details.

**Best for**:
- Understanding project architecture
- Learning about development status and roadmap
- Finding implementation details and design decisions
- LLM-assisted development and maintenance

### 4. Quick Reference Guides

**Location**: `docs/`

**Individual Guides**:
- **10min_tutorial.md** - Quick 10-minute introduction
- **QUICK_REFERENCE.md** - Common operations cheat sheet
- **ALGORITHM_CITATIONS.md** - Academic references with DOIs
- **ARCHITECTURE.md** - System design and architecture
- **CONTRIBUTING.md** - Contribution guidelines
- **development.md** - Development workflow
- **algorithm_selection_guide.md** - Algorithm selection guide
- **MULTILAYER_FORMULAS_QUICK_REFERENCE.md** - Mathematical formulas
- **multilayer_centrality_tutorial.md** - Centrality measures tutorial
- **multilayer_modularity_tutorial.md** - Modularity tutorial

**Best for**:
- Quick lookups and reference
- Specific topics (algorithms, formulas, development)
- Understanding mathematical foundations

### 5. Example Scripts

**Location**: `examples/`

**Purpose**: 52 working Python scripts demonstrating real-world usage.

**Best for**:
- Seeing working code examples
- Copy-paste starting points
- Understanding practical applications
- Testing features

**Key Examples**:
- `tutorial_10min.py` - Executable tutorial
- `example_random_walks.py` - Random walks and Node2Vec
- `example_multilayer_visualization.py` - Visualization
- `example_community_detection.py` - Community detection
- `example_network_decomposition.py` - Meta-path features
- `example_multilayer_statistics.py` - Multilayer metrics

### 6. Main README

**Location**: `README.md`

**Purpose**: Project introduction, installation, and quick start.

**Best for**:
- First-time visitors
- Installation instructions
- Quick start examples
- License information

## Documentation Hierarchy

### For New Users
1. Start with **README.md** for installation
2. Follow **10min_tutorial.md** or **MASTER_DOCUMENTATION.md** Quick Start
3. Explore **examples/** for practical use cases
4. Refer to **MASTER_DOCUMENTATION.md** for in-depth learning

### For Developers
1. Read **CONTRIBUTING.md** for contribution guidelines
2. Review **development.md** for development workflow
3. Check **ARCHITECTURE.md** for design decisions
4. Use **LLM.md** for comprehensive context
5. Run `make docs-check` to verify API documentation

### For Researchers
1. Start with **MASTER_DOCUMENTATION.md** for comprehensive overview
2. Check **ALGORITHM_CITATIONS.md** for references
3. Review **MULTILAYER_FORMULAS_QUICK_REFERENCE.md** for mathematical details
4. Explore specific tutorials (centrality, modularity)
5. Cite using references in **MASTER_DOCUMENTATION.md**

### For Quick Reference
1. Use **QUICK_REFERENCE.md** for common operations
2. Check **algorithm_selection_guide.md** for algorithm choice
3. Browse **Sphinx documentation** for API details

## Documentation Maintenance

### Generating Documentation

**Sphinx HTML Documentation**:
```bash
make docs
# Output: docfiles/_build/html/index.html
```

**PDF from Master Documentation**:
```bash
make docs-pdf
# Output: docs/py3plex_documentation.pdf
# Requires: pandoc, xelatex
```

**API Consistency Check**:
```bash
make docs-check
# Checks for undocumented functions and missing docstrings
```

### Documentation Quality Metrics

Run the API consistency checker:
```bash
python docs/check_api_consistency.py --verbose
```

This reports:
- Functions missing docstrings
- Functions missing Args/Returns/Example sections
- Functions missing type hints

### Adding New Documentation

1. **For API changes**: Update docstrings in source code
2. **For tutorials**: Add to `docs/` or `docfiles/tutorials/`
3. **For examples**: Add to `examples/` with clear comments
4. **For reference**: Update relevant guide in `docs/`

### Documentation Standards

All documentation should follow:
- **Style**: Google Python Style Guide
- **Tone**: Scientific but approachable
- **Structure**: Self-contained sections
- **Code**: Runnable examples with expected output
- **Line length**: < 80 characters for PDF export
- **Examples**: Real, tested code using actual APIs

## Common Tasks

### I want to learn Py3plex
→ Read **MASTER_DOCUMENTATION.md** sections 1-2 (Overview, Quick Start)

### I need API documentation for a function
→ Check **MASTER_DOCUMENTATION.md** API Reference or browse **Sphinx docs**

### I want to run a quick example
→ Browse **examples/** directory and run a script

### I'm contributing code
→ Read **CONTRIBUTING.md** and **development.md**

### I need to cite Py3plex
→ See **MASTER_DOCUMENTATION.md** Citations section or **ALGORITHM_CITATIONS.md**

### I need mathematical formulas
→ Check **MULTILAYER_FORMULAS_QUICK_REFERENCE.md**

### I want algorithm references
→ See **ALGORITHM_CITATIONS.md** with DOIs

### I'm debugging or extending
→ Read **LLM.md** and **ARCHITECTURE.md**

## Documentation Updates

**Last Major Update**: October 2025
- Added MASTER_DOCUMENTATION.md (comprehensive documentation)
- Added PDF generation script (docs/generate_pdf.sh)
- Added API consistency checker (docs/check_api_consistency.py)
- Updated Makefile with documentation targets
- Updated all documentation cross-references

**Documentation Status**:
- ✅ Master documentation complete and comprehensive
- ✅ Sphinx documentation builds cleanly (16 minor warnings)
- ✅ 52 example scripts available
- ✅ All major modules have tutorial coverage
- ⚠️ ~1000 functions need improved docstrings (tracked by API checker)

## Getting Help

### Documentation Issues
If you find errors or gaps:
1. Check existing [GitHub issues](https://github.com/SkBlaz/py3plex/issues)
2. Create new issue with `documentation` label
3. Consider submitting a PR with fixes

### Usage Questions
For questions about using Py3plex:
1. Check examples in `examples/` directory
2. Search [closed issues](https://github.com/SkBlaz/py3plex/issues?q=is%3Aissue+is%3Aclosed)
3. Open a [discussion](https://github.com/SkBlaz/py3plex/discussions)
4. Create issue with `question` label

## License

Documentation licensed under the same terms as Py3plex (MIT License).

---

**For the most comprehensive documentation, start with**: `docs/MASTER_DOCUMENTATION.md`

**For quick reference**: `docs/QUICK_REFERENCE.md`

**For development**: `docs/development.md` and `CONTRIBUTING.md`

**For API details**: https://skblaz.github.io/py3plex/
