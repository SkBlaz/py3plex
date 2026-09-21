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
date: 22 September 2026
bibliography: paper.bib
---

# Summary

Multilayer networks are a powerful abstraction for modeling complex systems in which entities (nodes) are connected through multiple types of relationships, organized into distinct layers. This preserves the heterogeneity of connections and supports more accurate analysis of system structure and dynamics than a single flattened network [@kivela2014; @boccaletti2014].

**Py3plex** is a Python library for the analysis and visualization of multilayer and multiplex networks. It preserves the distinct relationship types found in real-world multilayer systems, rather than collapsing them into a single-layer graph. The library supports users working with data where entities are connected through multiple channels, such as social media users active across platforms, biological entities linked by different chemical pathways, or networks that evolve over time.

# Statement of Need

There is a gap in how existing software handles multilayer graphs. Most established libraries, such as NetworkX [@networkx] and igraph [@igraph], can encode layer information manually, but they do not provide multilayer semantics as a first-class abstraction. Users must therefore manage layer identity and multilayer interpretation themselves, and many standard algorithms operate on a monoplex representation, which removes layer-specific information and can produce inaccurate results for multilayer properties. Dedicated multilayer libraries close part of that gap, but they generally leave uncertainty, provenance and cross-run reproducibility to be assembled by hand - which is where multilayer conclusions most often fail.

**Py3plex** addresses this problem by providing a framework for the analysis and visualization of multiplex, heterogeneous and temporal networks. It is designed for researchers in social science, bioinformatics and physics who need to maintain the distinction between relationship types (layers) while executing end-to-end analytical pipelines.

Py3plex provides four practical advantages for working with multilayer networks:

- **Native multilayer representation and algorithms.** Nodes are represented as node-layer pairs, so a node in one layer is distinct from the same node in another, enabling precise inter-layer connections and supra-adjacency operations. Py3plex provides native multilayer operators where implemented, and makes projection- or restriction-based execution paths explicit when a delegated routine needs one. Coverage includes Louvain and multilayer-modularity community detection, multilayer centralities, random walk with restart, layer entanglement, network embeddings, and SIR/SIS diffusion models.
- **Declarative, auditable querying (DSL).** A SQL-inspired domain-specific language lets users query multilayer structures with readable commands (e.g., `SELECT nodes WHERE layer="social" AND degree > 5`). Queries carry static diagnostics, inspectable explain plans and an AST hash, so a reviewer can verify the exact query behind a reported claim and detect workflow drift between revisions.
- **Uncertainty-aware, reproducible analysis.** Py3plex provides first-class uncertainty representations for uncertainty-enabled statistics, drawing on delta, Gaussian, bootstrap, empirical and interval models, with provenance carried through supported workflows. Uncertainty propagates through arithmetic and can be used inside queries, so rank stability is testable rather than assumed. Experiment records and meta-analysis support conclusions drawn across repeated networks, and a Model Context Protocol server exposes the typed query API to AI coding assistants for recorded, replayable analysis.
- **Representation learning and publication-ready visualization.** Embedding models take (node, layer) state nodes as their canonical target, covering supra-Node2Vec, supra-spectral, supra-NetMF, MNE, MELL and an experimental multilayer GNN, feeding into scikit-learn pipelines for node classification, clustering and link prediction. Diagonal-projection layouts preserve layer separation and clarity at scales where comparable multilayer tools become impractical, with the original benchmark rendering a network of 4,000 nodes and 18,600 edges.

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

Each of these tools could, in principle, absorb part of what Py3plex offers: NetworkX or igraph could add layer-aware data structures, and pymnet or MultiNetX could add a query layer or uncertainty estimation. Py3plex exists as a separate package because these capabilities are most useful together, not apart - a query language is not fully auditable without provenance, provenance is not informative without uncertainty estimates, and uncertainty estimates are not actionable without native multilayer semantics to attach them to. Py3plex therefore contributes one coherent execution model, rather than a set of features better contributed piecemeal to existing packages.

# Software Design

The primary design goal of Py3plex is to provide a scalable framework for multilayer network analysis while maintaining compatibility with the NetworkX algorithms. The project prioritises three properties, in order: a consistent multilayer representation, interoperability with established graph tooling, and explicit caveats around approximations and feature maturity.

