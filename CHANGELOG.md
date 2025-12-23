# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2024-12-23

### Removed
- Removed redundant temporary documentation tracking files:
  - `DOCUMENTATION_FIXES.md` - temporary tracking document for completed documentation work
  - `book/PDF_FIXES_SUMMARY.md` - temporary tracking document for completed PDF fixes

### Changed
- Version bumped from 1.0.2 to 1.0.3

## [Unreleased]

### Book/Documentation Improvements

#### Fixed
- **Book Structure**: Fixed PDF table of contents to properly display all 17 chapters as top-level entries instead of collapsing content under "Front Matter"
  - Added `latex_toplevel_sectioning = 'chapter'` to Sphinx configuration
  - Restructured index.rst to use toctree for front matter instead of inline include
  - Each chapter now renders as `\chapter{}` in LaTeX output

- **Placeholders Removed**: Replaced all placeholder content with real documentation
  - chapter07_core_algorithms.rst (5 placeholders + integration note)
    - Added complete overview of three algorithm families
    - Added mathematical definition and complexity table for multilayer modularity
    - Added algorithm selection guidelines with performance characteristics
    - Added comprehensive summary section
  - chapter11_limitations_stability.rst (2 placeholders)
    - Added complete query complexity table with 8 operations
    - Added memory usage guidelines for small/medium/large networks
  - Case study chapters (3 "Work in Progress" notices)
    - Reframed as "Case Study Template" with production-ready workflows

- **Cross-References**: Fixed broken forward references to use Sphinx-native links
  - Added anchors: `installation-chapter`, `data-loading-chapter`, `dsl-chapter`
  - Replaced "See Chapter X" text with `:ref:` links in 3 locations
  - All cross-references now resolve correctly in HTML and PDF builds

#### Improved
- **Security Guidance**: Replaced unsafe `chmod -R 777` advice with three secure alternatives
  - Method 1: Run container with host user ID (recommended)
  - Method 2: Match container user to host ownership
  - Method 3: Use docker-compose with user mapping
  - Added explicit warning against world-writable permissions

- **Reproducibility Documentation**: Enhanced dependency pinning guidance
  - Documented two-file approach (requirements.in + requirements.txt)
  - Clarified exact pins vs version ranges with trade-offs
  - Added pip-compile workflow for managing transitive dependencies
  - Explained when to use each approach (research vs development)

- **Version Information**: Moved from prominent section header to compact note format in front matter

#### Changed
- Book now builds with only 4 warnings (unreferenced bibliography citations)
- HTML and PDF builds verified working
- All placeholder brackets `[...]` removed from reader-facing content
- No broken Sphinx references remaining

