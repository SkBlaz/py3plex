Development Guide
==================

This guide covers **development workflows**, **Makefile commands**, **testing**, and **contributing** to py3plex. Use it as your single reference while coding, testing, and writing docs.

Getting Started
---------------

**Clone the repository** and install in **development mode**. Requirements: Python 3.8+ and ``pip``; ``make`` is recommended for the shortcuts below. Keep your virtual environment active so ``make`` uses the same interpreter every time.

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    
    # Setup development environment
    make setup
    
    # Install package in editable mode with dev dependencies
    make dev-install

If you prefer manual setup, create and activate ``.venv`` yourself, then run ``pip install -e .[dev]`` from the repository root.

Makefile Commands
-----------------

The Makefile provides a streamlined development workflow (run targets from the repository root with your virtual environment active):

.. code-block:: bash

    # View all available commands
    make help
    
    # Environment setup
    make setup          # Create virtual environment
    make dev-install    # Install in editable mode
    
    # Code quality
    make format         # Auto-format code
    make lint           # Run linters
    
    # Testing
    make test           # Run tests with coverage
    make coverage       # Open coverage report
    
    # Documentation
    make docs           # Build Sphinx documentation
    
    # Build & publish
    make clean          # Remove build artifacts
    make build          # Build distributions
    make publish        # Publish to PyPI
    
    # CI
    make ci             # Run full CI checks (format + lint + tests)

Makefile highlights:

- Uses ``.venv/bin/`` tools when available, otherwise falls back to global tools
- Colorized output with clear **success/warning/error** messages
- Works on **Linux** and **macOS**
- ``make ci`` is the superset; use it before pushing, and use ``make format`` / ``make lint`` / ``make test`` for quicker local loops

Testing
-------

Start with the Makefile target, then drill down with pytest as needed. Favor deterministic seeds for generators so results are reproducible.

.. code-block:: bash

    # Recommended: run all tests with coverage
    make test
    
    # Equivalent pytest invocations
    python -m pytest tests/ -v
    python -m pytest tests/ --cov=py3plex --cov-report=html
    
    # Run a specific test module or node
    python -m pytest tests/test_core.py -k "degree"

The coverage HTML report is written to ``htmlcov/index.html``.

Code Quality
------------

Tools configured in ``pyproject.toml``:

- **Black**: Code formatting
- **Ruff**: Fast linting
- **isort**: Import sorting
- **Mypy**: Type checking
- **Pytest**: Testing with coverage

Before committing, run the quality loop from an active virtual environment:

.. code-block:: bash

    make format  # Auto-format code
    make lint    # Check code quality
    make test    # Run tests
    make ci      # Run all checks (use before pushing)

Contributing
------------

We welcome contributions! Recommended workflow:

1. Sync your local ``main`` with ``upstream/main``
2. Create a feature branch
3. Make focused changes with tests and docs
4. Run ``make format``, ``make lint``, ``make test`` (or ``make ci``)
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

**Code Guidelines**:

- Follow existing code style (enforced by Black and Ruff)
- Add tests for new features
- Update documentation as needed
- Keep changes focused and atomic
- Write clear commit messages

Documentation
-------------

Build Sphinx documentation:

.. code-block:: bash

    # Using Makefile (recommended from repository root)
    make docs
    
    # Manual build from docfiles/
    cd docfiles
    sphinx-build -b html . _build/html

If the build fails because Sphinx is missing, (re)install the development extras in your active virtual environment, then rerun the command.

Open ``docfiles/_build/html/index.html`` in your browser to view the output.

Documentation Style Guide
~~~~~~~~~~~~~~~~~~~~~~~~~

When contributing to documentation, follow these conventions for consistency:

**Naming Conventions:**

* Use "Quickstart" (one word) instead of "Quick Start" or "Quickstart Guide"
* Use "multilayer" (no hyphen) consistently, not "multi-layer" or "multi layer"
* Use short, direct section titles without boilerplate

**Tone and Structure:**

* Write first paragraphs that directly explain why the reader is on this page
* Avoid boilerplate like "This chapter will introduce..." or "In this section, you will learn..."
* Start with concrete examples rather than abstract explanations
* Provide 2-3 explicit reading paths for different audiences (new users, experienced users, advanced users)

**Code Examples:**

All code examples must include:

1. **Imports** — Always show required imports
2. **Network creation** — Build a tiny example network from scratch or via helper
3. **Core operation** — Run one focused operation
4. **Expected output** — Show what the user should see

**Example structure:**

.. code-block:: python

    # 1. Imports
    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls

    # 2. Create network
    network = multinet.multi_layer_network(directed=False)
    network.add_nodes([{'source': 'A', 'type': 'layer1'}])
    network.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}
    ])

    # 3. Run operation
    density = mls.layer_density(network, 'layer1')
    print(f"Density: {density:.3f}")

**Expected output:**

.. code-block:: text

    Density: 1.000

**Marking Experimental APIs:**

Use warning directives for experimental or unstable features:

.. code-block:: rst

    .. warning::

       **Experimental Feature:** This API is under active development and may change in future versions.

**Cross-references:**

* Link to related sections using ``:doc:`` for documentation pages
* Link to algorithm details using ``:ref:`` for labeled sections
* When documenting algorithms, link to the Algorithm Roadmap as the conceptual entry point

**Output accuracy:**

* Use real outputs from the current version of py3plex (no placeholders)
* Include the smallest network or dataset needed to reproduce the output

**Version Labels:**

* Use consistent version strings throughout (e.g., "py3plex 1.0.0 documentation")
* Update version in ``conf.py`` and ``pyproject.toml`` together

Resources
---------

- **Repository**: https://github.com/SkBlaz/py3plex
- **Documentation**: https://skblaz.github.io/py3plex/
- **Issues**: https://github.com/SkBlaz/py3plex/issues
- **Examples**: https://github.com/SkBlaz/Py3Plex/tree/master/examples
