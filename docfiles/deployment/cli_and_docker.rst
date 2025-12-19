Docker Usage Guide
==================

This guide provides concise, step-by-step instructions for running Py3plex with Docker. It assumes Docker is installed and that you are working from the repository root unless noted otherwise.

.. contents:: Table of Contents
   :local:
   :depth: 2

Prerequisites
-------------

* Docker installed and running (``docker ps`` should work).
* Optional: Docker Compose (``docker compose`` or ``docker-compose``) if you prefer compose workflows.
* Run commands from the repository root unless a command explicitly sets another path.

Quickstart
-----------

The fastest way to get started with Py3plex using Docker (uses the ``latest`` tag):

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex

    # Build the Docker image
    docker build -t py3plex:latest .

    # Run a self-test to verify installation
    docker run --rm py3plex:latest selftest

    # Display help
    docker run --rm py3plex:latest help

Building the Image
------------------

Using Docker
~~~~~~~~~~~~

Build directly from the repository root:

.. code-block:: bash

    # Build from the repository root (default tag)
    docker build -t py3plex:latest .

    # Build with a specific tag
    docker build -t py3plex:0.95a .

    # Build without cache (if needed)
    docker build --no-cache -t py3plex:latest .

Using Docker Compose
~~~~~~~~~~~~~~~~~~~~

If you prefer docker-compose (or ``docker compose``), use the provided configuration:

.. code-block:: bash

    # Build using docker-compose (v1 syntax)
    docker-compose build

    # Force rebuild
    docker-compose build --no-cache

Running Commands
----------------

Basic Commands
~~~~~~~~~~~~~~

The image sets ``py3plex`` as the entrypoint, so you can run CLI commands directly. Substitute your tag if not using ``latest``.

.. code-block:: bash

    # Show version
    docker run --rm py3plex:latest --version

    # Run self-test
    docker run --rm py3plex:latest selftest

    # Show help
    docker run --rm py3plex:latest help

    # Show help for a specific command
    docker run --rm py3plex:latest create --help

Using Docker Compose
~~~~~~~~~~~~~~~~~~~~

With Docker Compose, commands are slightly more verbose but easier to repeat:

.. code-block:: bash

    # Show version
    docker-compose run --rm py3plex --version

    # Run self-test
    docker-compose run --rm py3plex selftest -v

    # Show help
    docker-compose run --rm py3plex help
    # Show help (modern syntax)
    docker compose run --rm py3plex help

Working with Files
------------------

To persist inputs/outputs, mount a local directory to ``/data`` inside the container. Examples assume ``./data`` on the host and a POSIX shell; adjust the path syntax for Windows shells.

Creating a Data Directory
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Create a local data directory
    mkdir -p data

Mounting Volumes
~~~~~~~~~~~~~~~~

**With docker run:**

.. code-block:: bash

    # Mount current directory's data folder (Linux/macOS)
    docker run --rm -v $(pwd)/data:/data py3plex:latest create --nodes 100 --layers 3 --output /data/network.edgelist

    # If your path contains spaces, quote it:
    docker run --rm -v "$(pwd)"/data:/data py3plex:latest create --nodes 100 --layers 3 --output /data/network.edgelist

    # On Windows (PowerShell)
    docker run --rm -v ${PWD}/data:/data py3plex:latest create --nodes 100 --layers 3 --output /data/network.edgelist

    # On Windows (CMD)
    docker run --rm -v %cd%/data:/data py3plex:latest create --nodes 100 --layers 3 --output /data/network.edgelist

**With docker-compose:**

The ``docker-compose.yml`` file already configures volume mounting from ``./data`` to ``/data``, so you can simply:

.. code-block:: bash

    docker-compose run --rm py3plex create --nodes 100 --layers 3 --output /data/network.edgelist

Complete Workflow Example
~~~~~~~~~~~~~~~~~~~~~~~~~

End-to-end example using volume mounts and the default ``latest`` tag:

.. code-block:: bash

    # Create data directory
    mkdir -p data

    # 1. Create a multilayer network
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      create --nodes 100 --layers 3 --type random --probability 0.1 --output /data/network.edgelist

    # 2. Load and display network information
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      load /data/network.edgelist --info

    # 3. Compute statistics
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      stats /data/network.edgelist --measure all --output /data/stats.json

    # 4. Detect communities
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      community /data/network.edgelist --algorithm louvain --output /data/communities.json

    # 5. Visualize the network
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      visualize /data/network.edgelist --output /data/network.png --layout multilayer

    # 6. View the results
    ls -lh data/

Advanced Usage
--------------

Interactive Shell
~~~~~~~~~~~~~~~~~

To explore the container interactively:

.. code-block:: bash

    # Start an interactive shell in the container
    docker run --rm -it -v $(pwd)/data:/data --entrypoint /bin/bash py3plex:latest

    # Inside the container, you can run:
    # py3plex --version
    # py3plex selftest
    # python -c "import py3plex; print(py3plex.__version__)"

Using Python API
~~~~~~~~~~~~~~~~

You can also use py3plex as a Python library inside the container:

.. code-block:: bash

    # Create a Python script
    cat > data/analyze.py << 'EOF'
    from py3plex.core import multinet

    # Create a network
    network = multinet.multi_layer_network()
    nodes = [{"source": f"node{i}", "type": "layer1"} for i in range(10)]
    network.add_nodes(nodes, input_type="dict")

    print(f"Created network with {network.core_network.number_of_nodes()} nodes")
    EOF

    # Run the script in the container
    docker run --rm -v $(pwd)/data:/data --entrypoint python py3plex:latest /data/analyze.py

Custom Image Builds
~~~~~~~~~~~~~~~~~~~

If you need additional Python or system packages, extend the base image. Pin the base tag you want to customize (e.g., ``py3plex:latest`` or a versioned tag):

.. code-block:: dockerfile

    # Create a custom Dockerfile
    FROM py3plex:latest

    # Install additional packages
    RUN pip install --no-cache-dir pandas jupyter

    # Or system packages
    USER root
    RUN apt-get update && apt-get install -y vim && rm -rf /var/lib/apt/lists/*
    USER py3plex

Docker Compose with Multiple Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can extend the ``docker-compose.yml`` to include related services and run them together (``docker compose up jupyter``):

.. code-block:: yaml

    version: '3.8'

    services:
      py3plex:
        build: .
        image: py3plex:latest
        volumes:
          - ./data:/data

      jupyter:
        image: py3plex:latest
        ports:
          - "8888:8888"
        volumes:
          - ./data:/data
          - ./notebooks:/notebooks
        command: jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root
        working_dir: /notebooks

Helper Scripts
--------------

The repository includes optional helper scripts to simplify Docker usage.

py3plex-docker.sh
~~~~~~~~~~~~~~~~~

A wrapper script that simplifies running py3plex commands via Docker:

.. code-block:: bash

    # The script automatically handles:
    # - Docker installation checks
    # - Image building (if needed)
    # - Data directory creation
    # - Volume mounting
    
    # Usage examples:
    ./py3plex-docker.sh --version
    ./py3plex-docker.sh selftest
    ./py3plex-docker.sh create --nodes 100 --layers 3 --output /data/network.edgelist
    ./py3plex-docker.sh load /data/network.edgelist --info

**Features:**

* Automatically checks if Docker is installed
* Prompts to build the image if it doesn't exist
* Creates the ``data/`` directory if needed
* Mounts the local ``data/`` directory to ``/data`` in the container
* Passes all arguments directly to py3plex

**Script location:** ``py3plex-docker.sh`` in the repository root

test-docker-setup.sh
~~~~~~~~~~~~~~~~~~~~

A comprehensive test script to validate your Docker setup:

.. code-block:: bash

    # Run the validation script
    ./test-docker-setup.sh

**What it tests:**

1. Docker installation verification
2. Dockerfile existence check
3. .dockerignore existence check
4. docker-compose.yml existence check
5. Docker image build process
6. Container version command
7. Container help command
8. Container selftest
9. Volume mounting and file creation

The script provides colored output ([OK] PASS / [X] FAIL) and a summary report.

**Script location:** ``test-docker-setup.sh`` in the repository root

Docker Configuration Files
--------------------------

.dockerignore
~~~~~~~~~~~~~

The ``.dockerignore`` file controls which files are excluded from the Docker build context:

**Key exclusions:**

* **Git and version control**: ``.git/``, ``.github/``, ``.gitignore``
* **Python artifacts**: ``__pycache__/``, ``*.pyc``, ``dist/``, ``build/``
* **Virtual environments**: ``venv/``, ``env/``
* **Testing and coverage**: ``.pytest_cache/``, ``htmlcov/``, ``coverage.*``
* **Documentation builds**: ``docs/_build/``, ``docfiles/``
* **Examples and datasets**: ``examples/``, ``datasets/``, ``multilayer_datasets/``
* **Development files**: ``tests/``, ``run_tests.py``, ``validate_*.py``

**Why this matters:**

* **Faster builds**: Smaller build context means faster Docker builds
* **Smaller images**: Excludes unnecessary files from the final image
* **Security**: Prevents accidental inclusion of sensitive files
* **Efficiency**: Only includes files needed to run py3plex

The ``.dockerignore`` file is located in the repository root.



Troubleshooting
---------------

Testing the Docker Setup
~~~~~~~~~~~~~~~~~~~~~~~~

To verify your Docker setup is working correctly, use the included test script:

.. code-block:: bash

    # Run the test script
    ./test-docker-setup.sh

This script will:

* Check Docker installation
* Verify all Docker-related files exist
* Build the Docker image
* Run basic py3plex commands (--version, help, selftest)
* Test volume mounting and file creation
* Clean up test artifacts

Permission Issues
~~~~~~~~~~~~~~~~~

If you encounter permission issues with mounted volumes (common on Linux), run with your UID/GID so files stay writable on the host:

.. code-block:: bash

    # On Linux, you might need to run with your user ID
    docker run --rm -v $(pwd)/data:/data --user $(id -u):$(id -g) py3plex:latest create --output /data/network.edgelist

Container Not Found
~~~~~~~~~~~~~~~~~~~

If the image is missing locally:

.. code-block:: bash

    # List available images
    docker images | grep py3plex

    # Rebuild if necessary
    docker build -t py3plex:latest .

Network Issues During Build
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you encounter network timeouts during build, try a higher timeout or a different PyPI mirror:

.. code-block:: bash

    # Increase timeout
    docker build --build-arg PIP_DEFAULT_TIMEOUT=300 -t py3plex:latest .

    # Or use a different PyPI mirror
    docker build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple -t py3plex:latest .

Out of Disk Space
~~~~~~~~~~~~~~~~~

Clean up unused Docker resources:

.. code-block:: bash

    # Remove unused images
    docker image prune -a

    # Remove all stopped containers, unused networks, and dangling images
    docker system prune -a

Debugging Build Issues
~~~~~~~~~~~~~~~~~~~~~~

Build with verbose output:

.. code-block:: bash

    docker build --progress=plain --no-cache -t py3plex:latest .

Best Practices
--------------

1. **Use Volume Mounts:** Always mount volumes for input/output files.
2. **Use --rm Flag:** Remove containers after execution with ``--rm`` to save space.
3. **Tag Images:** Use specific tags (e.g., ``py3plex:0.95a``) for reproducibility.
4. **Keep Data Separate:** Store network files in the mounted ``data`` directory.
5. **Use Docker Compose:** For repeated operations, Docker Compose simplifies commands.
6. **Regular Updates:** Rebuild the image periodically to get the latest Py3plex updates.

Practical Examples
------------------

The following examples assume you created ``./data`` and will reuse it across commands.

Basic Network Analysis
~~~~~~~~~~~~~~~~~~~~~~

Create and analyze a multilayer network:

.. code-block:: bash

    # Create data directory
    mkdir -p data

    # Create a network
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      create --nodes 100 --layers 3 --type random --probability 0.05 \
      --output /data/network.edgelist

    # Analyze the network
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      load /data/network.edgelist --info --stats

    # Visualize
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      visualize /data/network.edgelist --output /data/network.png

Community Detection
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Detect communities using Louvain
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      community /data/network.edgelist --algorithm louvain \
      --output /data/communities.json

    # View community statistics
    cat data/communities.json | python -m json.tool | head -20

Centrality Analysis
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Compute degree centrality
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      centrality /data/network.edgelist --measure degree \
      --top 10 --output /data/centrality.json

    # Compute betweenness centrality
    docker run --rm -v $(pwd)/data:/data py3plex:latest \
      centrality /data/network.edgelist --measure betweenness \
      --top 10 --output /data/betweenness.json

Batch Processing
~~~~~~~~~~~~~~~~

Process multiple networks (save as ``batch-process.sh``):

.. code-block:: bash

    #!/bin/bash
    # Process multiple networks in batch
    set -e

    DATA_DIR=$(pwd)/data
    mkdir -p $DATA_DIR

    # Create several networks
    for i in {1..5}; do
      echo "Creating network $i..."
      docker run --rm -v $DATA_DIR:/data py3plex:latest \
        create --nodes $((50 * i)) --layers 3 \
        --type random --probability 0.1 \
        --output /data/network_$i.edgelist
    done

    # Analyze each network
    for i in {1..5}; do
      echo "Analyzing network $i..."
      docker run --rm -v $DATA_DIR:/data py3plex:latest \
        stats /data/network_$i.edgelist --measure all \
        --output /data/stats_$i.json
    done

    echo "Done! Results in $DATA_DIR"

Custom Analysis Script
~~~~~~~~~~~~~~~~~~~~~~

Create a Python script (``analysis.py``) and run it in the container:

**Python script:**

.. code-block:: python

    # analysis.py
    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls

    # Load network
    network = multinet.multi_layer_network()
    network.load_network("/data/network.edgelist", input_type="multiedgelist")

    # Compute statistics
    layers = ["layer1", "layer2", "layer3"]
    for layer in layers:
        density = mls.layer_density(network, layer)
        print(f"{layer} density: {density:.4f}")

    print("Analysis complete!")

**Run it:**

.. code-block:: bash

    # Copy script to data directory
    cp analysis.py data/

    # Run in container
    docker run --rm -v $(pwd)/data:/data \
      --entrypoint python py3plex:latest /data/analysis.py

Complete Analysis Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A comprehensive analysis pipeline:

.. code-block:: bash

    #!/bin/bash
    # complete-pipeline.sh
    set -e

    DATA_DIR=$(pwd)/data
    mkdir -p $DATA_DIR

    echo "Step 1: Creating network..."
    docker run --rm -v $DATA_DIR:/data py3plex:latest \
      create --nodes 200 --layers 3 --type ba --probability 0.05 \
      --output /data/network.edgelist

    echo "Step 2: Computing statistics..."
    docker run --rm -v $DATA_DIR:/data py3plex:latest \
      stats /data/network.edgelist --measure all \
      --output /data/stats.json

    echo "Step 3: Detecting communities..."
    docker run --rm -v $DATA_DIR:/data py3plex:latest \
      community /data/network.edgelist --algorithm louvain \
      --output /data/communities.json

    echo "Step 4: Computing centrality..."
    docker run --rm -v $DATA_DIR:/data py3plex:latest \
      centrality /data/network.edgelist --measure pagerank \
      --top 20 --output /data/centrality.json

    echo "Step 5: Visualizing..."
    docker run --rm -v $DATA_DIR:/data py3plex:latest \
      visualize /data/network.edgelist --output /data/network.png \
      --layout multilayer --width 16 --height 12

    echo "Pipeline complete! Check $DATA_DIR for results."

Comparative Network Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compare different network types:

.. code-block:: bash

    #!/bin/bash
    # compare-networks.sh
    set -e

    DATA_DIR=$(pwd)/data
    mkdir -p $DATA_DIR

    TYPES=("random" "er" "ba" "ws")

    for type in "${TYPES[@]}"; do
      echo "Creating $type network..."
      docker run --rm -v $DATA_DIR:/data py3plex:latest \
        create --nodes 100 --layers 3 --type $type --probability 0.1 \
        --output /data/network_${type}.edgelist
      
      echo "Analyzing $type network..."
      docker run --rm -v $DATA_DIR:/data py3plex:latest \
        stats /data/network_${type}.edgelist --measure all \
        --output /data/stats_${type}.json
    done

    echo "Comparison complete!"

CI/CD Integration
-----------------

GitHub Actions
~~~~~~~~~~~~~~

Example workflow for network analysis:

.. code-block:: yaml

    # .github/workflows/network-analysis.yml
    name: Network Analysis with Docker

    on: [push, pull_request]

    jobs:
      analyze:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          
          - name: Build Docker image
            run: docker build -t py3plex:latest .
          
          - name: Create test network
            run: |
              mkdir -p data
              docker run --rm -v $PWD/data:/data py3plex:latest \
                create --nodes 50 --layers 2 --output /data/test.edgelist
          
          - name: Run analysis
            run: |
              docker run --rm -v $PWD/data:/data py3plex:latest \
                stats /data/test.edgelist --measure all --output /data/stats.json
          
          - name: Upload results
            uses: actions/upload-artifact@v3
            with:
              name: analysis-results
              path: data/

GitLab CI
~~~~~~~~~

Example GitLab CI configuration:

.. code-block:: yaml

    # .gitlab-ci.yml
    image: docker:latest

    services:
      - docker:dind

    variables:
      DOCKER_DRIVER: overlay2

    stages:
      - build
      - analyze

    build:
      stage: build
      script:
        - docker build -t py3plex:latest .
        - docker save py3plex:latest > py3plex-image.tar
      artifacts:
        paths:
          - py3plex-image.tar

    analyze:
      stage: analyze
      script:
        - docker load < py3plex-image.tar
        - mkdir -p data
        - docker run --rm -v $PWD/data:/data py3plex:latest create --nodes 100 --layers 3 --output /data/network.edgelist
        - docker run --rm -v $PWD/data:/data py3plex:latest stats /data/network.edgelist --measure all --output /data/stats.json
      artifacts:
        paths:
          - data/

Additional Resources
--------------------

* `Py3plex Documentation <https://skblaz.github.io/py3plex/>`_
* :doc:`CLI Tutorial <./cli_usage>`
* `Docker Documentation <https://docs.docker.com/>`_
* `Docker Compose Documentation <https://docs.docker.com/compose/>`_
* `DOCKER.md <https://github.com/SkBlaz/py3plex/blob/master/DOCKER.md>`_ - Main Docker guide in the repository

Support
-------

For issues related to:

* **Py3plex functionality**: Open an issue at https://github.com/SkBlaz/py3plex/issues
* **Docker setup**: Check this guide first, then open an issue if problems persist
* **General questions**: See the main README.md and documentation
