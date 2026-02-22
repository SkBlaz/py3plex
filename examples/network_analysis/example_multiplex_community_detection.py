"""
Multiplex Community Detection Example

Teaches:
- Pipeline-based Louvain detection on synthetic multiplex graphs
- DSL-based community detection and interoperability with pipeline outputs
- File-based multiplex workflow for reproducible runs

Prerequisites:
- Dataset files: `simple_multiplex.edgelist` and `simple_multiplex.txt`
- py3plex installed (brings required dependencies)

SKIP_CI: external_deps - Requires specific dataset files (simple_multiplex.edgelist)
"""

from __future__ import annotations

import os
from typing import Dict

import numpy as np

try:
    from py3plex.algorithms.community_detection import community_wrapper as cw
    from py3plex.core import multinet
    from py3plex.dsl import detect_communities, execute_query
    from py3plex.pipeline import LoadStep, LouvainCommunity, Pipeline
    from py3plex.utils import get_dataset_path
except ImportError as exc:  # pragma: no cover - surfaced to user
    cw = None
    multinet = None
    detect_communities = None
    execute_query = None
    LoadStep = None
    LouvainCommunity = None
    Pipeline = None
    get_dataset_path = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

DEFAULT_SEED = 42


def _print_header(title: str) -> None:
    """Consistent section header formatting."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def approach_pipeline_chaining() -> None:
    """Approach 1: Pipeline-based community detection (chaining)."""
    _print_header("Approach 1: Pipeline-based community detection (chaining)")
    pipe = Pipeline(
        [
            ("generate", LoadStep(generator="random_er", n=50, l=8, p=0.05)),
            ("community", LouvainCommunity()),
        ]
    )
    result = pipe.run()
    print(f"Communities found: {result['num_communities']}")
    print(f"Sample assignments: {dict(list(result['communities'].items())[:5])}")


def approach_dsl() -> None:
    """Approach 2: DSL-based community detection (declarative)."""
    _print_header("Approach 2: DSL-based community detection (declarative)")
    network = LoadStep(generator="random_er", n=30, l=3, p=0.1).transform(None)
    dsl_result = execute_query(network, "SELECT nodes COMPUTE communities")
    print("DSL query: SELECT nodes COMPUTE communities")
    print(f"Communities found: {len(set(dsl_result['computed']['communities'].values()))}")


def approach_interoperability() -> None:
    """Approach 3: Pipeline + DSL interoperability on the same network."""
    _print_header("Approach 3: Interoperability - Pipeline network -> DSL analysis")
    generated_net = LoadStep(generator="random_er", n=40, l=4, p=0.08).transform(None)
    dsl_analysis = detect_communities(generated_net)
    print(f"Network has {dsl_analysis['num_communities']} communities")
    print(f"Biggest community: {dsl_analysis['biggest_community']}")

    traditional_part = cw.louvain_communities(generated_net)
    print(f"Traditional Louvain partitions: {len(set(traditional_part.values()))}")


def approach_file_based() -> None:
    """Approach 4: Traditional file-based multiplex workflow."""
    _print_header("Approach 4: Traditional approach (file-based network)")
    edge_path = get_dataset_path("simple_multiplex.edgelist")
    mapping_path = get_dataset_path("simple_multiplex.txt")

    if not os.path.exists(edge_path) or not os.path.exists(mapping_path):
        print("Required multiplex dataset files are missing; skipping file-based demo.")
        return

    com_net = multinet.multi_layer_network().load_network(
        edge_path, directed=False, input_type="multiplex_edges"
    )
    com_net.load_layer_name_mapping(mapping_path)
    com_net.basic_stats()
    partition: Dict = cw.louvain_communities(com_net)
    print(f"Partition: {partition}")


def main() -> int:
    """Run all multiplex community detection approaches."""
    if IMPORT_ERROR:
        print(f"Error importing dependencies: {IMPORT_ERROR}")
        print("Install py3plex to run this example.")
        return 1

    np.random.seed(DEFAULT_SEED)
    _print_header("Multiplex Community Detection Walkthrough")

    try:
        approach_pipeline_chaining()
        approach_dsl()
        approach_interoperability()
        approach_file_based()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Error during multiplex community walkthrough: {exc}")
        return 1

    print("\n" + "=" * 60)
    print("Summary: All approaches use interoperable multi_layer_network objects")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