Py3plex utilizes a node-layer pair representation, where each logical entity is a unique tuple `(node_id, layer_id)`. Internally, Py3plex stores all nodes and edges in a single NetworkX MultiGraph (for undirected) or MultiDiGraph (for directed networks), and the multilayer structure is encoded through the node representation. The library therefore operates on attribute-rich, list-based representations rather than dense tensor structures, with computationally expensive operations vectorised over sparse indices using NumPy. This lets a node be central in one context while remaining peripheral in another.

The library distinguishes between two primary network types:

- **Multilayer:** Designed for heterogeneous systems where node sets vary by layer (e.g. author-paper-venue networks). Inter-layer edges must be explicitly defined.
- **Multiplex:** A special case where all layers share the same node set. Upon initialization, the software automatically generates coupling edges (identity links that connect a node to its counterparts across all layers).

Coupling edges remain tagged distinctly from domain edges throughout, because conflating the two makes transfer intensity read as domain connectivity and distorts both centrality and community interpretation.

For spectral analysis and linear algebra operations, Py3plex materialises a supra-adjacency matrix `S`. This block-matrix representation stacks intra-layer adjacency blocks along the diagonal and inter-layer coupling blocks in the off-diagonal positions. Algebraic path and closure computations are handled by `py3plex.algebra` and `py3plex.semiring`, which express reachability and shortest-path variants as semiring reductions rather than as separately special-cased algorithms.

Building on NetworkX-compatible objects provides immediate access to mature single-layer algorithms and the surrounding ecosystem, but some multilayer operations necessarily pass through a reduction - a layer restriction or projection to a monoplex graph - before a delegated routine runs, with results then mapped back to multilayer identifiers. Such a path can be computationally practical but is analytically different from a native multilayer operator. Py3plex therefore separates what a statistic means (theory) from how it is computed or delegated (implementation), and reports the execution path so that a native multilayer estimate is never presented as interchangeable with a projection-based baseline.

The public interface is organised around this separation, with modules for the core network object, DSL and typed query programs, algorithms and wrappers, multilayer embeddings and machine learning, experiment tracking and meta-analysis, and scalable out-of-core workflows. Supported I/O includes edge lists, CSV, JSON, GraphML/GML and Arrow/Parquet, with export to Gephi and Cytoscape; visualization adds per-layer force-directed layouts and inter-layer edge rendering.

# Research impact statement

py3plex is one of only four libraries - alongside Multinet, MuxViz and Pymnet - selected for full operator-coverage and scalability benchmarking in a recent survey of multilayer network engineering @Panayiotou2024, and the two py3plex papers have together been cited by more than 30 distinct publications (OpenAlex, September 2026).

That uptake reaches well beyond network science itself. Within multilayer methods and visualisation, @SkrljRenoust2019 builds directly on the library to introduce entanglement metrics for multiplex, multilayer and temporal networks. In biology and biomedicine, it was used with plant pathologists to render gene communities in a temporal model of grapevine infection by 'Candidatus Phytoplasma solani' @SkrljEtAl2021. In computer science and optimisation, an independent group made it part of the analysis pipeline for multi-layer local optima networks in fitness-landscape studies of local-search algorithms @MartinsEtAl2020 - a use case the toolkit never advertised. In engineering, it serves as the modelling backbone for representing material and energy flows between petrochemical plants as a multiplex graph, from which cluster integration is read off the network properties @TanEtAl2024. In urban studies it is cited as the reference tooling for the multilayer analysis stage of an indicator framework for high-frequency cities @SenousiEtAl2021, and in computational linguistics it supported the analysis and visualisation of InfoMap community structure in word-token networks derived from a nine-language parallel corpus @SkrljPollak2019.

# Availability

Py3plex is distributed under the MIT licence [@mitlicense]. The source code, documentation and usage examples are publicly available on GitHub [@py3plexgithub]. The package is distributed through PyPI [@py3plexpypi] and can be installed using `pip install py3plex`.

# AI usage disclosure

Large language models assisted with parts of this manuscript and codebase. Google Gemini, OpenAI ChatGPT and Anthropic Claude (versions in use at the time of writing) were used to draft and edit documentation text and to check grammar and spelling. GitHub Copilot and Claude Code was used during development to assist with code review and to generate candidate code snippets and tests. In all cases the tools were used for drafting and suggestion only, and every output was treated as a draft requiring verification. Every AI-assisted passage of text and every AI-suggested code change was reviewed, edited and validated by the authors before inclusion. The authors made all core design decisions independently of any AI tool, and take full responsibility for the published article and released software.

# Acknowledgements

This work received no dedicated external funding. The authors thank the py3plex user and contributor community for feedback that has helped improve the library.

# References
