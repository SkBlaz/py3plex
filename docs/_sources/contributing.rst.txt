Contributing to py3plex
=======================

We welcome contributions to py3plex. This guide explains how to contribute effectively.

Ways to Contribute
------------------

You can contribute in many ways:

* Report bugs - Open issues for bugs you encounter
* Suggest features - Propose new features or improvements
* Write documentation - Improve or expand documentation
* Fix bugs - Submit pull requests fixing issues
* Add features - Implement new algorithms or capabilities
* Write tests - Improve test coverage
* Review PRs - Help review pull requests from others

Getting Started
---------------

Fork and Clone
~~~~~~~~~~~~~~

1. Fork the repository on GitHub
2. Clone your fork:

.. code-block:: bash

    git clone https://github.com/YOUR_USERNAME/py3plex.git
    cd py3plex

3. Add upstream remote:

.. code-block:: bash

    git remote add upstream https://github.com/SkBlaz/py3plex.git

Development Setup
~~~~~~~~~~~~~~~~~

Install in development mode with all dependencies:

.. code-block:: bash

    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    
    # Install in editable mode with dev dependencies
    pip install -e ".[dev]"

This installs:

* Core dependencies
* Testing tools (pytest, coverage)
* Linting tools (black, ruff, isort, mypy)
* Documentation tools (sphinx)

Development Workflow
--------------------

Create a Branch
~~~~~~~~~~~~~~~

Always create a new branch for your work:

.. code-block:: bash

    git checkout -b feature/my-new-feature
    # or
    git checkout -b fix/issue-123

Make Changes
~~~~~~~~~~~~

1. Write your code following our coding standards (see below)
2. Add or update tests
3. Update documentation
4. Run linters and tests

Run Tests
~~~~~~~~~

.. code-block:: bash

    # Run all tests
    make test
    
    # Or directly with pytest
    python run_tests.py

Run Linters
~~~~~~~~~~~

.. code-block:: bash

    # Run all linters
    make lint
    
    # Or individual tools
    make format  # Auto-format code (black, isort)
    ruff check .
    mypy py3plex

Commit Changes
~~~~~~~~~~~~~~

Write clear, descriptive commit messages:

.. code-block:: bash

    git add .
    git commit -m "Add feature X to support Y
    
    - Implement algorithm for Z
    - Add tests for edge cases
    - Update documentation"

Push and Create PR
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    git push origin feature/my-new-feature

Then create a Pull Request on GitHub with:

* Clear title describing the change
* Description of what changed and why
* Reference to related issues (e.g., "Fixes #123")
* Screenshots for UI changes

Coding Standards
----------------

Code Style
~~~~~~~~~~

We follow PEP 8 with these specifics:

* Line length: 100 characters (not 80)
* Indentation: 4 spaces (no tabs)
* String quotes: Single quotes preferred ('text' not "text")
* Imports: Grouped and sorted (using isort)

Auto-format your code:

.. code-block:: bash

    make format

This runs:

* ``isort`` - Sort and organize imports
* ``black`` - Format code consistently
* ``ruff --fix`` - Auto-fix linting issues

Naming Conventions
~~~~~~~~~~~~~~~~~~

* Functions/variables: ``snake_case``
* Classes: ``PascalCase``
* Constants: ``UPPER_SNAKE_CASE``
* Private members: ``_leading_underscore``

.. code-block:: python

    # Good
    def compute_centrality(network, node_id):
        MAX_ITERATIONS = 100
        centrality_scores = {}
        return centrality_scores
    
    class MultilayerNetwork:
        def __init__(self):
            self._internal_state = {}

Docstrings
~~~~~~~~~~

Use NumPy-style docstrings for all public functions and classes:

.. code-block:: python

    def multilayer_degree_centrality(network, layer=None, weighted=False):
        """
        Compute degree centrality for multilayer network.
        
        Parameters
        ----------
        network : multi_layer_network
            The multilayer network to analyze.
        layer : str, optional
            Specific layer to analyze. If None, aggregates across all layers.
        weighted : bool, default=False
            If True, compute strength (weighted degree) instead of degree.
        
        Returns
        -------
        dict
            Dictionary mapping node names to centrality scores.
        
        Examples
        --------
        >>> network = multinet.multi_layer_network()
        >>> network.add_edges([['A', 'L1', 'B', 'L1', 1]])
        >>> centrality = multilayer_degree_centrality(network)
        >>> centrality['A---L1']
        1.0
        
        See Also
        --------
        multilayer_betweenness_centrality : Betweenness centrality
        
        Notes
        -----
        For directed networks, this computes out-degree by default.
        
        References
        ----------
        .. [1] De Domenico, M., et al. (2013). Mathematical formulation of 
               multilayer networks. Physical Review X, 3(4), 041022.
        """
        pass

Type Hints
~~~~~~~~~~

Add type hints to improve code clarity:

