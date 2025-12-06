# Practical Multilayer Network Analysis with Py3plex

This directory contains the source files for the technical book **"Practical Multilayer Network Analysis with Py3plex"**, a research-oriented handbook for graduate students and applied network scientists.

## Structure

The book is organized into five main parts plus appendices:

### Part I: Foundations of Multilayer Networks and Py3plex
- Chapter 1: Introduction & Motivation
- Chapter 2: Multilayer Network Basics
- Chapter 3: Design of Py3plex

### Part II: Working with Py3plex
- Chapter 4: Installation and Getting Started
- Chapter 5: Data Loading and Representation
- Chapter 6: Visualization and Exploration (outline)
- Chapter 7: Core Algorithms: Communities, Centrality, Dynamics (outline)

### Part III: Advanced Analysis and the Py3plex DSL
- Chapter 8: Introduction to the Py3plex DSL
- Chapter 9: The Builder API and Explain Plans (outline)
- Chapter 10: Advanced Queries and Workflows (outline)
- Chapter 11: Limitations and Stability Guarantees

### Part IV: Case Studies
- Chapter 12: Case Study 1 (outline)
- Chapter 13: Case Study 2 (outline)
- Chapter 14: Case Study 3 (outline/optional)

### Part V: Systems, Reproducibility, and Deployment
- Chapter 15: Testing and Validation (outline)
- Chapter 16: Reproducible Environments
- Chapter 17: The Py3plex GUI (Overview)

### Appendices
- Appendix A: Repository Layout and Scripts
- Appendix B: Docker, Docker Compose, and Deployment
- Appendix C: Detailed Validation Scripts
- Appendix D: Error Handling and Exception Hierarchy
- Appendix E: Extended API and DSL Reference

## Building the Book

### Requirements

```bash
pip install sphinx sphinx_rtd_theme
```

### Build HTML

```bash
cd book
make html
# Output in _build/html/
```

### Build PDF

```bash
cd book
make latexpdf
# Output in _build/latex/py3plex_book.pdf
```

### Build EPUB

```bash
cd book
make epub
# Output in _build/epub/
```

## Status

**Current State (as of PR creation):**

- **Complete Chapters:** 1-5, 8, 11, 16, 17, and all appendices
- **Outline Chapters:** 6-7, 9-10, 12-15 (detailed outlines with source file references)

The complete chapters provide:
- Full narrative text with examples
- Code snippets and usage patterns
- Structured content ready for publication

The outline chapters include:
- Detailed section structure
- Key topics to cover
- References to source files in `docfiles/` to integrate
- TODO markers for expansion

## Design Principles

This book follows these refactoring principles from the original issue:

1. **Research-oriented handbook** — Not just API docs
2. **Clean structure** — 5 Parts + Appendices, no giant blobs
3. **Preserve technical depth** — Math, algorithms, and examples intact
4. **Remove cruft** — No internal dev notes, roadmap chatter, or broken snippets
5. **Professional tone** — Friendly but disciplined
6. **Clear feature status** — Stable, Experimental, Planned
7. **Move heavy details to appendices** — Docker, CI, validation scripts

## Content Mapping

Key source files from `docfiles/` have been restructured:

- **Foundations** — From `concepts/`, `multilayer_networks_101.rst`, `supra.rst`
- **Installation** — From `getting_started/installation.rst`, `quickstart_5min.rst`
- **Data Loading** — From `user_guide/io_and_formats.rst`, `io_serialization.rst`
- **DSL** — From `user_guide/dsl.rst` and `examples/network_analysis/example_dsl_*.py`
- **GUI** — From `gui/*.rst` files
- **Appendices** — From `dev/`, `deployment/`, and scattered implementation details

## Contributing to the Book

If expanding outline chapters:

1. Review the chapter outline and TODO comments
2. Check referenced source files in `docfiles/`
3. Integrate content following the book's tone and structure
4. Ensure code examples are complete and runnable
5. Keep chapters focused (10-15 pages typical length)
6. Move heavy details to appendices when appropriate

## License

- **Book content:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Code examples:** MIT License (same as py3plex)

## Citation

To cite this book:

```bibtex
@book{Skrlj2025book,
  author = {Škrlj, Blaž},
  title = {Practical Multilayer Network Analysis with Py3plex},
  year = {2025},
  version = {1.0},
  url = {https://github.com/SkBlaz/py3plex}
}
```

## Notes

This book refactoring was created to transform the existing py3plex documentation from a collection of library docs into a coherent technical book suitable for graduate students and researchers. The structure preserves all important technical content while improving organization and readability.

Chapters marked as outlines provide detailed structure and can be expanded by integrating content from the referenced source files in `docfiles/`.
