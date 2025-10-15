# Algorithm Citations and References

This document provides citations for the algorithms implemented in py3plex. When using these algorithms in your research, please cite the original publications.

## Community Detection Algorithms

### Louvain Algorithm
- **Implementation**: `py3plex.algorithms.community_detection.community.community_louvain`
- **Citation**: Blondel, V. D., Guillaume, J. L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. Journal of Statistical Mechanics: Theory and Experiment, 2008(10), P10008.
- **DOI**: https://doi.org/10.1088/1742-5468/2008/10/P10008
- **Description**: Fast modularity optimization algorithm for community detection in large networks.

### Multilayer Modularity
- **Implementation**: `py3plex.algorithms.community_detection.multilayer_modularity`
- **Citation**: Mucha, P. J., Richardson, T., Macon, K., Porter, M. A., & Onnela, J. P. (2010). Community structure in time-dependent, multiscale, and multiplex networks. Science, 328(5980), 876-878.
- **DOI**: https://doi.org/10.1126/science.1184819
- **Description**: Extension of modularity for multilayer network community detection with interlayer coupling.

### Infomap
- **Implementation**: `py3plex.algorithms.community_detection.infomap` (wrapper)
- **Citation**: Rosvall, M., & Bergstrom, C. T. (2008). Maps of random walks on complex networks reveal community structure. Proceedings of the National Academy of Sciences, 105(4), 1118-1123.
- **DOI**: https://doi.org/10.1073/pnas.0706851105
- **Description**: Information-theoretic approach to community detection based on random walks.
- **Note**: Requires external Infomap binary installation.

### Label Propagation
- **Implementation**: Uses NetworkX implementation via wrappers
- **Citation**: Raghavan, U. N., Albert, R., & Kumara, S. (2007). Near linear time algorithm to detect community structures in large-scale networks. Physical Review E, 76(3), 036106.
- **DOI**: https://doi.org/10.1103/PhysRevE.76.036106
- **Description**: Fast semi-supervised algorithm that propagates labels through the network.

## Network Embedding

### Node2Vec
- **Implementation**: `py3plex.wrappers.node2vec_embedding`
- **Citation**: Grover, A., & Leskovec, J. (2016). node2vec: Scalable feature learning for networks. In Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (pp. 855-864).
- **DOI**: https://doi.org/10.1145/2939672.2939754
- **Description**: Generates node embeddings using biased random walks that balance breadth-first and depth-first search.
- **Note**: Requires external Node2Vec binary or python implementation.

## Centrality Measures

### PageRank
- **Implementation**: Uses NetworkX implementation
- **Citation**: Page, L., Brin, S., Motwani, R., & Winograd, T. (1999). The PageRank citation ranking: Bringing order to the web. Stanford InfoLab.
- **URL**: http://ilpubs.stanford.edu:8090/422/
- **Description**: Ranking algorithm measuring node importance based on the structure of incoming links.

### Multilayer Centrality
- **Implementation**: `py3plex.algorithms.node_ranking`
- **Citation**: De Domenico, M., Solé-Ribalta, A., Omodei, E., Gómez, S., & Arenas, A. (2015). Ranking in interconnected multilayer networks reveals versatile nodes. Nature Communications, 6(1), 1-6.
- **DOI**: https://doi.org/10.1038/ncomms7868
- **Description**: Centrality measures adapted for multilayer networks considering inter-layer connections.

## Network Statistics

### Power-Law Fitting
- **Implementation**: `py3plex.algorithms.statistics.powerlaw`
- **Citation**: Clauset, A., Shalizi, C. R., & Newman, M. E. (2009). Power-law distributions in empirical data. SIAM Review, 51(4), 661-703.
- **DOI**: https://doi.org/10.1137/070710111
- **Description**: Statistical methods for testing and fitting power-law distributions to degree sequences.

### Multilayer Network Statistics
- **Implementation**: `py3plex.algorithms.statistics.multilayer_statistics`
- **Citation**: Bianconi, G. (2018). Multilayer networks: structure and function. Oxford University Press.
- **ISBN**: 9780198753919
- **Description**: Comprehensive statistical measures for characterizing multilayer network structure.

## Network Decomposition

### HIN Mining and Decomposition
- **Implementation**: `py3plex.core.HINMINE`
- **Citation**: Kralj, J., Robnik-Šikonja, M., & Lavrač, N. (2018). HINMINE: Heterogeneous information network mining with information retrieval heuristics. Journal of Intelligent Information Systems, 50(1), 29-61.
- **DOI**: https://doi.org/10.1007/s10844-017-0444-9
- **Description**: Decomposition of heterogeneous information networks using meta-paths and information retrieval.

## Benchmark Generators

### Multilayer Lancichinetti-Fortunato-Radicchi (mLFR)
- **Implementation**: `py3plex.algorithms.community_detection.multilayer_benchmark`
- **Citation**: Lancichinetti, A., & Fortunato, S. (2009). Benchmarks for testing community detection algorithms on directed and weighted graphs with overlapping communities. Physical Review E, 80(1), 016118.
- **DOI**: https://doi.org/10.1103/PhysRevE.80.016118
- **Description**: Synthetic benchmark generator for testing community detection algorithms with ground truth.

## Visualization Algorithms

### Force-Directed Layout (ForceAtlas2)
- **Implementation**: `py3plex.visualization.fa2`
- **Citation**: Jacomy, M., Venturini, T., Heymann, S., & Bastian, M. (2014). ForceAtlas2, a continuous graph layout algorithm for handy network visualization designed for the Gephi software. PloS one, 9(6), e98679.
- **DOI**: https://doi.org/10.1371/journal.pone.0098679
- **Description**: Scalable force-directed layout algorithm optimized for network visualization.

### Multilayer Network Visualization
- **Implementation**: `py3plex.visualization.multilayer`
- **Citation**: De Domenico, M., Porter, M. A., & Arenas, A. (2015). MuxViz: a tool for multilayer analysis and visualization of networks. Journal of Complex Networks, 3(2), 159-176.
- **DOI**: https://doi.org/10.1093/comnet/cnu038
- **Description**: Diagonal projection and other visualization techniques for multilayer networks.

## Statistical Testing

### Bayesian Tests
- **Implementation**: `py3plex.algorithms.statistics.bayesiantests`
- **Citation**: Benavoli, A., Corani, G., & Mangili, F. (2016). Should we really use post-hoc tests based on mean-ranks?. The Journal of Machine Learning Research, 17(1), 152-161.
- **URL**: http://www.jmlr.org/papers/v17/benavoli16a.html
- **Description**: Bayesian statistical tests for comparing network properties and algorithm performance.

## Usage in Publications

When using py3plex in your research, please cite:

```bibtex
@misc{py3plex,
  author = {Škrlj, Blaž},
  title = {Py3plex: A Python library for multilayer network analysis},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/SkBlaz/py3plex}},
  version = {0.95a}
}
```

And cite the specific algorithms you use from the list above.

## Contributing Citations

If you implement a new algorithm in py3plex, please:

1. Add the citation to this file
2. Include the citation in the function/class docstring
3. Update the documentation with a link to the original paper
4. Add a note in CHANGELOG.md

For questions about citations or to report missing references, please open an issue on GitHub.
