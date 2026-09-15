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
  - name: Evgenija Popchanovska
    equal-contrib: true
    affiliation: 2
  - name: Boshko Koloski
    orcid: 0000-0002-7330-0579
    equal-contrib: true
    affiliation: 1
  - name: Yana Melnik
    equal-contrib: true
    affiliation: 4
  - name: Benjamin Renoust
    equal-contrib: true
    affiliation: 3
  - name: Blaž Škrlj
    orcid: 0000-0002-9916-8756
    equal-contrib: true
    affiliation: 1

affiliations: 
- index: 1
   name: Jožef Stefan Institute, Ljubljana, Slovenia
- index: 2
   name: Faculty of Computer Science and Engineering, Skopje, North Macedonia
- index: 3
   name: Institute for Datability Science Osaka University, Japan
- index: 4
   name: Epitech - L'école de l'excellence informatique
date: 25 May 2026
bibliography: paper.bib
---

# Summary

Multilayer networks are a powerful abstraction for modeling complex systems in which entities (nodes) are connected through multiple types of relationships, organized into distinct layers. Instead of representing all interactions in a single network, this approach preserves the heterogeneity of connections and enables more accurate analysis of system structure and dynamics [@kivela2014; @boccaletti2014].

**Py3plex** is a Python library created for the analysis and visualization of multilayer and multiplex networks. While traditional network tools typically "flatten" complex data into simple and single-layer graphs, Py3plex preserves the distinct types of relationships that exist in real-world multilayer systems. This library is helpful for users working with datasets where entities are connected through multiple channels, such as social media users interacting across different platforms, biological entities linked by various chemical pathways or evolving networks. 

# Statement of Need

There is a gap for interpreting multilayer graphs in existing software because most established libraries, like NetworkX [@networkx] and igraph [@igraph], are designed primarily for single-layer graphs. These tools are useful, but they often require researchers to "flatten" multidimensional data into a single layer. This removes important layer-specific information and can produce inaccurate results for multilayer properties. Dedicated multilayer libraries close part of that gap, but they generally leave uncertainty, provenance and cross-run reproducibility to be assembled by hand - which is where multilayer conclusions most often fail.

**Py3plex** addresses this problem by providing a framework for the analysis and visualization of multiplex, heterogeneous and temporal networks. It is designed for researchers in social science, bioinformatics and physics who need to maintain the distinction between relationship types (layers) while executing end-to-end analytical pipelines.

Py3plex provides practical advantages for working with multilayer networks:

- **Native multilayer abstraction.** Nodes are represented as node-layer pairs, distinguishing a node in one layer from the same node in another. This enables precise inter-layer connections and supra-adjacency operations.
- **Declarative, auditable querying (DSL).** A SQL-inspired domain-specific language allows users to query complex multilayer structures with readable commands (e.g., `SELECT nodes WHERE layer="social" AND degree > 5`), reducing long and repetitive code. Queries additionally carry static diagnostics, inspectable explain plans and an AST hash, so a reviewer can verify the exact query structure behind a reported claim and detect silent workflow drift between revisions.
- **Algorithmic breadth.** The library includes multilayer algorithms such as Louvain and multilayer-modularity community detection, PageRank versatility and multilayer centralities, random walk with restart, layer entanglement, network embeddings, and SIR/SIS models for diffusion processes, all operating natively without flattening the network. Path and reachability queries are expressed as semiring reductions rather than hard-coded shortest-path routines.
- **Uncertainty-first statistics.** Every statistic is returned as a value together with an explicit uncertainty model and its provenance, with delta, Gaussian, bootstrap, empirical and interval models available. Uncertainty propagates through arithmetic and can be used inside queries, so rank stability is testable rather than assumed.
- **Multilayer representation learning.** Embedding models take (node, layer) state nodes as their canonical target, covering supra-Node2Vec, supra-spectral, supra-NetMF, MNE, MELL and an experimental multilayer GNN, and feed directly into scikit-learn pipelines for node classification, clustering and link prediction. Py3plex sits upstream of dedicated graph deep-learning frameworks such as PyTorch Geometric and DGL, preparing and querying multilayer data rather than replacing them.
- **Publication-ready visualization.** Diagonal-projection layouts preserve layer separation and clarity at scales where comparable multilayer tools become impractical, with the original benchmark rendering a network of 4,000 nodes and 18,600 edges.
- **Reproducible and agent-accessible workflows.** High-performance I/O (Apache Arrow, Parquet) and converters for NetworkX, igraph and SciPy sparse matrices enable scalable, interoperable pipelines. Experiment records and fixed- and random-effects meta-analysis support conclusions drawn across repeated networks, and a Model Context Protocol server exposes the typed query API to AI coding assistants, so exploratory multilayer analysis can be driven conversationally while remaining a recorded, replayable program.

Py3plex uses high-performance I/O like Apache Arrow and works with NetworkX, enabling scalable workflows.

# State of the Field

The following section describes the comparison of Py3plex with other ecosystems for network analysis.

