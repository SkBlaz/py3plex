---
title: 'Py3plex 2.0: Declarative Workflows for Multilayer Network Science' 

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
  - name: Yana Melnyk
    equal-contrib: false
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
date: 22 September 2026
bibliography: paper.bib
---

# Summary

Multilayer networks are a powerful abstraction for modeling complex systems in which entities (nodes) are connected through multiple types of relationships, organized into distinct layers. This preserves the heterogeneity of connections and supports more accurate analysis of system structure and dynamics than a single flattened network [@kivela2014; @boccaletti2014].

**Py3plex** is a Python library for the analysis and visualization of multilayer and multiplex networks. It preserves the distinct relationship types found in real-world multilayer systems, rather than collapsing them into a single-layer graph. The library supports researchers studying systems such as social networks, biological interactions, and networks that evolve over time. Earlier publications described its original visualization and analysis capabilities [@skrlj2019toolkit; @skrlj2019conference]. Version 2.0 substantially extends this foundation with a declarative query language, broader algorithm coverage, performance-oriented execution, and a Model Context Protocol (MCP) interface.

# Statement of Need

There is a gap in how existing software handles multilayer graphs. Most established libraries, such as NetworkX [@networkx] and igraph [@igraph], can encode layer information manually, but they do not provide multilayer semantics as a first-class abstraction. Users must therefore manage layer identity and multilayer interpretation themselves, and many standard algorithms operate on a monoplex representation, which removes layer-specific information and can produce inaccurate results for multilayer properties. Dedicated multilayer libraries provide important alternatives, but combining layer-aware queries, uncertainty analysis, and provenance can require additional tooling.

**Py3plex** addresses this problem by providing a framework for the analysis and visualization of multiplex, heterogeneous and temporal networks. It is designed for researchers in social science, bioinformatics and physics who need to maintain the distinction between relationship types (layers) while executing end-to-end analytical pipelines.

Py3plex provides four practical advantages for working with multilayer networks:

- **Native multilayer representation and algorithms.** Nodes are represented as node-layer pairs, so a node in one layer is distinct from the same node in another, enabling precise inter-layer connections and supra-adjacency operations. Py3plex provides native multilayer operators where implemented, and makes projection- or restriction-based execution paths explicit when a delegated routine needs one. Coverage includes Louvain and multilayer-modularity community detection, multilayer centralities, random walk with restart, layer entanglement, network embeddings, and SIR/SIS diffusion models.
- **Declarative, auditable querying (DSL).** A SQL-inspired domain-specific language lets users query multilayer structures with readable commands (e.g., `SELECT nodes WHERE layer="social" AND degree > 5`). Supported workflows offer query diagnostics, explain plans, and provenance to help researchers inspect and reproduce an analysis.
- **Uncertainty-aware, reproducible analysis.** Py3plex provides first-class uncertainty representations for uncertainty-enabled statistics, drawing on delta, Gaussian, bootstrap, empirical and interval models, with provenance carried through supported workflows. Uncertainty propagates through arithmetic and can be used inside queries, so rank stability is testable rather than assumed. Experiment records and meta-analysis support conclusions drawn across repeated networks, and an MCP server exposes query and analysis tools to compatible assistants.
- **Representation learning and publication-ready visualization.** Embedding models take (node, layer) state nodes as their canonical target, covering supra-Node2Vec, supra-spectral, supra-NetMF, MNE, MELL and an experimental multilayer GNN, feeding into scikit-learn pipelines for node classification, clustering and link prediction. Diagonal-projection layouts display layers and inter-layer edges separately. An earlier experiment rendered a network with 4,000 nodes and 18,600 edges, although its authors noted that the resulting visualization was not necessarily useful for interpretation [@skrlj2019toolkit].

# State of the Field

The following section compares Py3plex with the ecosystems it overlaps with most directly.

| Ecosystem | Overlap with Py3plex 2.0 | Py3plex 2.0 positioning |
|-----------|---------------------------|---------------------------|
| pymnet [@pymnet] | Formal multilayer data structures, multilayer metrics, transformations, random models, and visualization | Py3plex extends beyond representation and metrics toward workflow-oriented multilayer analysis, with DSL queries, uncertainty-aware summaries, and reproducible execution. |
| MultiNetX [@multinex] | Python-native multilayer graph manipulation, supra-adjacency analysis, and visualization | Py3plex provides a broader end-to-end environment for multilayer workflows, temporal analysis, and structured analytical pipelines. |
| muxViz [@muxviz] | Multilayer visualization, centrality analysis, community detection, and structural analysis | Py3plex emphasizes Python-native, scriptable, and reproducible multilayer workflows rather than desktop-oriented visual analytics. |
| NetworkX [@networkx] | Core graph algorithms, graph data structures, and Python graph workflows | Py3plex extends the general graph ecosystem with multilayer semantics, layer algebra, temporal workflows, and structured outputs. |
| igraph [@igraph] | Centrality analysis, community detection, graph transformations, and scalable graph analytics | Py3plex differentiates through multilayer-specific workflows, query abstractions, and reproducible analytical interfaces. |
| Tulip [@Tulip] | Full-range generic graph visualization and analytics framework, with Python support | Py3plex focuses on multilayer-native representations and workflow-oriented analysis, with DSL queries, uncertainty-aware summaries, and reproducible execution, rather than generic graph visual analytics. |

