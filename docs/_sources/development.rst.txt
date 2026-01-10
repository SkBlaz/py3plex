Development Guide
==================

This guide covers **development workflows**, **Makefile commands**, **testing**, and **contributing** to py3plex. Keep it handy as your single reference while coding, testing, and writing docs.

Getting Started
---------------

Clone the repository and install in development mode. Requirements: Python 3.8+, ``pip`` or ``uv``; ``make`` is recommended for the shortcuts below. Keep your virtual environment active so the same interpreter is used for every command.

**Using uv (recommended):**

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    
    # Install uv if not already installed
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Create virtual environment
    uv venv .venv
    source .venv/bin/activate
    
    # Install package in editable mode with dev dependencies
    uv pip install -e ".[dev]"

**Using Makefile (auto-detects uv):**

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    
    # Setup development environment (creates .venv, uses uv if available)
    make setup
    
    # Install package in editable mode with dev dependencies
    make dev-install

If you prefer manual setup, create and activate ``.venv`` yourself, then run ``pip install -e .[dev]`` from the repository root. Whichever path you choose, activate the environment before running any ``make`` target so the same interpreter is used consistently.

Makefile Commands
-----------------

The Makefile provides a streamlined development workflow. Run targets from the repository root with your virtual environment active:

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
- Automatically uses ``uv`` if available for faster installs, otherwise falls back to ``pip``
- Colorized output with clear **success/warning/error** messages
- Works on **Linux** and **macOS**
- ``make ci`` is the superset; use it before pushing. Use ``make format`` / ``make lint`` / ``make test`` for quicker local loops during development.

Testing
-------

Start with the Makefile target, then drill down with pytest as needed. Favor deterministic seeds for generators so results are reproducible. Use narrow targets while iterating, then run the full suite.

.. code-block:: bash

    # Recommended: run all tests with coverage
    make test

    # Equivalent pytest invocations
    python -m pytest tests/ -v
    python -m pytest tests/ --cov=py3plex --cov-report=html

    # Run a specific test module or node
    python -m pytest tests/test_core.py -k "degree"
    python -m pytest tests/test_core.py::test_degree  # single test

The coverage HTML report is written to ``htmlcov/index.html``.

Code Quality
------------

Tools configured in ``pyproject.toml``:

- **Black**: Code formatting
- **Ruff**: Fast linting
- **isort**: Import sorting
- **Mypy**: Type checking
- **Pytest**: Testing with coverage

Before committing, run the quality loop from an active virtual environment. Reinstall dev dependencies if a tool is missing.

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
4. Run ``make format``, ``make lint``, ``make test`` (or ``make ci``) from your active environment
5. Commit with clear messages that explain what changed and why
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

Resources
---------

- **Repository**: https://github.com/SkBlaz/py3plex
- **Documentation**: https://skblaz.github.io/py3plex/
- **Issues**: https://github.com/SkBlaz/py3plex/issues
- **Examples**: https://github.com/SkBlaz/Py3Plex/tree/master/examples
