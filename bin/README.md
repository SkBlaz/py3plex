# Binary Dependencies

This directory previously contained bundled Infomap and Node2Vec binaries. These have been removed to:

1. Reduce repository size (~5MB)
2. Improve licensing clarity (AGPL vs BSD)
3. Support cross-platform compatibility
4. Simplify maintenance

## Installation Options

### Option 1: Use Python Alternatives (Recommended)

#### For Community Detection (Infomap alternative):
```bash
pip install python-louvain  # Louvain community detection (already included)
# Or use the built-in Louvain: from py3plex.algorithms.community_detection import louvain_communities
```

#### For Node Embeddings (Node2Vec alternative):
```bash
pip install node2vec  # Pure Python implementation
# Or
pip install pecanpy  # Fast parallel implementation
```

### Option 2: Install Binaries Manually

#### Infomap:
1. Download from: https://www.mapequation.org/infomap/
2. Place the binary in this directory or specify path in your code:
   ```python
   infomap_communities(network, binary="./bin/Infomap")
   ```

#### Node2Vec:
1. Download/compile from: https://github.com/snap-stanford/snap/tree/master/examples/node2vec
2. Place the binary in this directory or specify path in your code:
   ```python
   n2v_embedding(G, targets, binary_path="./bin/node2vec")
   ```

## Using in Code

The library will provide clear error messages if binaries are missing, along with suggestions for alternatives.

Example error:
```
FileNotFoundError: Node2Vec binary not found at './node2vec'. 
Please provide a valid path to the Node2Vec binary, 
or consider using pure Python alternatives like 'node2vec' or 'pecanpy' packages: 
pip install node2vec
```

## License Considerations

- **Infomap**: Released under AGPL-3.0 license (copyleft, requires open-source distribution)
- **Node2Vec**: Released under BSD-style license (permissive)
- **py3plex core**: Released under BSD-3-Clause license (permissive)

If you need to use Infomap, ensure your project is compatible with AGPL licensing terms or use the Louvain alternative instead.
