# Changelog

All notable changes to py3plex will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CHANGELOG.md to track changes systematically
- Python 3.12 support in CI test matrix
- Optional dependency groups in pyproject.toml: `[infomap]`, `[algos]`, `[viz]`
- Type hints coverage increased to 65.4% (70 of 107 maintainable modules)
- Custom exception types module (`py3plex/exceptions.py`) with 13 domain-specific exceptions
- Pre-commit hooks configuration
- Logging infrastructure across core modules

### Changed
- Modern build system with pyproject.toml (PEP 517/518/621 compliance)
- Comprehensive Makefile-based development workflow
- Updated all dependencies to modern versions compatible with Python 3.8+
  - numpy 1.19+, scipy 1.5+, matplotlib 3.3+, gensim 4.0+, scikit-learn 0.24+
- Converted 170 of 229 print statements to logging (74% completion)
- Fixed all 50 bare except clauses with specific exception types
- Removed 8 wildcard imports (from 9 to 1)

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
