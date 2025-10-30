# Docker Examples for Py3plex

This directory contains example scripts and workflows for using Py3plex with Docker.

## Quick Examples

### 1. Basic Network Analysis

Create and analyze a multilayer network:

```bash
# Create data directory
mkdir -p ../data

# Create a network
docker run --rm -v $(pwd)/../data:/data py3plex:latest \
  create --nodes 100 --layers 3 --type random --probability 0.05 \
  --output /data/network.edgelist

# Analyze the network
docker run --rm -v $(pwd)/../data:/data py3plex:latest \
  load /data/network.edgelist --info --stats

# Visualize
docker run --rm -v $(pwd)/../data:/data py3plex:latest \
  visualize /data/network.edgelist --output /data/network.png
```

### 2. Community Detection

```bash
# Detect communities using Louvain
docker run --rm -v $(pwd)/../data:/data py3plex:latest \
  community /data/network.edgelist --algorithm louvain \
  --output /data/communities.json

# View community statistics
cat ../data/communities.json | python -m json.tool | head -20
```

### 3. Centrality Analysis

```bash
# Compute degree centrality
docker run --rm -v $(pwd)/../data:/data py3plex:latest \
  centrality /data/network.edgelist --measure degree \
  --top 10 --output /data/centrality.json

# Compute betweenness centrality
docker run --rm -v $(pwd)/../data:/data py3plex:latest \
  centrality /data/network.edgelist --measure betweenness \
  --top 10 --output /data/betweenness.json
```

### 4. Batch Processing

Process multiple networks (save as `batch-process.sh`):

```bash
#!/bin/bash
# Process multiple networks in batch

DATA_DIR=$(pwd)/../data
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
```

### 5. Using with Docker Compose

If you prefer docker-compose:

```bash
# Build once
docker-compose build

# Create network
docker-compose run --rm py3plex create --nodes 100 --layers 3 \
  --output /data/network.edgelist

# Analyze
docker-compose run --rm py3plex stats /data/network.edgelist --measure all

# Visualize
docker-compose run --rm py3plex visualize /data/network.edgelist \
  --output /data/network.png
```

### 6. Interactive Python Session

Work with py3plex interactively:

```bash
# Start Python in the container
docker run --rm -it -v $(pwd)/../data:/data \
  --entrypoint python py3plex:latest

# Inside Python:
# >>> from py3plex.core import multinet
# >>> network = multinet.multi_layer_network()
# >>> # Your code here...
```

### 7. Custom Analysis Script

Create a Python script (`analysis.py`) and run it in the container:

```python
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
```

Run it:
```bash
# Copy script to data directory
cp analysis.py ../data/

# Run in container
docker run --rm -v $(pwd)/../data:/data \
  --entrypoint python py3plex:latest /data/analysis.py
```

## Advanced Examples

### Pipeline Example

Complete analysis pipeline:

```bash
#!/bin/bash
# complete-pipeline.sh
set -e

DATA_DIR=$(pwd)/../data
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
```

### Comparative Analysis

Compare different network types:

```bash
#!/bin/bash
# compare-networks.sh

DATA_DIR=$(pwd)/../data
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
```

## CI/CD Examples

### GitHub Actions

```yaml
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
```

### GitLab CI

```yaml
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
```

## Tips

1. **Performance**: Building the Docker image the first time takes a few minutes. Subsequent builds are faster due to layer caching.

2. **Data Persistence**: Always use volume mounts (`-v`) to persist data outside the container.

3. **Permissions**: If you encounter permission issues, you may need to specify user ID:
   ```bash
   docker run --rm --user $(id -u):$(id -g) -v $(pwd)/data:/data py3plex:latest [commands]
   ```

4. **Memory Limits**: For large networks, you may need to increase Docker's memory limit.

5. **Cleanup**: Remove unused images regularly:
   ```bash
   docker system prune -a
   ```

## More Information

- Main documentation: [README.md](../README.md)
- Detailed Docker guide: [DOCKER.md](../DOCKER.md)
- Py3plex documentation: https://skblaz.github.io/py3plex/
