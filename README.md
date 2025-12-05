
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
![Lines of Code](https://img.shields.io/badge/lines-100.7K-blue)

*Multilayer networks* are complex networks with additional information assigned to nodes or edges (or both). This library includes
some of the state-of-the-art algorithms for decomposition, visualization and analysis of such networks.

**Key Features:**
* SQL-like DSL for intuitive network queries
* Multilayer network visualization and analysis
* Community detection and centrality measures
* Network decomposition and embeddings

![Py3plex Visualization Showcase](example_images/py3plex_showcase.png)

## Getting Started

* **Documentation:** [https://skblaz.github.io/py3plex/](https://skblaz.github.io/py3plex/)
* **PDF Documentation:** [py3plex_documentation.pdf](docs/py3plex_documentation.pdf)
* **Examples:** [examples/](examples/) - 50+ example scripts demonstrating usage

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
