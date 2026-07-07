---
title: 'Py3plex: A Python library for multilayer and heterogeneous network analysis and visualization' 

tags:  
- Python
- network science
- multilayer networks
- heterogeneous networks
- graph embedding
- visualization

authors:
  - name: Blaž Škrlj
    orcid: 0000-0002-9916-8756
    equal-contrib: true
    affiliation: 1
  - name: Boshko Koloski
    equal-contrib: true
    affiliation: 1
  - name: Evgenija Popchanovska
    equal-contrib: true
    affiliation: 2

affiliations: 
- index: 1
   name: Jožef Stefan Institute, Ljubljana, Slovenia
- index: 2
   name: Faculty of Computer Science and Engineering, Skopje, North Macedonia
date: 25 May 2026
bibliography: paper.bib
---

# Summary

Multilayer networks are a powerful abstraction for modeling complex systems in which entities (nodes) are connected through multiple types of relationships, organized into distinct layers. Instead of representing all interactions in a single network, this approach preserves the heterogeneity of connections and enables more accurate analysis of system structure and dynamics [@kivela2014; @boccaletti2014].

**Py3plex** is a Python library created for the analysis and visualization of multilayer and multiplex networks. While traditional network tools typically "flatten" complex data into simple and single-layer graphs, Py3plex preserves the distinct types of relationships that exist in real-world multilayer systems. This library is helpful for users working with datasets where entities are connected through multiple channels, such as social media users interacting across different platforms, biological entities linked by various chemical pathways or evolving networks.

# Statement of Need

There is a gap for interpreting multilayer graphs in existing software because most established libraries, like NetworkX [@networkx] and igraph [@igraph], are designed primarily for single-layer graphs. These tools are useful, but they often require researchers to "flatten" multidimensional data into a single layer. This removes important layer-specific information and can produce inaccurate results for multilayer properties.

**Py3plex** addresses this problem by providing a framework for the analysis and visualization of multiplex, heterogeneous and temporal networks. It is designed for researchers in social science, bioinformatics and physics who need to maintain the distinction between relationship types (layers) while executing end-to-end analytical pipelines.

Py3plex provides practical advantages for working with multilayer networks:

- **Native multilayer abstraction.** Nodes are represented as node-layer pairs, distinguishing a node in one layer from the same node in another. This enables precise inter-layer connections and supra-adjacency operations.
- **Declarative querying (DSL).** A SQL-inspired domain-specific language allows users to query complex multilayer structures with readable commands (e.g., `SELECT nodes WHERE layer="social" AND degree > 5`), reducing long and repetitive code and improving reproducibility.
- **Algorithmic breadth.** The library includes multilayer algorithms such as Louvain community detection, PageRank versatility, Node2Vec and DeepWalk for network embeddings, SIR/SIS models for diffusion processes, all operating natively without flattening the network.
- **Publication-ready visualization.** Py3plex supports multilayer layouts for networks with over 1,000 nodes, preserving layer separation and clarity.

Py3plex uses high-performance I/O like Apache Arrow and works with NetworkX, enabling scalable workflows.

# State of the Field

The following section describes the comparison of Py3plex with other ecosystems for network analysis.