Each of these tools could, in principle, absorb part of what Py3plex offers: NetworkX or igraph could add layer-aware data structures, and pymnet or MultiNetX could add a query layer or uncertainty estimation. Py3plex builds on NetworkX and extends an established multilayer library with a shared interface for these workflows. Maintaining this integrated package allows its query, uncertainty, and provenance features to operate on the same node-layer representation; contributing the entire stack to a general graph library or another multilayer project would require adopting its data model and design priorities.

# Software Design

The primary design goal of Py3plex is to provide a scalable framework for multilayer network analysis while maintaining compatibility with the NetworkX algorithms. The project prioritises three properties, in order: a consistent multilayer representation, interoperability with established graph tooling, and explicit caveats around approximations and feature maturity.

Py3plex utilizes a node-layer pair representation, where each logical entity is a unique tuple `(node_id, layer_id)`. Internally, Py3plex stores all nodes and edges in a single NetworkX MultiGraph (for undirected) or MultiDiGraph (for directed networks), and the multilayer structure is encoded through the node representation. This representation supports attributes and interoperability with NetworkX, while avoiding a mandatory dense tensor representation; sparse and vectorized operations are used where implemented. This lets a node be central in one context while remaining peripheral in another.

The library distinguishes between two primary network types:

- **Multilayer:** Designed for heterogeneous systems where node sets vary by layer (e.g. author-paper-venue networks). Inter-layer edges must be explicitly defined.
- **Multiplex:** A special case where all layers share the same node set. For multiplex networks loaded through the network loader, the software can automatically generate coupling edges between replicas of the same node.

Automatically generated coupling edges carry a distinct type tag, helping users distinguish identity links from domain edges when interpreting connectivity.

For spectral analysis and linear algebra operations, Py3plex materialises a supra-adjacency matrix `S`. This block-matrix representation stacks intra-layer adjacency blocks along the diagonal and inter-layer coupling blocks in the off-diagonal positions. Algebraic path and closure computations are handled by `py3plex.algebra` and `py3plex.semiring`, which express reachability and shortest-path variants as semiring reductions rather than as separately special-cased algorithms.

Building on NetworkX-compatible objects provides immediate access to mature single-layer algorithms and the surrounding ecosystem, but some multilayer operations necessarily pass through a reduction - a layer restriction or projection to a monoplex graph - before a delegated routine runs, with results then mapped back to multilayer identifiers. Such a path can be computationally practical but is analytically different from a native multilayer operator. Py3plex therefore separates what a statistic means (theory) from how it is computed or delegated (implementation), and documents execution paths so that users can distinguish native multilayer estimates from projection-based baselines.

The public interface is organised around this separation, with modules for the core network object, DSL and typed query programs, algorithms and wrappers, multilayer embeddings and machine learning, experiment tracking and meta-analysis, and scalable out-of-core workflows. Supported I/O includes edge lists, CSV, JSON, GraphML/GML and Arrow/Parquet, with export to Gephi and Cytoscape; visualization adds per-layer force-directed layouts and inter-layer edge rendering.

# Research impact statement

The original Py3plex toolkit was included in a comparative study of multilayer network engineering that examined operator coverage and scalability across several libraries [@Panayiotou2024]. Its prior use includes visualization of gene communities in a temporal study of grapevine infection [@SkrljEtAl2021] and network analysis and visualization in a comparison of nine languages [@SkrljPollak2019]. These examples concern earlier versions; they establish use of the project but do not by themselves evaluate the new 2.0 features.

# Availability

Py3plex is distributed under the MIT licence [@mitlicense]. The source code, documentation and usage examples are publicly available on GitHub [@py3plexgithub]. The package is distributed through PyPI [@py3plexpypi] and can be installed using `pip install py3plex`.

# AI usage disclosure

The initial code was written by hand. As language models became more capable, OpenAI Codex was used for larger code refactors and for revising this manuscript (GPT-6 for the latter); GitHub Copilot and Anthropic Claude Code also assisted with code review, candidate snippets, and tests. Google Gemini, OpenAI ChatGPT, and Anthropic Claude assisted with documentation drafting and editing and with grammar and spelling checks for the manuscript. The authors need to confirm the model and tool versions used for earlier work before submission. Human authors made the core design decisions and reviewed and edited the manuscript; they reviewed and validated AI-assisted code and text before inclusion and take responsibility for the submitted work.

# Acknowledgements

This work was partly funded by the Slovenian Research Agency under the projects: P2-0103, PR-12394 and GC-0002 (Large Language Models for Digital Humanities). This work was also partially supported by the European Union's Horizon Europe research and innovation program under grant agreement No. 101214398 (ELLIOT). Views and opinions expressed are, however, those of the author(s) only and do not necessarily reflect those of the European Union or the European Commission. Neither the European Union nor the European Commission can be held responsible for them. Furthermore, the authors thank the py3plex user and contributor community for feedback that has helped improve the library.

# References
