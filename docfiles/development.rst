Development Guide
==================

This guide covers **development workflows**, **Makefile commands**, **testing**, and **contributing** to py3plex.

**View the full development guide**: `development.md <https://github.com/SkBlaz/py3plex/blob/master/docs/development.md>`_

Getting Started
---------------

**Clone the repository** and install in **development mode**:

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    
    # Setup development environment
    make setup
    
    # Install package in editable mode with dev dependencies
    make dev-install

Makefile Commands
-----------------

The project includes a **production-grade Makefile** for streamlined development:

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
    make ci             # Run full CI checks

Key Features:

- **Smart tool detection**: Uses ``.venv/bin/`` tools if available, otherwise falls back to **global tools**
- **Colorized output**: Clear **success/warning/error** messages
- **Cross-platform**: Works on **Linux** and **macOS**

Testing
-------

**Quick testing:**

.. code-block:: bash

    python run_tests.py

**Development testing** with pytest:

.. code-block:: bash

    # Run all tests
    pytest
    
    # Run with coverage
    pytest --cov=py3plex --cov-report=html
    
    # Run specific test file
    pytest tests/test_core.py
    
    # Using Makefile (recommended)
    make test

Code Quality
------------

Tools configured in ``pyproject.toml``:

- **Black**: Code formatting
- **Ruff**: Fast linting
- **isort**: Import sorting
- **Mypy**: Type checking
- **Pytest**: Testing with coverage

Before committing:

.. code-block:: bash

    make format  # Auto-format code
    make lint    # Check code quality
    make test    # Run tests
    make ci      # Run all checks

Contributing
------------

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting: ``make ci``
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

    # Using Makefile (recommended)
    make docs
    
    # Manual build
    cd docfiles
    sphinx-build -b html . _build/html

The built documentation will be in ``docfiles/_build/html/``.

Resources
---------

- **Repository**: https://github.com/SkBlaz/py3plex
- **Documentation**: https://skblaz.github.io/py3plex/
- **Issues**: https://github.com/SkBlaz/py3plex/issues
- **Examples**: https://github.com/SkBlaz/Py3Plex/tree/master/examples

For comprehensive project context, see `LLM.md <https://github.com/SkBlaz/py3plex/blob/master/LLM.md>`_.

