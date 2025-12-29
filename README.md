
<img src="https://github.com/user-attachments/assets/47e16a25-cd58-41eb-9ccd-b40191758d91" alt="py3plex logo" width="400">

[![Tests](https://github.com/SkBlaz/py3plex/actions/workflows/tests.yml/badge.svg)](https://github.com/SkBlaz/py3plex/actions/workflows/tests.yml)
[![Examples](https://github.com/SkBlaz/py3plex/actions/workflows/examples.yml/badge.svg)](https://github.com/SkBlaz/py3plex/actions/workflows/examples.yml)
[![Tutorial](https://github.com/SkBlaz/py3plex/actions/workflows/tutorial-validation.yml/badge.svg)](https://github.com/SkBlaz/py3plex/actions/workflows/tutorial-validation.yml)
[![Code Quality](https://github.com/SkBlaz/py3plex/actions/workflows/code-quality.yml/badge.svg)](https://github.com/SkBlaz/py3plex/actions/workflows/code-quality.yml)
[![Benchmarks](https://github.com/SkBlaz/py3plex/actions/workflows/benchmarks.yml/badge.svg)](https://github.com/SkBlaz/py3plex/actions/workflows/benchmarks.yml)
[![Documentation](https://github.com/SkBlaz/py3plex/actions/workflows/doc-coverage.yml/badge.svg)](https://github.com/SkBlaz/py3plex/actions/workflows/doc-coverage.yml)
[![Formal Verification](https://github.com/SkBlaz/py3plex/actions/workflows/verify.yml/badge.svg)](https://github.com/SkBlaz/py3plex/actions/workflows/verify.yml)
[![Fuzzing](https://github.com/SkBlaz/py3plex/actions/workflows/fuzzing.yml/badge.svg)](https://github.com/SkBlaz/py3plex/actions/workflows/fuzzing.yml)
[![PyPI version](https://img.shields.io/pypi/v/py3plex.svg)](https://pypi.org/project/py3plex/)
![CLI Tool](https://img.shields.io/badge/CLI%20Tool-Available-brightgreen)
![Docker](https://img.shields.io/badge/Docker-Available-blue)
![Lines of Code](https://img.shields.io/badge/lines-129.2K-blue)

*Multilayer networks* are complex networks with additional information assigned to nodes or edges (or both). This library includes
some of the state-of-the-art algorithms for decomposition, visualization and analysis of such networks.

**Key Features:**
* SQL-like DSL for intuitive network queries with smart defaults
* Multilayer network visualization and analysis
* Community detection and centrality measures
* Network decomposition and embeddings


```python
from py3plex.core import datasets
from py3plex.dsl import Q, UQ
from py3plex.algorithms.community_detection import multilayer_louvain

# 1. Load a built-in multilayer biological network (~500 nodes, 4 layers)
network = datasets.fetch_multilayer("human_ppi_gene_disease_drug")

# 2. Run multilayer community detection
partition_vector, Q_modularity = multilayer_louvain(network, gamma=1.2, random_state=42)
network.assign_partition(partition_vector)

# 3. Find master regulator candidates with uncertainty quantification
master_regulators = (
    Q.nodes()
     .node_type("gene")                        # Filter by node type
     .where(degree__gt=3)                      # Remove peripheral genes
     .uq(method="perturbation", n_samples=100, ci=0.95, seed=42)  # Quantify confidence
     .per_layer()                              # Group by layer
        .compute("degree_centrality", "betweenness_centrality")
        .top_k(20, "betweenness_centrality__mean")  # Top 20 per layer by mean
     .end_grouping()
     .coverage(mode="at_least", k=2)           # Keep genes that are hubs in ≥2 layers
     .mutate(                                  # Create derived influence score
         influence_score=lambda row: (
             row.get("degree_centrality__mean", 0) * 0.4 +
             row.get("betweenness_centrality__mean", 0) * 0.6
         )
     )
     .sort(by="influence_score", descending=True)
     .limit(20)                                # Final top 20 candidates
     .execute(network)
)

df = master_regulators.to_pandas(expand_uncertainty=True)
print(df[["id", "layer", "betweenness_centrality", "betweenness_centrality_std", 
          "betweenness_centrality_ci95_low", "betweenness_centrality_ci95_high",
          "influence_score"]].head(10))
```

Emits:
```
Found 287 communities, modularity = 0.649
    id  layer  betweenness_centrality  betweenness_centrality_std  betweenness_centrality_ci95_low  betweenness_centrality_ci95_high  influence_score
0  252      0                0.025961                    0.002134                         0.021820                          0.030102         0.015577
1   91      0                0.024918                    0.002051                         0.020902                          0.028934         0.014951
2  419      0                0.024184                    0.001987                         0.020298                          0.028070         0.014510
...
```

**Note:** The `.coverage(mode="at_least", k=2)` operator filters nodes to keep only those that appear in the top-20 of at least 2 layers, ensuring we find *robust* master regulators that are consistently important across the multilayer structure.

![Py3plex Visualization Showcase](example_images/py3plex_showcase.png)

## Getting Started

* **Documentation:** [https://skblaz.github.io/py3plex/](https://skblaz.github.io/py3plex/)
* **Technical Book (PDF):** [Practical Multilayer Network Analysis with Py3plex](docs/py3plex_book.pdf) - Complete handbook (106 pages)
* **Examples:** [examples/](examples/) - 50+ example scripts demonstrating usage

## License

Py3plex is released under the [MIT License](LICENSE).

**Note on licensing:** Prior to version 1.0, the project was distributed under the BSD-3-Clause license. Starting with version 1.0, the license was changed to MIT to better align with the broader Python scientific ecosystem and simplify contribution and reuse. Both licenses are permissive and OSI-approved.

# Citations
```
@Article{Skrlj2019,
author={Skrlj, Blaz
and Kralj, Jan
and Lavrac, Nada},
title={Py3plex toolkit for visualization and analysis of multilayer networks},
journal={Applied Network Science},
year={2019},
volume={4},
number={1},
pages={94},
abstract={Complex networks are used as means for representing multimodal, real-life systems. With increasing amounts of data that lead to large multilayer networks consisting of different node and edge types, that can also be subject to temporal change, there is an increasing need for versatile visualization and analysis software. This work presents a lightweight Python library, Py3plex, which focuses on the visualization and analysis of multilayer networks. The library implements a set of simple graphical primitives supporting intra- as well as inter-layer visualization. It also supports many common operations on multilayer networks, such as aggregation, slicing, indexing, traversal, and more. The paper also focuses on how node embeddings can be used to speed up contemporary (multilayer) layout computation. The library's functionality is showcased on both real and synthetic networks.},
issn={2364-8228},
doi={10.1007/s41109-019-0203-7},
url={https://doi.org/10.1007/s41109-019-0203-7}
}
```
and
```
@InProceedings{10.1007/978-3-030-05411-3_60,
author="{\v{S}}krlj, Bla{\v{z}}
and Kralj, Jan
and Lavra{\v{c}}, Nada",
editor="Aiello, Luca Maria
and Cherifi, Chantal
and Cherifi, Hocine
and Lambiotte, Renaud
and Li{\'o}, Pietro
and Rocha, Luis M.",
title="Py3plex: A Library for Scalable Multilayer Network Analysis and Visualization",
booktitle="Complex Networks and Their Applications VII",
year="2019",
publisher="Springer International Publishing",
address="Cham",
pages="757--768",
abstract="Real-life systems are commonly represented as networks of interacting entities. While homogeneous networks consist of nodes of a single node type, multilayer networks are characterized by multiple types of nodes or edges, all present in the same system. Analysis and visualization of such networks represent a challenge for real-life complex network applications. The presented Py3plex Python-based library facilitates the exploration and visualization of multilayer networks. The library includes a diagonal projection-based network visualization, developed specifically for large networks with multiple node (and edge) types. The library also includes state-of-the-art methods for network decomposition and statistical analysis. The Py3plex functionality is showcased on real-world multilayer networks from the domains of biology and on synthetic networks.",
isbn="978-3-030-05411-3"
}
```
