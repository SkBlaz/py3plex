Reproducible Environments
======================================

Reproducibility is fundamental to scientific computing. This chapter covers practices for creating consistent, reproducible analysis environments using py3plex. **For detailed Docker configurations and deployment recipes, see Appendix B.**

Reproducibility Principles
---------------------------

Reproducible research requires:

1. **Isolated environments** — Avoid conflicts between projects and system packages
2. **Dependency pinning** — Lock package versions to prevent drift
3. **Seed management** — Control randomness in stochastic processes
4. **Environment documentation** — Record exact configurations used

Without these practices, analyses may produce different results on different machines or at different times, undermining scientific validity.

Environment Management
----------------------

Python Virtual Environments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``venv`` or ``conda`` to isolate py3plex installations:

**Using venv (built-in):**

.. code-block:: bash

    # Create virtual environment
    python3 -m venv py3plex-env
    
    # Activate (Linux/macOS)
    source py3plex-env/bin/activate
    
    # Activate (Windows)
    py3plex-env\Scripts\activate
    
    # Install py3plex
    pip install py3plex
    
    # Deactivate when done
    deactivate

**Using conda:**

.. code-block:: bash

    # Create conda environment
    conda create -n py3plex python=3.10
    
    # Activate
    conda activate py3plex
    
    # Install py3plex
    pip install py3plex
    
    # Deactivate
    conda deactivate

**Recommendation:** Use ``venv`` for simple projects, ``conda`` when you need non-Python dependencies (e.g., graph-tool, igraph bindings).

Dependency Pinning
~~~~~~~~~~~~~~~~~~

Lock exact package versions to ensure reproducibility:

**Two-file approach (recommended):**

1. ``requirements.in`` — High-level dependencies with version ranges

   .. code-block:: text
   
       # requirements.in
       py3plex>=1.0.0
       numpy>=1.24.0
       networkx>=3.0

2. ``requirements.txt`` — Exact pinned versions (generated)

   .. code-block:: bash
   
       # Generate exact pins from requirements.in
       pip-compile requirements.in --output-file requirements.txt
       
       # This creates entries like:
       # py3plex==1.1.3
       # numpy==1.24.3
       # networkx==3.1
       # matplotlib==3.7.1
       # scipy==1.10.1
       # pandas==2.0.2
       # (includes all transitive dependencies)
   
   **Install from pinned file:**
   
   .. code-block:: bash
   
       pip install -r requirements.txt

**Single-file approach (simpler but less flexible):**

.. code-block:: bash

    # Generate requirements file with exact versions
    pip freeze > requirements.txt
    
    # Reproduce environment on another machine
    pip install -r requirements.txt

**Trade-offs:**

- **Exact pins** (``==``) ensure reproducibility but may miss security patches
- **Version ranges** (``>=``) allow updates but may introduce drift
- **Recommended:** Use exact pins in ``requirements.txt`` for reproducible research, 
  maintain ``requirements.in`` with ranges for development

**Best practices:**

* Commit ``requirements.txt`` to version control
* Regenerate when dependencies change
* Use separate files for development (``requirements-dev.txt``) and production

**Example requirements.txt structure (with exact pins):**

.. code-block:: text

    # Core dependencies (exact versions)
    py3plex==1.1.3
    numpy==1.24.3
    scipy==1.10.1
    networkx==3.1
    
    # Optional features
    matplotlib==3.7.1
    pandas==2.0.2

Docker Containers (Overview)
-----------------------------

Docker provides the strongest reproducibility guarantees by packaging the entire environment—OS, Python, libraries, and code—into a container.

Why Docker?
~~~~~~~~~~~

* **Complete isolation** — No system Python conflicts, no OS differences
* **Perfect reproducibility** — Identical environment across machines and time
* **Portability** — Share complete analysis environment with collaborators
* **Deployment** — Easy transition from development to production

Basic Docker Usage
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Build py3plex image
    docker build -t py3plex:latest .
    
    # Run analysis script
    docker run --rm -v $(pwd):/workspace py3plex:latest \
        python /workspace/analysis.py
    
    # Interactive shell
    docker run --rm -it py3plex:latest bash

