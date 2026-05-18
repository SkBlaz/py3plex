
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
[![PyPI - Downloads](https://img.shields.io/pypi/dm/py3plex)](https://pypistats.org/packages/py3plex)
![CLI Tool](https://img.shields.io/badge/CLI%20Tool-Available-brightgreen)
![Docker](https://img.shields.io/badge/Docker-Available-blue)
![Lines of Code](https://img.shields.io/badge/lines-211.4K-blue)
![Test Count](https://img.shields.io/badge/tests-9.2K-blue)

*Multilayer networks* are complex networks with additional information assigned to nodes or edges (or both). This library includes
some of the state-of-the-art algorithms for decomposition, visualization and analysis of such networks.

**Key Features:**
* SQL-like DSL for intuitive network queries with smart defaults
* Multilayer network visualization and analysis
* Community detection and centrality measures
* Network decomposition and embeddings


```python
from py3plex.core import datasets
from py3plex.dsl import Q

# Load a built-in multilayer biological network (~500 nodes, 4 layers)
network = datasets.fetch_multilayer("human_ppi_gene_disease_drug")

# Find key regulator candidates with integrated community detection and uncertainty quantification
master_regulators = (
    Q.communities(                           # Automated community detection
        mode="pareto",                       # Multi-objective Pareto selection
        uq=True,                             # Uncertainty quantification enabled
        uq_n_samples=30,                     # Robustness via 30 perturbed runs
        uq_method="seed",                    # Vary random seeds for stability
        seed=42,                             # Reproducibility
        write_attrs={                        # Attribute names for community info
            "community_id": "community_id",
            "community_stability": "community_stability",
        },
    )
    .nodes()                                 # Switch to node-level analysis
    .node_type("gene")                       # Filter by node type
    .where(degree__gt=3)                     # Remove peripheral nodes
    .uq(method="perturbation", n_samples=100, ci=0.95, seed=42)  # Quantify confidence
    .compute("betweenness_centrality", "pagerank", "degree_centrality")
    .per_layer()                             # Group by layer
        .top_k(30, "betweenness_centrality__mean")  # Top 30 per layer by mean
    .end_grouping()
    .coverage(mode="at_least", k=2)          # Keep nodes that are hubs in ≥2 layers
    .mutate(                                 # Create derived influence score
        score=lambda row: (
            0.5 * row.get("betweenness_centrality__mean", 0.0) +
            0.3 * row.get("pagerank__mean", 0.0) +
            0.2 * row.get("degree_centrality__mean", 0.0)
        )
    )
    .order_by("score", desc=True)
    .limit(20)                               # Final top 20 candidates
    .explain(neighbors_top=5)                # Enrich: community ID, top 5 partners, layers
    .execute(network)
)

df = master_regulators.to_pandas(expand_uncertainty=True, expand_explanations=True)
print(df[["id", "layer", "community_id",
          "betweenness_centrality__mean", "betweenness_centrality_ci95_low",
          "betweenness_centrality_ci95_high", "score", "top_neighbors"]].head(10))
```

### Safe chaining order (DSL v2)

Use a strict two-phase flow:

1. **Build query** on `Q...` (`.where()`, `.compute()`, `.order_by()`, `.per_layer()`, `.coverage()`, ...)
2. **Execute once** with `.execute(network)`
3. **Handle results** on `QueryResult` (`.to_pandas()`, `.group_summary()`, `.to_json()`, ...)

**Example output:**
```
    id  layer  community_id  betweenness_centrality__mean  betweenness_centrality_ci95_low  betweenness_centrality_ci95_high     score  top_neighbors
0  252      0            42                      0.025961                         0.021820                          0.030102  0.015577  [{'id': '91', 'weight': 2.3}, {'id': '419', 'weight': 1.9}]
1   91      0            42                      0.024918                         0.020902                          0.028934  0.014951  [{'id': '252', 'weight': 2.3}, {'id': '103', 'weight': 2.1}]
2  419      0            42                      0.024184                         0.020298                          0.028070  0.014510  [{'id': '252', 'weight': 1.9}, {'id': '91', 'weight': 1.7}]
3  103      0            42                      0.023450                         0.019596                          0.027304  0.014069  [{'id': '91', 'weight': 2.1}, {'id': '252', 'weight': 1.8}]
4  375      0            42                      0.022716                         0.018894                          0.026538  0.013628  [{'id': '91', 'weight': 1.8}, {'id': '252', 'weight': 1.6}]
```


**Key features demonstrated:**
- **Streamlined API**: Community detection integrated directly into the DSL query chain
- **AutoCommunity**: Multi-objective Pareto-optimal selection across algorithms (Louvain, Leiden, etc.)
- **Uncertainty Quantification**: Confidence intervals for both community detection and centrality measures
- **Cross-layer analysis**: `.coverage(mode="at_least", k=2)` keeps only nodes that are hubs in ≥2 layers
- **Interpretability**: `.explain()` enriches results with community IDs, top interaction partners, and layer presence
- **Composite scoring**: Weighted combination of multiple centrality measures for robust ranking

### Ecosystem positioning

| Comparator | Ecosystem | Primary scope | Where it overlaps with py3plex 2.0 | py3plex 2.0 positioning |
|---|---|---|---|---|
| **py3plex 2019** | Python | Multilayer network visualization and analysis | Direct historical predecessor: multilayer representation, aggregation, indexing, traversal, visualization, and embedding-assisted layouts | **Historical foundation.** py3plex 2.0 extends the original toolkit from visualization-oriented analysis into a reproducible, query-driven multilayer network science environment. |
| **pymnet** | Python | General multilayer network representation, metrics, random models, and visualization | Strong overlap on formal multilayer data structures, multilayer metrics, transformations, random models, and visualization | **Closest Python multilayer comparator.** pymnet is strongest as a formal multilayer framework; py3plex 2.0 is strongest as a workflow, DSL, uncertainty, and reproducibility layer. |
| **MultiNetX** | Python / NetworkX | NetworkX-style multilayer graph manipulation, spectral analysis, and visualization | Overlap on Python-native multilayer graph objects, supra-adjacency/Laplacian workflows, and visualization | **Lightweight Python comparator.** MultiNetX provides compact multilayer graph utilities; py3plex 2.0 provides a broader end-to-end analysis and workflow environment. |
| **muxViz** | R / desktop ecosystem | Multilayer and multiplex visual analytics | Overlap on multilayer visualization, centrality, community detection, motifs, structural reducibility, and dynamic visualization | **R visual-analytics comparator.** muxViz is strongest for visual exploration; py3plex 2.0 emphasizes Python-native, scriptable, DSL-driven, reproducible analysis. |
| **R `multinet`** | R | Multiplex and multilayer social-network analysis and mining | Overlap on multilayer representation, import/export, attributes, centrality, community detection, generation, and plotting | **R social-network comparator.** `multinet` is strongest for multiplex social-network analysis; py3plex 2.0 targets broader heterogeneous scientific multilayer workflows in Python. |
| **tnetwork** | Python | Temporal-network manipulation and dynamic communities | Overlap on temporal slicing, dynamic graphs, and evolving-community analysis | **Temporal-community comparator.** tnetwork focuses on temporal community workflows; py3plex 2.0 embeds temporal analysis inside a broader multilayer DSL/workflow stack. |
| **DyNetx** | Python / NetworkX | Dynamic graph extension for NetworkX | Overlap on time-varying graph representation, snapshots, interaction streams, and temporal slicing | **Dynamic-NetworkX comparator.** DyNetx handles dynamic graphs; py3plex 2.0 adds multilayer semantics, declarative analysis, integrated dynamics, and reusable workflows. |
| **Reticula** | Python with C++ core | Fast static and temporal network / hypergraph analysis | Overlap on temporal networks, reachability, randomized models, and dynamical-process analysis | **Performance temporal/hypergraph comparator.** Reticula is stronger for fast temporal and hypergraph analysis; py3plex 2.0 is stronger for multilayer workflow integration and analyst ergonomics. |
| **Raphtory** | Rust / Python | Temporal graph engine and deployment platform | Overlap on temporal graph views, time-aware querying, reachability, motifs, and deployment-oriented graph analysis | **Modern temporal-engine comparator.** Raphtory is an engine/platform; py3plex 2.0 is a multilayer network-science workflow layer with DSL, uncertainty, dynamics, and reproducible analysis. |
| **pathpy / pathpyG** | Python / PyTorch ecosystem | Path-centric temporal-network analytics and graph learning | Overlap on temporal analytics, time-respecting paths, temporal centralities, visualization, and graph-learning handoff | **Temporal graph-learning comparator.** pathpy/pathpyG is adjacent; py3plex 2.0 focuses on multilayer network science, layer-aware querying, uncertainty, and reproducible workflows. |
| **NetworkX** | Python | General graph creation, manipulation, and algorithms | Overlap on core graph algorithms, graph data structures, centrality, communities, and Python graph workflows | **General graph substrate.** NetworkX is the base graph ecosystem; py3plex 2.0 adds multilayer semantics, DSL queries, layer algebra, temporal/dynamics workflows, and structured outputs. |
| **igraph** | C / R / Python | Efficient general-purpose network analysis | Overlap on centrality, community detection, graph transformations, and scalable graph analysis | **Efficient general-graph comparator.** igraph is the speed/breadth baseline; py3plex 2.0 differentiates through multilayer-specific workflows and reproducible analyst interfaces. |
| **graph-tool** | Python with C++ core | High-performance graph algorithms and statistical network modeling | Overlap on large-network statistics, community detection, inference, and performance-sensitive graph analysis | **Performance/statistical comparator.** graph-tool is strongest for efficient statistical graph analysis; py3plex 2.0 prioritizes multilayer expressiveness, querying, uncertainty, and workflow integration. |
| **tidygraph** | R / tidyverse | Tidy, dplyr-style graph manipulation | Overlap on chainable, analyst-friendly node/edge manipulation and graph-as-table workflows | **Analyst-grammar comparator.** tidygraph motivates fluent graph manipulation; py3plex 2.0 adapts this style to Python multilayer networks with DSL, builder APIs, and layer-aware grouping. |
| **NDlib** | Python | Diffusion and epidemic processes on networks | Overlap on SIS/SIR-style processes, random walks, spreading dynamics, and simulation workflows | **Dynamics comparator.** NDlib specializes in diffusion; py3plex 2.0 embeds dynamics inside multilayer, temporal, queryable, uncertainty-aware workflows. |
| **PyTorch Geometric** | Python / PyTorch | Graph neural networks and geometric deep learning | Overlap on graph embeddings, graph data preparation, and downstream graph-learning workflows | **Graph-ML comparator.** PyG trains graph neural models; py3plex 2.0 prepares, queries, explains, summarizes, and analyzes multilayer networks. |
| **DGL** | Python / deep-learning frameworks | Scalable graph deep learning and message passing | Overlap on heterogeneous graph processing, graph learning, and scalable graph ML pipelines | **Scalable graph-ML comparator.** DGL addresses GNN systems engineering; py3plex 2.0 addresses multilayer network science, query abstractions, uncertainty, temporal analysis, and workflows. |
| **Neo4j / Cypher** | Database systems | Persistent property-graph storage and declarative graph querying | Overlap on declarative graph querying and pattern-style graph access | **Graph-query comparator.** Cypher queries persistent property graphs; py3plex 2.0 provides an in-memory scientific DSL for multilayer network analysis, metrics, uncertainty, and exports. |
| **py3plex 2.0** | Python | Query-driven, reproducible multilayer network analysis | Integrates capabilities otherwise spread across multilayer libraries, temporal engines, graph libraries, graph-ML frameworks, graph-query systems, and workflow tools | **Main contribution.** py3plex 2.0 is best framed as a Python-native workflow layer for multilayer network science: DSL + builder API, layer algebra, QueryResult exports, uncertainty-first statistics, temporal/dynamics workflows, null models, CLI/config execution, and agent-facing interfaces. |

![Py3plex Visualization Showcase](example_images/py3plex_showcase.png)

## Getting Started

### Installation

We recommend using [uv](https://docs.astral.sh/uv/) for fast, reliable Python environment management:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install py3plex
uv pip install py3plex

# Or install from source with development dependencies
uv pip install -e ".[dev]"
```

Alternatively, use pip:
```bash
pip install py3plex
```

### Optional Features

Install additional features as needed:

```bash
# MCP server for AI agent integration (requires Python 3.10+)
pip install py3plex[mcp]

# Community detection algorithms
pip install py3plex[algos]

# Advanced visualization
pip install py3plex[viz]

# All optional features
pip install py3plex[mcp,algos,viz]

# Common optional feature bundle (algorithms + visualization + workflows + arrow + mcp)
pip install py3plex[optional]
```

### Contributing (First PR Quick Path)

If this is your first contribution, use this sequence:

```bash
# 1) Create local dev environment and install package
make setup
make dev-install

# 2) Run formatting and checks before opening a PR
make format
make lint
make test
```

Helpful commands:

```bash
make help   # List all project commands
make ci     # Run lint + tests in CI-style order
```

Safety notes for contributors:
- Keep changes focused and add tests next to the feature you modify.
- Do not add new markdown files unless explicitly requested (enforced by `tests/test_link_checker.py` to prevent documentation drift).
- Prefer running targeted tests first, then broader checks before opening a PR.
- For docs-only updates, run `make docs-check` before opening a PR.

### MCP Integration (AI Agents)

py3plex provides a Model Context Protocol (MCP) server for integration with AI coding assistants:

**Requirements**: Python 3.10 or higher (due to MCP SDK dependency)

```bash
# Install with MCP support (Python 3.10+ required)
pip install py3plex[mcp]

# Start MCP server
py3plex-mcp
```

**Configure Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "py3plex": {
      "command": "py3plex-mcp"
    }
  }
}
```

The MCP server exposes:
- **7 tools**: Load networks, run queries (with DSL v2 support), detect communities, export results, and more
- **3 resources**: Complete documentation, DSL v2 reference, and tool schemas
- **DSL v2 support**: Modern builder API with type hints (`Q.nodes().where(degree__gt=5).compute('pagerank')`)
- **Security-first**: Safe file access, automatic output directory, structured errors

See [AGENTS.md](AGENTS.md#mcp-integration-model-context-protocol) for complete MCP documentation including DSL v2 examples.

### Resources

* **Documentation:** [https://skblaz.github.io/py3plex/](https://skblaz.github.io/py3plex/)
* **Technical Book (PDF):** [Practical Multilayer Network Analysis with Py3plex](docs/py3plex_book.pdf) - Complete handbook (106 pages)
* **Examples:** [examples/](examples/) - 170+ example scripts demonstrating usage

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
