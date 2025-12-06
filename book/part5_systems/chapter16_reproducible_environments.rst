Reproducible Environments
======================================

*TODO: Consolidate environment setup practices—defer details to Appendix*

Reproducibility Principles
---------------------------

[Why reproducibility matters in network science]

Environment Management
----------------------

Python Virtual Environments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # venv
    python3 -m venv py3plex-env
    source py3plex-env/bin/activate
    pip install py3plex
    
    # conda
    conda create -n py3plex python=3.10
    conda activate py3plex
    pip install py3plex

Dependency Pinning
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Generate requirements.txt
    pip freeze > requirements.txt
    
    # Reproduce environment
    pip install -r requirements.txt

Docker Containers (Overview)
-----------------------------

[High-level benefits—detailed configs in Appendix B]

Why Docker?
~~~~~~~~~~~

* **Isolation** — No system Python conflicts
* **Reproducibility** — Identical environment across machines
* **Portability** — Share complete environment

Basic Docker Usage
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Build image
    docker build -t py3plex:latest .
    
    # Run analysis
    docker run --rm py3plex:latest python analysis.py

[For detailed Dockerfile, Compose configs → See Appendix B]

Seed Management
---------------

[Ensuring deterministic results]

Setting Seeds
~~~~~~~~~~~~~

.. code-block:: python

    # For dynamics
    from py3plex.dynamics.models import SIRDynamics
    
    sir = SIRDynamics(network, beta=0.3, gamma=0.1)
    sir.set_seed(42)  # Reproducible results
    
    # For random graph generation
    import random
    random.seed(42)

Recording Environments
----------------------

Environment Captures
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Save environment info
    import platform
    import py3plex
    
    print(f"Python: {platform.python_version()}")
    print(f"py3plex: {py3plex.__version__}")
    print(f"Platform: {platform.platform()}")

Version Control
~~~~~~~~~~~~~~~

[Git for code, data versioning strategies]

Summary
-------

**Key practices:**

* Use virtual environments or containers
* Pin dependencies with requirements.txt
* Set seeds for stochastic processes
* Record environment details in papers/reports

[Detailed Docker configs and CI setup → Appendices]

*Source files:*
- docfiles/deployment/cli_and_docker.rst (high-level)
- Dockerfile and docker-compose.yml → Appendix B
- docfiles/dev/development_guide.rst
