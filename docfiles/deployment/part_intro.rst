Environments & Deployment
=========================

This section covers running py3plex from the command line, in Docker containers, and at scale.

**This section covers:**

* :doc:`cli_and_docker` — Command-line interface and containerized deployment
* :doc:`performance_scalability` — Memory management, optimization, large networks

When to Use This Section
------------------------

Read this section when you need to:

* Automate analyses that currently run interactively
* Process networks too large for a single Python session
* Share reproducible environments with collaborators
* Integrate py3plex into a production pipeline

**CLI** provides a scriptable interface for common operations—no Python required.

**Docker** ensures identical results everywhere, eliminating environment issues.

**Performance** chapter covers memory management and optimization for large networks.

Start with :doc:`cli_and_docker` for automation, then :doc:`performance_scalability` for optimization.

.. tip::

   **Deployment checklist:**
   
   * Version-pin all dependencies
   * Add error handling for edge cases
   * Verify results on test data
   * Set up logging for debugging
   * Test on the target environment