**When to use Docker:**

* **Multi-machine reproducibility** — Running on clusters, cloud, or different dev machines
* **Long-term archival** — Preserve exact environment for future replication
* **Production deployment** — Consistent behavior from dev to production

**For detailed Dockerfile examples, docker-compose configurations, and deployment recipes, see Appendix B.**

Seed Management
---------------

Controlling Randomness
~~~~~~~~~~~~~~~~~~~~~~

Set seeds for all stochastic processes to ensure deterministic results:

.. code-block:: python

    import random
    import numpy as np
    
    # Set global seeds
    random.seed(42)
    np.random.seed(42)
    
    # For dynamics models
    from py3plex.dynamics import SIRDynamics
    
    sir = SIRDynamics(network, beta=0.3, gamma=0.1)
    sir.set_seed(42)  # Reproducible epidemic simulation
    results = sir.run(steps=100)
    
    # For random graph generation
    import networkx as nx
    G = nx.erdos_renyi_graph(100, 0.1, seed=42)

**Seed management checklist:**

1. Set seeds at the **start** of scripts before any randomness
2. Document seed values in code comments and papers
3. Use **different seeds** for different experiments (42, 43, 44, ...)
4. Re-run with multiple seeds to assess variability

Recording Environments
----------------------

Document Analysis Environments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Record environment details for publication and replication:

.. code-block:: python

    import platform
    import sys
    import py3plex
    import numpy as np
    import networkx as nx
    
    # Print environment summary
    print("Environment Information:")
    print(f"  Python: {sys.version}")
    print(f"  Platform: {platform.platform()}")
    print(f"  py3plex: {py3plex.__version__}")
    print(f"  NumPy: {np.__version__}")
    print(f"  NetworkX: {nx.__version__}")

**Include in papers/reports:**

* Python version (e.g., Python 3.10.8)
* py3plex version (e.g., 1.1.3)
* Key dependency versions (NumPy, NetworkX, SciPy)
* Operating system (Linux, macOS, Windows)
* Hardware details for performance-critical analyses

Version Control for Code
~~~~~~~~~~~~~~~~~~~~~~~~~

Use Git to track code changes:

.. code-block:: bash

    # Initialize repository
    git init
    git add analysis.py requirements.txt
    git commit -m "Initial analysis code"
    
    # Tag important versions
    git tag -a v1.0 -m "Version used for paper submission"

**Best practices:**

* Commit ``requirements.txt`` and environment configs
* Use meaningful commit messages
* Tag versions used for publications
* Don't commit large datasets (use Git LFS or external storage)

Version Control for Data
~~~~~~~~~~~~~~~~~~~~~~~~~

For input datasets:

* **Small datasets (<100 MB):** Commit directly to Git
* **Medium datasets (100 MB - 1 GB):** Use Git LFS
* **Large datasets (>1 GB):** Store externally (Zenodo, OSF, Dataverse) and include download script

**Example download script:**

.. code-block:: python

    # download_data.py
    import urllib.request
    
    # Dataset DOI and URL
    DOI = "10.5281/zenodo.1234567"
    URL = "https://zenodo.org/record/1234567/files/network.edgelist"
    
    print(f"Downloading dataset from {DOI}")
    urllib.request.urlretrieve(URL, "data/network.edgelist")
    print("Download complete")

Summary
-------

**Essential practices for reproducible py3plex analyses:**

1. **Use virtual environments** (venv or conda) to isolate dependencies
2. **Pin exact versions** with ``pip freeze > requirements.txt``
3. **Set random seeds** for all stochastic processes
4. **Record environment details** in papers and code comments
5. **Use version control** (Git) for code, Git LFS or external storage for data
6. **Consider Docker** for maximum reproducibility and deployment

**For production deployments:**

* Use Docker containers for complete environment isolation
* See Appendix B for Dockerfile templates and docker-compose configurations
* See Appendix A for repository structure best practices

**Next chapter:** Overview of the py3plex GUI for visual exploration
