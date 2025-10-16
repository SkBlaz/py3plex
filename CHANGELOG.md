# Changelog

All notable changes to py3plex will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CHANGELOG.md to track changes systematically
- Python 3.12 support in CI test matrix
- Optional dependency groups in pyproject.toml: `[infomap]`, `[algos]`, `[viz]`
- README.md section documenting optional dependencies installation
- Type hints coverage increased to 65.4% (70 of 107 maintainable modules)
- Custom exception types module (`py3plex/exceptions.py`) with 13 domain-specific exceptions
- Pre-commit hooks configuration
- Logging infrastructure across core modules
- Unified random seeding helper (`get_rng()` in `py3plex.utils`)
- Seed parameters added to layout algorithms (`compute_force_directed_layout`, `compute_random_layout`)
- Seed parameter added to `infomap_communities()` wrapper
- Algorithm selection guide (`docs/algorithm_selection_guide.md`)
- Complexity documentation for key algorithms (louvain_multilayer)
- `bin/README.md` with installation instructions for external binaries
- **NEW**: Centralized configuration module (`py3plex/config.py`) with visualization, color schemes, and layout settings
- **NEW**: Deprecation utilities (`deprecated` decorator and `warn_if_deprecated()` in `py3plex.utils`)
- **NEW**: `__api_version__` attribute in main package for downstream tool compatibility
- **NEW**: CODEOWNERS file for GitHub code review automation
- **NEW**: Algorithm citations document (`docs/ALGORITHM_CITATIONS.md`) with proper academic references
- **NEW**: Color-blind safe color palettes (ColorBrewer and Wong palettes)
- **NEW**: Validation utility (`validate_multilayer_input()`) for input sanity checks
- **NEW**: Comprehensive test suite for config module and API improvements

### Changed
- Modern build system with pyproject.toml (PEP 517/518/621 compliance)
- Comprehensive Makefile-based development workflow
- Sphinx documentation version updated to 0.95a (from 0.80)
- Updated all dependencies to modern versions compatible with Python 3.8+
  - numpy 1.19+, scipy 1.5+, matplotlib 3.3+, gensim 4.0+, scikit-learn 0.24+
- Converted 170 of 229 print statements to logging (74% completion)
- Fixed all 50 bare except clauses with specific exception types
- Removed 8 wildcard imports (from 9 to 1)
- Examples updated to handle missing binaries gracefully with try/except blocks
- Default binary paths changed from `../bin/` to `.` (assumes in PATH or current directory)
- Enhanced `__init__.py` with proper module docstring and version exports

### Removed
- **BREAKING**: Bundled Infomap and Node2Vec binaries (~5MB reduction)
  - **Migration**: Install binaries separately or use pure Python alternatives
  - See `bin/README.md` for installation instructions
  - Louvain algorithm remains available as a built-in alternative to Infomap

### Fixed
- Boolean logic in edge rendering for multilayer networks (Issue #19)
- NetworkX 3.x compatibility issues
- Node2Vec binary validation with better error messages
- Permission checks for external binaries

## [0.95a] - 2025

### Added
- Modern packaging with pyproject.toml
- CI with code quality checks (ruff, black, isort, mypy)
- Multi-Python version testing (3.8-3.11)
- NetworkX 3.x compatibility
- Partial seed support (multilayer_modularity)
- Sparse supra-adjacency matrix support (default)

### Changed
- Minimum Python version set to 3.8
- Build backend switched to setuptools with PEP 517/518 compliance

---

**Note**: For detailed development history and roadmap, see `LLM.md`.
