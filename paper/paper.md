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

Multilayer networks represent systems with several kinds of relationships. Keeping those relationships in separate layers allows researchers to study each layer and the connections between them [@kivela2014; @boccaletti2014]. Py3plex is a Python library for analyzing and visualizing these networks.

The original Py3plex publications focused on multilayer network representation, analysis, and visualization [@skrlj2019toolkit; @skrlj2019conference]. Version 2.0 adds a query language, expands the available algorithms, and provides tools for uncertainty analysis and recording how results were produced. It also includes a Model Context Protocol (MCP) server through which compatible assistants can access network analysis tools.

# Statement of Need

Researchers in fields such as social science, biology, and physics often need to compare relationships across layers. A network of people, for example, might contain separate layers for work and friendship. Combining these layers into one graph can hide whether a connection belongs to one setting or both.

General graph libraries such as NetworkX [@networkx] and igraph [@igraph] can store layer labels, but users must manage their interpretation. Dedicated multilayer packages offer data structures and analysis methods, while a researcher may still need to assemble separate tools for selecting layers, assessing uncertainty, and recording an analysis.

Py3plex represents each occurrence of a node in a layer separately and supports edges within and between layers. It offers a query language for selecting and analyzing parts of a network, along with tools for uncertainty analysis and provenance. Its methods include community detection, centrality measures, diffusion simulations, embeddings, and multilayer visualization.

# State of the Field

General graph libraries such as NetworkX [@networkx] and igraph [@igraph] provide data structures and algorithms that can be used with layer labels. Dedicated multilayer packages include pymnet [@pymnet] and MultiNetX [@multinex], both of which provide multilayer representations and operations. Pymnet also supports models with multiple aspects. MuxViz [@muxviz] provides multilayer analysis and visualization in R; Tulip [@Tulip] offers general graph visualization and analysis with Python support.

Py3plex 2.0 extends the existing Py3plex library, retaining its NetworkX-based representation and API. This allows its new query and uncertainty features to work with networks built using the earlier library. Researchers can choose among these tools according to their needs, such as pymnet's support for multiple aspects or muxViz's visualization tools.

# Software Design

Py3plex represents a node in a layer as a pair `(node_id, layer_id)`. Its core network stores these pairs and their edges in a NetworkX MultiGraph or MultiDiGraph. This choice gives users access to NetworkX data structures and algorithms without requiring a dense tensor for the network. It also means that a node's role can be studied separately in each layer.

The library supports multilayer networks whose node sets differ across layers and multiplex networks in which nodes have counterparts across layers. Inter-layer edges in a general multilayer network are specified by the user. For multiplex networks loaded through the network loader, Py3plex can create coupling edges between replicas of the same node; these generated edges have a distinct type tag.

NetworkX interoperability has a trade-off. Some analyses operate directly on the multilayer representation, whereas others restrict the network to a layer or project it to a single graph before applying a delegated algorithm. For example, a degree calculated on a single layer counts connections within that layer, while a degree calculated on the full network can also count inter-layer connections. The execution path therefore matters when interpreting a result. For matrix-based analysis, Py3plex can also construct a supra-adjacency matrix, with within-layer connections on diagonal blocks and inter-layer connections on off-diagonal blocks. For performance, the library includes vectorized layer aggregation and a query planner that can reorder stages of a query.

Queries are represented internally as an abstract syntax tree, which can be inspected before execution. In supported workflows, the result can retain the query and its provenance alongside uncertainty estimates. The library also provides temporal network operations, network embeddings, and layouts that display layers and their inter-layer edges.

# Research impact statement

Earlier versions of Py3plex have been used to visualize gene communities in a temporal study of grapevine infection [@SkrljEtAl2021] and to analyze and visualize networks in a comparison of nine languages [@SkrljPollak2019]. Py3plex was also included in a comparative study of multilayer software that examined operator coverage and scalability [@Panayiotou2024]. These studies used earlier versions of the library.

# Availability

Py3plex is released under the MIT licence [@mitlicense]. The repository also contains third-party Infomap code distributed under the GNU Affero General Public License version 3 or later. The source code, documentation and examples are available on GitHub [@py3plexgithub], and the package is available on PyPI [@py3plexpypi].

# AI usage disclosure

The authors made the software design decisions and wrote the initial code and paper. OpenAI Codex assisted with coding and larger refactors. The authors used large language models to refine the paper and align its description with the codebase; Codex using GPT-6 assisted with the revisions in this submission. Earlier drafting and editing also used Google Gemini, OpenAI ChatGPT, and Anthropic Claude, and GitHub Copilot and Claude Code assisted with code and tests. The authors are responsible for reviewing and validating all AI-assisted material. [Before submission, confirm the tool and model versions used for earlier work and complete the authors' review of this revision.]

# Acknowledgements

This work was partly funded by the Slovenian Research Agency under the projects: P2-0103, PR-12394 and GC-0002 (Large Language Models for Digital Humanities). This work was also partially supported by the European Union's Horizon Europe research and innovation program under grant agreement No. 101214398 (ELLIOT). Views and opinions expressed are, however, those of the author(s) only and do not necessarily reflect those of the European Union or the European Commission. Neither the European Union nor the European Commission can be held responsible for them. Furthermore, the authors thank the py3plex user and contributor community for feedback that has helped improve the library.

# References
