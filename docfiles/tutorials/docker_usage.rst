Docker Usage Guide
==================

This guide provides comprehensive instructions for using Py3plex via Docker.

.. contents:: Table of Contents
   :local:
   :depth: 2

Quick Start
-----------

The fastest way to get started with Py3plex using Docker:

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

.. code-block:: bash

    # Build from the repository root
    docker build -t py3plex:latest .

    # Build with a specific tag
    docker build -t py3plex:0.95a .

    # Build without cache (if needed)
    docker build --no-cache -t py3plex:latest .

Using Docker Compose
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Build using docker-compose
    docker-compose build

    # Force rebuild
    docker-compose build --no-cache

Running Commands
----------------

Basic Commands
~~~~~~~~~~~~~~

The Docker container is set up with ``py3plex`` as the entrypoint, so you can run any py3plex CLI command directly:

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

With docker-compose, commands are slightly more verbose but easier to manage:

.. code-block:: bash

    # Show version
    docker-compose run --rm py3plex --version

    # Run self-test
    docker-compose run --rm py3plex selftest -v

    # Show help
    docker-compose run --rm py3plex help

Working with Files
------------------

To work with network files, you need to mount a local directory to the container's ``/data`` directory.

Creating a Data Directory
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Create a local data directory
    mkdir -p data

Mounting Volumes
~~~~~~~~~~~~~~~~

**With docker run:**

.. code-block:: bash

    # Mount current directory's data folder
    docker run --rm -v $(pwd)/data:/data py3plex:latest create --nodes 100 --layers 3 --output /data/network.edgelist

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

If you need additional packages:

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

You can extend the ``docker-compose.yml`` to include related services:

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

If you encounter permission issues with mounted volumes:

.. code-block:: bash

    # On Linux, you might need to run with your user ID
    docker run --rm -v $(pwd)/data:/data --user $(id -u):$(id -g) py3plex:latest create --output /data/network.edgelist

Container Not Found
~~~~~~~~~~~~~~~~~~~

If the image isn't found:

.. code-block:: bash

    # List available images
    docker images | grep py3plex

    # Rebuild if necessary
    docker build -t py3plex:latest .

Network Issues During Build
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you encounter network timeouts during build:

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

1. **Use Volume Mounts**: Always mount volumes for input/output files
2. **Use --rm Flag**: Remove containers after execution with ``--rm`` to save space
3. **Tag Images**: Use specific tags (e.g., ``py3plex:0.95a``) for reproducibility
4. **Keep Data Separate**: Store network files in the mounted ``data`` directory
5. **Use Docker Compose**: For repeated operations, docker-compose simplifies commands
6. **Regular Updates**: Rebuild the image periodically to get latest py3plex updates

Practical Examples
------------------

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
* :doc:`CLI Tutorial <cli_usage>`
* `Docker Documentation <https://docs.docker.com/>`_
* `Docker Compose Documentation <https://docs.docker.com/compose/>`_

Support
-------

For issues related to:

* **Py3plex functionality**: Open an issue at https://github.com/SkBlaz/py3plex/issues
* **Docker setup**: Check this guide first, then open an issue if problems persist
* **General questions**: See the main README.md and documentation