.. code-block:: python

    from typing import Dict, List, Optional
    from py3plex.core.multinet import multi_layer_network
    
    def compute_statistics(
        network: multi_layer_network,
        layers: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Compute network statistics."""
        pass

Testing Guidelines
------------------

Test Requirements
~~~~~~~~~~~~~~~~~

All new code should include tests:

* Unit tests for individual functions
* Integration tests for workflows
* Edge cases for boundary conditions
* Documentation tests for examples in docstrings

Writing Tests
~~~~~~~~~~~~~

Use pytest for testing:

.. code-block:: python

    # tests/test_my_feature.py
    import pytest
    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    def test_layer_density():
        """Test layer density calculation."""
        # Setup
        network = multinet.multi_layer_network()
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
        ], input_type='list')
        
        # Execute
        density = mls.layer_density(network, 'L1')
        
        # Assert
        assert 0 <= density <= 1
        assert density == pytest.approx(0.333, abs=0.01)
    
    def test_invalid_layer():
        """Test error handling for invalid layer."""
        network = multinet.multi_layer_network()
        
        with pytest.raises(ValueError):
            mls.layer_density(network, 'nonexistent')

Test Coverage
~~~~~~~~~~~~~

Aim for high test coverage:

.. code-block:: bash

    # Run tests with coverage
    pytest --cov=py3plex --cov-report=html
    
    # View coverage report
    open htmlcov/index.html  # macOS
    # or
    xdg-open htmlcov/index.html  # Linux

Target: >80% coverage for new code

Documentation
-------------

Update Documentation
~~~~~~~~~~~~~~~~~~~~

When adding features, update:

1. **Docstrings** in the code
2. **RST files** in ``docfiles/`` if adding major features
3. **Examples** in ``examples/`` directory
4. **README.md** if changing installation or basic usage

Build Documentation
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    cd docfiles
    make html
    
    # View documentation
    open _build/html/index.html

Documentation Style
~~~~~~~~~~~~~~~~~~~

* Clear and concise - Use simple language
* Code examples - Include working examples
* Cross-references - Link to related documentation
* Visual aids - Add diagrams where helpful

Pull Request Guidelines
------------------------

Before Submitting
~~~~~~~~~~~~~~~~~

[OK] Code follows style guide (``make lint`` passes)

[OK] All tests pass (``make test`` passes)

[OK] New code has tests

[OK] Documentation is updated

[OK] Commit messages are clear

[OK] Branch is up to date with main

PR Description
~~~~~~~~~~~~~~

Include in your PR description:

* What changed
* Why the change is needed
* How you implemented it
* Testing done
* Screenshots for visual changes
* Breaking changes if any

Example PR template:

.. code-block:: markdown

    ## Description
    
    Implements multilayer PageRank centrality following [citation].
    
    ## Motivation
    
    Closes #123 - needed for analyzing directed multilayer networks.
    
    ## Changes
    
    - Add `multilayer_pagerank()` function
    - Add tests with 90% coverage
    - Add example in `example_centrality.py`
    - Update documentation in `centrality.rst`
    
    ## Testing
    
    - [x] Unit tests pass
    - [x] Integration test on real network
    - [x] Tested on Python 3.8, 3.10, 3.12
    - [x] Linting passes
    
    ## Breaking Changes
    
    None.

Review Process
~~~~~~~~~~~~~~

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged
4. Your contribution will be in the next release!

Reporting Issues
----------------

Bug Reports
~~~~~~~~~~~

When reporting bugs, include:

* Description of the bug
* Steps to reproduce
* Expected behavior
* Actual behavior
* Python version (``python --version``)
* py3plex version
* Operating system
* Minimal code example

Example:

.. code-block:: markdown

    ## Bug Description
    
    `layer_density()` returns negative values for certain graphs.
    
    ## Steps to Reproduce
    
    ```python
    network = multinet.multi_layer_network()
    network.add_edges([['A', 'L1', 'B', 'L1', -1]])
    density = mls.layer_density(network, 'L1')
    print(density)  # -0.5
    ```
    
    ## Expected
    
    Density should be between 0 and 1, or raise ValueError for negative weights.
    
    ## Actual
    
    Returns -0.5
    
    ## Environment
    
    - Python 3.10.5
    - py3plex 0.95a
    - Ubuntu 22.04

Feature Requests
~~~~~~~~~~~~~~~~

For feature requests, describe:

* Use case - What problem does it solve?
* Proposed solution - How should it work?
* Alternatives - Other approaches considered
* Additional context - Examples, papers, etc.

Code of Conduct
---------------

* Be respectful and inclusive
* Welcome newcomers
* Focus on what is best for the community
* Show empathy towards other community members

See our full `Code of Conduct <https://github.com/SkBlaz/py3plex/blob/master/CODE_OF_CONDUCT.md>`_.

License
-------

By contributing, you agree that your contributions will be licensed under the MIT License.

Recognition
-----------

Contributors are recognized in:

* ``CONTRIBUTORS.md`` file
* Release notes
* ``AUTHORS`` section in the documentation

Getting Help
------------

* Questions: Open a GitHub Discussion
* Chat: Join our community chat (link in README)
* Email: Contact maintainers at blaz.skrlj@ijs.si

Next Steps
----------

* Read :doc:`development` for development workflow details
* See :doc:`architecture` for system architecture
* Browse `existing issues <https://github.com/SkBlaz/py3plex/issues>`_
* Check `good first issues <https://github.com/SkBlaz/py3plex/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22>`_

Thank you for contributing to py3plex!
