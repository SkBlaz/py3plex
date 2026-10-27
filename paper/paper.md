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

Multilayer networks describe systems with several kinds of relationships, such as people connected through different social platforms. Keeping those relationships in separate layers lets researchers study both the individual layers and the connections between them [@kivela2014; @boccaletti2014]. Py3plex is a Python library for analyzing and visualizing these networks.

The original Py3plex publications focused on multilayer network representation, analysis, and visualization [@skrlj2019toolkit; @skrlj2019conference]. Version 2.0 adds a query language, expands the available algorithms, and provides tools for uncertainty analysis and recording how results were produced. It also includes a Model Context Protocol (MCP) server through which compatible assistants can access network analysis tools.

# Statement of Need

Researchers in fields such as social science, biology, and physics often need to compare relationships across layers. A network of people, for example, might contain separate layers for work and friendship. Combining these layers into one graph can hide whether a connection belongs to one setting or both.

General graph libraries such as NetworkX [@networkx] and igraph [@igraph] can store layer labels, but users must manage their interpretation. Dedicated multilayer packages offer data structures and analysis methods, while a researcher may still need to assemble separate tools for selecting layers, assessing uncertainty, and recording an analysis.

Py3plex represents each occurrence of a node in a layer separately and supports edges both within and between layers. Its query language lets researchers select parts of a network and request measures in a single expression. For supported analyses, users can estimate uncertainty, inspect the query plan, and record provenance. The library also includes community detection, centrality measures, diffusion simulations, embeddings, and multilayer visualization.

# State of the Field

Several packages address related needs. NetworkX [@networkx] and igraph [@igraph] provide general graph data structures and algorithms. Pymnet [@pymnet] and MultiNetX [@multinex] provide multilayer representations and operations; pymnet also supports multilayer models with multiple aspects. MuxViz [@muxviz] provides multilayer analysis and visualization in R, while Tulip [@Tulip] offers general graph visualization and analysis with Python support.

Py3plex builds on NetworkX and extends an existing multilayer library rather than introducing another independent graph backend. Its query language, uncertainty tools, and provenance features work with the same node-layer representation as its analysis methods. Contributing the whole interface to NetworkX would require adding multilayer concepts to a general graph library; adopting another dedicated package would require adapting the established Py3plex API and data model. The packages remain complementary: a researcher may prefer pymnet's model support or muxViz's visualization tools for a particular study.

# Software Design

Py3plex represents a node in a layer as a pair `(node_id, layer_id)`. Its core network stores these pairs and their edges in a NetworkX MultiGraph or MultiDiGraph. This choice gives users access to NetworkX data structures and algorithms without requiring a dense tensor for the network. It also means that a node's role can be studied separately in each layer.

The library supports multilayer networks whose node sets differ across layers and multiplex networks in which nodes have counterparts across layers. Inter-layer edges in a general multilayer network are specified by the user. For multiplex networks loaded through the network loader, Py3plex can create coupling edges between replicas of the same node; these generated edges have a distinct type tag.

NetworkX interoperability has a trade-off. Some analyses operate directly on the multilayer representation, whereas others restrict the network to a layer or project it to a single graph before applying a delegated algorithm. These choices can produce results with different meanings, so users need to consider the execution path when interpreting a measure. For matrix-based analysis, Py3plex can also construct a supra-adjacency matrix, with within-layer connections on diagonal blocks and inter-layer connections on off-diagonal blocks. Version 2.0 also includes vectorized layer aggregation and query planning for supported operations.

The query language provides a common way to select layers, filter nodes or edges, and compute measures. Supported queries can include uncertainty estimates and provenance, making it possible to retain information about the choices behind a result. The library also provides temporal network operations, network embeddings, and layouts that display layers and their inter-layer edges. These capabilities extend the analysis and visualization tools described in the original publications.

# Research impact statement

Earlier versions of Py3plex have been used to visualize gene communities in a temporal study of grapevine infection [@SkrljEtAl2021] and to analyze and visualize networks in a comparison of nine languages [@SkrljPollak2019]. Py3plex was also included in a comparative study of multilayer software that examined operator coverage and scalability [@Panayiotou2024]. These studies used earlier versions of the library.

# Availability

Py3plex is distributed under the MIT licence [@mitlicense]. The source code, documentation and examples are available on GitHub [@py3plexgithub], and the package is available on PyPI [@py3plexpypi].

# AI usage disclosure

The initial code was written by hand. OpenAI Codex was used for larger code refactors and to revise this manuscript (GPT-6 for the latter). GitHub Copilot and Anthropic Claude Code assisted with code review, candidate snippets, and tests. Google Gemini, OpenAI ChatGPT, and Anthropic Claude assisted with documentation drafting and editing and with grammar and spelling checks for the manuscript. The authors need to confirm the model and tool versions used for earlier work before submission. Human authors made the core design decisions and reviewed earlier drafts of the manuscript. They reviewed and validated AI-assisted code and text before inclusion and take responsibility for the submitted work; this revision also requires their review before submission.

# Acknowledgements

This work was partly funded by the Slovenian Research Agency under the projects: P2-0103, PR-12394 and GC-0002 (Large Language Models for Digital Humanities). This work was also partially supported by the European Union's Horizon Europe research and innovation program under grant agreement No. 101214398 (ELLIOT). Views and opinions expressed are, however, those of the author(s) only and do not necessarily reflect those of the European Union or the European Commission. Neither the European Union nor the European Commission can be held responsible for them. Furthermore, the authors thank the py3plex user and contributor community for feedback that has helped improve the library.

# References
