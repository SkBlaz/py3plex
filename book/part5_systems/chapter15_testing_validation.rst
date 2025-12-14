.. _testing-chapter:

Testing and Validation
===================================

py3plex uses a comprehensive testing strategy to ensure correctness across algorithms, data structures, and the DSL. This chapter provides a high-level overview of testing philosophy and organization. **For detailed validation scripts and test code, see Appendix C.**

Testing Philosophy
------------------

py3plex testing follows four principles:

1. **Correctness first:** Algorithms must produce mathematically correct results
2. **Conservation laws:** Physical constraints (e.g., probability conservation) must hold
3. **Regression prevention:** Known-good outputs are compared against current runs
4. **Property testing:** Invariants should hold for random inputs

Test Categories
~~~~~~~~~~~~~~~

* **Unit tests** — Individual functions and methods in isolation
* **Integration tests** — Module interactions and end-to-end workflows
* **Property-based tests** — Hypothesis-driven testing with random inputs
* **Regression tests** — Compare against reference runs for dynamics models

Test Organization
-----------------

The test suite is organized by module and functionality:

.. code-block:: text

    tests/
    ├── test_core.py                  # Core data structures
    ├── test_dsl*.py                  # DSL functionality (10+ files)
    ├── test_dynamics*.py             # Dynamics models
    ├── test_algorithms*.py           # Algorithm correctness
    ├── test_centrality*.py           # Centrality measures
    ├── test_community*.py            # Community detection
    ├── test_io*.py                   # I/O and serialization
    ├── test_uncertainty*.py          # Uncertainty quantification
    └── property/                     # Property-based tests (planned)

**Current coverage:** ~85% code coverage across core modules.

Key Validation Strategies
--------------------------

Random Walk Conservation
~~~~~~~~~~~~~~~~~~~~~~~~

Random walks must conserve probability—transition probabilities from any state must sum to 1:

.. code-block:: python

    def test_random_walk_conservation():
        """Verify random walk conserves probability."""
        # Implementation in tests/test_random_walk_conservation.py
        # Computes transition matrix and checks row sums ≈ 1.0

**Tests:** ``tests/test_paths.py`` includes walk conservation checks.

Node2Vec Validation
~~~~~~~~~~~~~~~~~~~

Validate that Node2Vec biases (parameters p and q) have the intended effects:

* Higher p → reduced probability of returning to previous node
* Higher q → preference for local exploration vs. distant jumps

**Tests:** ``tests/test_node2vec.py`` validates bias behavior.

Community Detection Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify that community detection algorithms satisfy basic properties:

* **Modularity bounds:** Q ∈ [-0.5, 1.0]
* **Partition completeness:** Every node assigned to exactly one community
* **Singleton handling:** Isolated nodes form their own communities

**Tests:** ``tests/test_community*.py`` files validate Louvain, Infomap, and other algorithms.

Dynamics Validation
~~~~~~~~~~~~~~~~~~~

Epidemic models must satisfy conservation laws:

* **SIS:** S(t) + I(t) = N for all t
* **SIR:** S(t) + I(t) + R(t) = N for all t
* **Steady state:** SIS reaches equilibrium for subcritical parameters

**Tests:** ``tests/test_dynamics.py`` validates SIR, SIS, and other models with reference runs.

Running Tests
-------------

Basic Test Execution
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Run all tests
    pytest tests/
    
    # Run specific test file
    pytest tests/test_dsl.py
    
    # Run tests matching a pattern
    pytest tests/ -k "test_community"
    
    # Run with coverage
    pytest tests/ --cov=py3plex --cov-report=html
    
    # Verbose output
    pytest tests/ -v

Using Makefile
~~~~~~~~~~~~~~

.. code-block:: bash

    make test           # Run all tests
    make test-coverage  # Generate HTML coverage report
    make test-fast      # Run only fast tests (skip slow integration tests)

**Test markers:**

* ``@pytest.mark.slow`` — Tests that take >5 seconds
* ``@pytest.mark.integration`` — End-to-end integration tests
* ``@pytest.mark.hypothesis`` — Property-based tests

Continuous Integration
----------------------

py3plex uses GitHub Actions for automated testing on every commit and pull request.

GitHub Actions
~~~~~~~~~~~~~~

The CI pipeline tests across:

* **Python versions:** 3.8, 3.9, 3.10, 3.11, 3.12
* **Operating systems:** Ubuntu Linux, macOS, Windows
* **Test suites:** Core, DSL, algorithms, dynamics, I/O

**Build status:** Tests must pass on all platforms before merging.

**Coverage requirements:** New code should maintain or improve coverage (target: 85%+).

.. admonition:: CI Configuration
   :class: note

   The GitHub Actions workflow files are located in ``.github/workflows/`` in the repository. Key workflows include ``test.yml`` (main test suite), ``lint.yml`` (code quality checks), and ``docs.yml`` (documentation builds).

Summary
-------

py3plex testing ensures correctness through:

1. **Comprehensive test suite** — 200+ tests across core functionality
2. **Multiple validation strategies** — Conservation laws, property tests, reference runs
3. **Continuous integration** — Automated testing on all platforms
4. **High coverage** — 85%+ code coverage

Testing is an ongoing priority. Contributions that add tests for uncovered code or validate edge cases are especially welcome.

**For detailed test scripts and validation examples, see Appendix C.**

**Next chapter:** Reproducible environments and deployment practices
