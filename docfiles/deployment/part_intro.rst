Environments & Deployment
=========================

Use this section to run py3plex from the command line, inside Docker containers, and at scale—while keeping runs reproducible.

**This section covers:**

* :doc:`cli_and_docker` — Command-line interface and containerized deployment
* :doc:`performance_scalability` — Memory management, optimization, large networks

When to Use This Section
------------------------

Use these chapters when you want to:

* Automate analyses that you currently run interactively
* Process networks too large for a single Python session
* Share reproducible environments with collaborators or CI
* Integrate py3plex into a production data pipeline

**CLI** gives you a scriptable interface for common operations—no Python coding required and suitable for headless automation. Start here if you already know the operations you want to run.

**Docker** keeps environments identical across machines, avoiding "works on my machine" issues. Use it when you need the same environment on laptops, CI, and servers.

The **performance** chapter covers memory management and optimization for large networks once you have a working workflow. It is most useful after you have a repeatable pipeline and want to speed it up or shrink memory use.

Most readers start with :doc:`cli_and_docker` to script or containerize workflows, then move to :doc:`performance_scalability` to tune runtime and memory as datasets grow.

.. tip::

   **Deployment checklist:**
   
   * Pin dependency versions (requirements.txt or lock file) and set a random seed for reproducibility
   * Handle missing files, empty inputs, and unexpected formats explicitly
   * Validate results on a small test network before scaling up
   * Enable logging for reproducibility and debugging; keep logs with your outputs
   * Run a dry run on the target environment (local, Docker, or cluster) before scheduling large jobs