| Ecosystem                              | Overlap with Py3plex 2.0                                                                                 | Py3plex 2.0 positioning                                                                                                                                                       |
|----------------------------------------| -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
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
| Tulip [@Tulip]                         | Full-range generic graph visualization and analytics framework, with python support                      | py3plex 2.0 provides multilayer-native representations and metrics toward workflow-oriented analysis with DSL queries, uncertainty-aware summaries, and reproducible execution rather than generic graph visual analytics|

# Software Design

The primary design goal of Py3plex is to provide a scalable framework for multilayer network analysis while maintaining compatibility with the NetworkX algorithms. The project prioritises three properties, in order: a consistent multilayer representation, interoperability with established graph tooling, and explicit caveats around approximations and feature maturity.

Py3plex utilizes a node-layer pair representation, where each logical entity is represented as a unique tuple `(node_id, layer_id)`. Internally, Py3plex stores all nodes and edges in a single NetworkX MultiGraph (for undirected) or MultiDiGraph (for directed networks), and the multilayer structure is encoded through the node representation. The library therefore operates on attribute-rich, list-based representations rather than dense tensor structures, with computationally expensive operations vectorised over sparse indices using NumPy. This architecture allows a node to be central in one context while remaining peripheral in another.

The library distinguishes between two primary network types:

- **Multilayer:** Designed for heterogeneous systems where node sets vary by layer (e.g. author-paper-venue networks). Inter-layer edges must be explicitly defined.
- **Multiplex:** A special case where all layers share the same node set. Upon initialization, the software automatically generates coupling edges (identity links that connect a node to its counterparts across all layers).

Coupling edges remain tagged distinctly from domain edges throughout, because conflating the two makes transfer intensity read as domain connectivity and distorts both centrality and community interpretation.

For spectral analysis and linear algebra operations, Py3plex materialises a supra-adjacency matrix `S`. This block-matrix representation stacks intra-layer adjacency blocks along the diagonal and inter-layer coupling blocks in the off-diagonal positions. Algebraic path and closure computations are handled by `py3plex.algebra` and `py3plex.semiring`, which express reachability and shortest-path variants as semiring reductions rather than as separately special-cased algorithms.

Building on NetworkX-compatible objects provides immediate access to mature single-layer algorithms and the surrounding ecosystem, but some multilayer operations necessarily pass through a reduction-a layer restriction or projection to a monoplex graph-before a delegated routine runs, with results then mapped back to multilayer identifiers. Such a path can be computationally practical but is analytically different from a native multilayer operator. Py3plex therefore separates what a statistic means (theory) from how it is computed or delegated (implementation), and reports the execution path so that a native multilayer estimate is never presented as interchangeable with a projection-based baseline.

The public interface is organised around this separation, with modules for the core network object, DSL and typed query programs, algorithms and wrappers, multilayer embeddings and machine learning, experiment tracking and meta-analysis, and scalable out-of-core workflows. Supported I/O includes edge lists, CSV, JSON, GraphML/GML, and Arrow/Parquet, with export to tools such as Gephi and Cytoscape. Visualization includes diagonal-projection layouts, independent per-layer force-directed layouts, inter-layer edge rendering, and embedding-based layouts such as Node2Vec followed by t-SNE.

# Research impact statement

py3plex is one of only four libraries - alongside Multinet, MuxViz and Pymnet - selected for full operator-coverage and scalability benchmarking in a recent survey of multilayer network engineering @Panayiotou2024, and the two py3plex papers have together been cited by more than 30 distinct publications (OpenAlex, September 2026).

That uptake reaches well beyond network science itself. Within multilayer methods and visualisation, @SkrljRenoust2019 builds directly on the library to introduce entanglement metrics for multiplex, multilayer and temporal networks. In biology and biomedicine, it was used in collaboration with plant pathologists to render gene communities in a temporal model of grapevine infection by 'Candidatus Phytoplasma solani' @SkrljEtAl2021. In computer science and optimisation, an independent group made it part of the analysis pipeline for multi-layer local optima networks in fitness-landscape studies of local-search algorithms @MartinsEtAl2020 - a use case the toolkit never advertised. In engineering, it serves as the modelling backbone for representing material and energy flows between petrochemical plants as a multiplex graph, from which cluster integration is read off the network properties @TanEtAl2024. In urban studies it is cited as the reference tooling for the multilayer analysis stage of an indicator framework for high-frequency cities @SenousiEtAl2021, and in computational linguistics it supported the analysis and visualisation of InfoMap community structure in word-token networks derived from a nine-language parallel corpus @SkrljPollak2019.

# Availability

Py3plex is distributed under the MIT licence [@mitlicense]. The source code, documentation and usage examples are publicly available on GitHub [@py3plexgithub]. The package is distributed through PyPI [@py3plexpypi] and can be installed using `pip install py3plex`.

# AI usage disclosure

Large language models (Gemini and ChatGPT) helped draft documentation and perform grammar and spelling checks. All content was subsequently reviewed and edited by the author, who takes full responsibility for the published article. We used GitHub Copilot to assist with code review and generate code snippets.

# Acknowledgements

The authors would like to thank Benjamin Renoust and Yana Melnik for their valuable feedback and contributions to the development of py3plex.

# References