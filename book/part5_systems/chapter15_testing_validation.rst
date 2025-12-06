Chapter 15: Testing and Validation
===================================

*TODO: Consolidate from docfiles/dev/ and tests/ structure*

Testing Philosophy
------------------

[High-level overview of py3plex's testing approach]

Test Categories
~~~~~~~~~~~~~~~

* **Unit tests** — Individual functions and methods
* **Integration tests** — Module interactions
* **Property-based tests** — Hypothesis-driven testing
* **Regression tests** — Reference runs for dynamics

Test Organization
-----------------

[Structure of tests/ directory]

.. code-block:: text

    tests/
    ├── test_core.py           # Core data structures
    ├── test_dsl*.py           # DSL functionality
    ├── test_dynamics*.py      # Dynamics models
    ├── test_algorithms*.py    # Algorithm correctness
    └── property/              # Property-based tests

Key Validation Strategies
--------------------------

Random Walk Conservation
~~~~~~~~~~~~~~~~~~~~~~~~

[Test that random walks conserve probability]

.. code-block:: python

    # Example validation pattern
    def test_random_walk_conservation():
        """Ensure random walk probabilities sum to 1."""
        # Test code here

Node2Vec Validation
~~~~~~~~~~~~~~~~~~~

[Bias checks, parameter sensitivity]

Community Detection Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[Modularity bounds, partition quality]

Dynamics Validation
~~~~~~~~~~~~~~~~~~~

[Conservation laws, steady-state properties]

Running Tests
-------------

Basic Test Execution
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Run all tests
    pytest tests/
    
    # Run specific test file
    pytest tests/test_dsl.py
    
    # Run with coverage
    pytest tests/ --cov=py3plex

Using Makefile
~~~~~~~~~~~~~~

.. code-block:: bash

    make test           # Run all tests
    make test-coverage  # Generate coverage report

Continuous Integration
----------------------

[Brief overview—detailed CI configs in Appendix]

GitHub Actions
~~~~~~~~~~~~~~

[Test matrix: Python versions, OS platforms]

Summary
-------

[Testing ensures correctness—but keep details in Appendix C]

*Source files:*
- tests/ directory structure
- docfiles/dev/development_guide.rst
- Detailed test scripts → Appendix C