| Ecosystem                              | Overlap with Py3plex 2.0                                                                                 | Py3plex 2.0 positioning                                                                                                                                                       |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| pymnet [@pymnet]                       | Formal multilayer data structures, multilayer metrics, transformations, random models, and visualization | py3plex 2.0 extends beyond representation and metrics toward workflow-oriented multilayer analysis with DSL queries, uncertainty-aware summaries, and reproducible execution. |
| MultiNetX [@multinex]                  | Python-native multilayer graph manipulation, supra-adjacency analysis, and visualization                 | py3plex 2.0 provides a broader end-to-end environment for multilayer workflows, temporal analysis, and structured analytical pipelines.                                       |
| muxViz [@muxviz]                       | Multilayer visualization, centrality analysis, community detection, and structural analysis              | py3plex 2.0 emphasizes Python-native, scriptable, and reproducible multilayer workflows rather than desktop-oriented visual analytics.                                        |
| tnetwork [@tnetwork]                   | Temporal slicing, dynamic graphs, and evolving-community analysis                                        | py3plex 2.0 integrates temporal analysis into a larger multilayer workflow and query ecosystem.                                                                               |
| DyNetx [@dynetx]                       | Time-varying graph representation and temporal slicing                                                   | py3plex 2.0 adds multilayer semantics, declarative analysis, integrated dynamics, and reusable workflows.                                                                     |
| Reticula [@reticula]                   | Temporal-network analysis, reachability, randomized models, and dynamical processes                      | py3plex 2.0 prioritizes multilayer workflow integration, analyst-oriented abstractions, and reproducible experimentation.                                                     |
| Raphtory [@raphtory]                   | Temporal graph querying, motifs, and deployment-oriented graph analysis                                  | py3plex 2.0 focuses on multilayer scientific workflows with DSL support, uncertainty analysis, and reproducible research pipelines.                                           |
| NetworkX [@networkx]                   | Core graph algorithms, graph data structures, and Python graph workflows                                 | py3plex 2.0 extends the general graph ecosystem with multilayer semantics, layer algebra, temporal workflows, and structured outputs.                                         |
| igraph [@igraph]                       | Centrality analysis, community detection, graph transformations, and scalable graph analytics            | py3plex 2.0 differentiates through multilayer-specific workflows, query abstractions, and reproducible analytical interfaces.                                                 |
| graph-tool [@graph-tool]               | Large-scale graph statistics, inference, and performance-sensitive analysis                              | py3plex 2.0 emphasizes multilayer expressiveness, querying, uncertainty handling, and workflow integration rather than performance optimization alone.                        |
| NDlib [@ndlib]                         | Diffusion processes, epidemic simulations, and network dynamics                                          | py3plex 2.0 embeds dynamics inside multilayer, temporal, and queryable analytical workflows.                                                                                  |
| PyTorch Geometric [@pytorch-geometric] | Graph embeddings, graph representation learning, and graph ML preparation                                | py3plex 2.0 focuses on multilayer querying, interpretation, summarization, and scientific network analysis rather than neural model training.                                 |
| DGL [@dgl]                             | Heterogeneous graph processing and scalable graph machine-learning pipelines                             | py3plex 2.0 addresses multilayer network science workflows, temporal analysis, and uncertainty-aware analytics.                                                               |
| Neo4j / Cypher [@neo4jcypher]          | Declarative graph querying and pattern-based graph access                                                | py3plex 2.0 provides an in-memory scientific DSL tailored to multilayer analysis, metrics, uncertainty estimation, and reproducible workflows.                                |

# Software Design

The primary design goal of Py3plex is to provide a scalable framework for multilayer network analysis while maintaining compatibility with the NetworkX algorithms. Py3plex utilizes a **node-layer pair representation**, where each logical entity is represented as a unique tuple: `(node_id, layer_id)`.

Internally, Py3plex stores all nodes and edges in a single NetworkX MultiGraph (for undirected) or MultiDiGraph (for directed networks). The multilayer structure is encoded through the node representation. This architecture allows a node to be central in one context while remaining peripheral in another.

The library distinguishes between two primary network types:

- **Multilayer:** Designed for heterogeneous systems where node sets vary by layer (e.g. author-paper-venue networks). Inter-layer edges must be explicitly defined.
- **Multiplex:** A special case where all layers share the same node set. Upon initialization, the software automatically generates coupling edges (identity links that connect a node to its counterparts across all layers).

For spectral analysis and linear algebra operations, Py3plex implements a supra-adjacency matrix `S`. This block-matrix representation stacks intra-layer adjacency blocks along the diagonal and inter-layer coupling blocks in the off-diagonal positions.

# Research impact statement

Usage statistics for Py3plex are publicly available on PyPI Stats [@pypistats]. According to the official PyPI download log (Google BigQuery pypi.file_downloads dataset), py3plex has been downloaded a total of 205758 times since its release (as of 1st July).

# Availability

Py3plex is distributed under the MIT licence [@mitlicense]. The source code, documentation and usage examples are publicly available on GitHub [@py3plexgithub]. The package is distributed through PyPI [@py3plexpypi] and can be installed using `pip install py3plex`.

# AI usage disclosure

Large language models (Gemini and ChatGPT) helped draft documentation and perform grammar and spelling checks. All content was subsequently reviewed and edited by the author, who takes full responsibility for the published article. We used GitHub Copilot to assist with code review and generate code snippets.

# Acknowledgements

TBD

# References
