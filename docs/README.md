# Py3plex Documentation

This directory contains comprehensive documentation for py3plex. Choose the guide that best fits your needs.

## Quick Start

- **[10-Minute Tutorial](10min_tutorial.md)** - Get started with py3plex quickly
- **[README](../README.md)** - Main project README with installation and basic usage

## User Guides

### Algorithms and Analysis
- **[Algorithm Selection Guide](algorithm_selection_guide.md)** - Choose the right algorithm for your task
- **[Algorithm Citations](ALGORITHM_CITATIONS.md)** - Academic references for implemented algorithms with DOIs
- **[Multilayer Centrality Tutorial](multilayer_centrality_tutorial.md)** - Centrality measures for multilayer networks
- **[Multilayer Modularity Tutorial](multilayer_modularity_tutorial.md)** - Computing modularity in multilayer networks
- **[Multilayer Formulas Quick Reference](MULTILAYER_FORMULAS_QUICK_REFERENCE.md)** - Mathematical formulas and metrics

### Visualization
- **[Layout Coordinates](LAYOUT_COORDINATES.md)** - Understanding coordinate systems and conventions

## Developer Resources

### Contributing
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to py3plex
- **[Architecture](ARCHITECTURE.md)** - System architecture and design patterns
- **[Development Guide](development.md)** - Development workflow and best practices
- **[Quick Reference](QUICK_REFERENCE.md)** - Cheat sheet for common operations

### Documentation Tools
- **[check_doc_coverage.py](check_doc_coverage.py)** - Measure RST documentation coverage
  - Run: `python docs/check_doc_coverage.py` to see coverage report
  - Options: `--verbose` (show undocumented items), `--json` (save JSON report), `--badge-only` (badge URL only)
  - CI: Automated checks run on every push/PR via `.github/workflows/doc-coverage.yml`
- **[check_api_consistency.py](check_api_consistency.py)** - Check API documentation quality
  - Run: `python docs/check_api_consistency.py` to find missing docstrings

### Additional Resources
- **[Open Issues Analysis](OPEN_ISSUES_ANALYSIS_2025-10-14.md)** - Status of open issues and roadmap items

### API Reference
- **Sphinx Documentation**: Build locally with `cd docfiles && make html`
- **API details**: See the [examples/](../examples/) directory for usage patterns

## Additional Resources

### Examples
See the [examples/](../examples/) directory for:
- Basic usage examples
- Algorithm demonstrations  
- Visualization samples
- Integration examples

### Benchmarks
See the [benchmarks/](../benchmarks/) directory for:
- Performance benchmarks
- Configuration examples
- Comparison scripts

### Tests
See the [tests/](../tests/) directory for:
- Unit test examples
- Integration test patterns
- Test coverage reports

## Documentation Structure

```
docs/
├── README.md                            ← You are here
├── 10min_tutorial.md                    ← Quick start guide
├── ALGORITHM_CITATIONS.md               ← Academic references with DOIs
├── ARCHITECTURE.md                      ← System design
├── CONTRIBUTING.md                      ← Contribution guidelines
├── LAYOUT_COORDINATES.md                ← Visualization coordinates
├── QUICK_REFERENCE.md                   ← Quick reference guide
├── MULTILAYER_FORMULAS_QUICK_REFERENCE.md ← Mathematical formulas
├── algorithm_selection_guide.md         ← Algorithm guide
├── development.md                       ← Development workflow
├── multilayer_centrality_tutorial.md    ← Centrality tutorial
├── multilayer_modularity_tutorial.md    ← Modularity tutorial
└── OPEN_ISSUES_ANALYSIS_2025-10-14.md   ← Status and roadmap
```

## Getting Help

### Documentation Issues
If you find errors or gaps in the documentation:
1. Check if there's already an [issue](https://github.com/SkBlaz/py3plex/issues)
2. Create a new issue with the `documentation` label
3. Consider submitting a PR with corrections

### Usage Questions
For questions about using py3plex:
- Check the [examples/](../examples/) directory
- Search [closed issues](https://github.com/SkBlaz/py3plex/issues?q=is%3Aissue+is%3Aclosed)
- Open a [discussion](https://github.com/SkBlaz/py3plex/discussions)
- Create an issue with the `question` label

### Feature Requests
To suggest new features or improvements:
- Check the [roadmap](../LLM.md) for planned features
- Open an issue with the `enhancement` label
- Describe the use case and expected behavior

## Contributing to Documentation

We welcome documentation contributions! To contribute:

1. Follow the [Contributing Guide](CONTRIBUTING.md)
2. Use Markdown format
3. Include code examples that run
4. Add links to related documentation
5. Update this README if adding new docs

### Documentation Style

- **Clear and concise**: Use simple language
- **Code examples**: Include working examples
- **Visual aids**: Add diagrams where helpful
- **Cross-references**: Link to related docs
- **Up-to-date**: Keep synchronized with code

### Building Sphinx Documentation

```bash
# Install documentation dependencies
pip install -e ".[dev]"

# Build HTML documentation
cd docfiles
make html

# View documentation
open _build/html/index.html  # macOS
# or
xdg-open _build/html/index.html  # Linux
```

## Version Information

This documentation is for py3plex version **0.95a**.

For documentation of other versions, see the [releases page](https://github.com/SkBlaz/py3plex/releases).

## License

Documentation is licensed under the same terms as py3plex (MIT License).

---

**Need more help?** Open an issue on [GitHub](https://github.com/SkBlaz/py3plex/issues) or check the [discussions](https://github.com/SkBlaz/py3plex/discussions).
