"""
Example: Pipeline with DSL Query Steps

Demonstrates how to integrate py3plex DSL queries into pipeline workflows.
Shows how to use query results to filter, aggregate, and transform networks
within a Pipeline, combining both pipeline and DSL patterns for flexible
analysis workflows.

This bridges the Pipeline API (example_6_complex_pipeline.py) with the DSL
builder API (dsl_zoo examples), showing they can work together seamlessly.

Runtime: FAST (<1 second)
"""

from __future__ import annotations

from pathlib import Path
import sys

# Allow running the example without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.pipeline import Pipeline, PipelineStep

DEFAULT_SEED = 42


class DSLFilterStep(PipelineStep):
    """Pipeline step that uses DSL to filter nodes."""

    def __init__(self, min_degree: int = 2, layer: str | None = None):
        self.min_degree = min_degree
        self.layer = layer

    def transform(self, network):
        """Filter nodes using DSL query and return filtered network."""
        print(f"\n[DSLFilterStep] Filtering nodes (degree > {self.min_degree})...")

        # Build DSL query
        query = Q.nodes().compute("degree").where(degree__gte=self.min_degree)
        if self.layer:
            query = query.from_layers(L[self.layer])

        # Execute query
        result = query.execute(network)

        total_nodes = len(list(network.get_nodes()))
        print(f"  Kept {result.count} nodes out of {total_nodes}")

        # Create new network with filtered nodes
        filtered_net = multinet.multi_layer_network(directed=network.directed)

        # Add filtered nodes
        nodes_to_keep = set(result.items)
        for node_id, layer in nodes_to_keep:
            filtered_net.add_nodes([{"source": node_id, "type": layer}])

        # Add edges between kept nodes
        for (src_id, src_layer), (dst_id, dst_layer) in network.get_edges():
            if (src_id, src_layer) in nodes_to_keep and (dst_id, dst_layer) in nodes_to_keep:
                filtered_net.add_edges(
                    [
                        {
                            "source": src_id,
                            "target": dst_id,
                            "source_type": src_layer,
                            "target_type": dst_layer,
                        }
                    ]
                )

        return filtered_net


class DSLAggregateStep(PipelineStep):
    """Pipeline step that uses DSL to compute per-layer statistics."""

    def __init__(self):
        pass

    def transform(self, network):
        """Compute per-layer statistics using DSL."""
        print("\n[DSLAggregateStep] Computing per-layer statistics...")

        result = (
            Q.nodes()
            .per_layer()
            .compute("degree")
            .aggregate(
                avg_degree="mean(degree)",
                max_degree="max(degree)",
                node_count="count()",
            )
            .execute(network)
        )

        stats = result.to_pandas()
        print(stats.to_string(index=False))

        # Return original network (stats already printed)
        return network


class DSLTopNodesStep(PipelineStep):
    """Pipeline step that identifies top nodes using DSL."""

    def __init__(self, k: int = 5, metric: str = "degree"):
        self.k = k
        self.metric = metric

    def transform(self, network):
        """Find top-k nodes per layer using DSL."""
        print(f"\n[DSLTopNodesStep] Finding top-{self.k} nodes by {self.metric}...")

        result = (
            Q.nodes()
            .per_layer()
            .compute(self.metric)
            .top_k(self.k, self.metric)
            .end_grouping()
            .execute(network)
        )

        top_nodes = result.to_pandas()
        print(f"\nTop nodes per layer:")
        # Group by layer and display
        if "layer" in top_nodes.columns:
            # get_layers() returns (layer_names, layer_graphs, ...)
            layer_names = network.get_layers()[0]
            for layer in layer_names:
                layer_nodes = top_nodes[top_nodes["layer"] == layer]
                if not layer_nodes.empty:
                    print(f"  {layer}: {list(layer_nodes['id'].head(self.k).values)}")
        else:
            print(f"  Total top nodes: {len(top_nodes)}")

        return network


def create_sample_network() -> multinet.multi_layer_network:
    """Create a sample multilayer network."""
    network = multinet.multi_layer_network(directed=False)

    # Two layers with 20 nodes each
    nodes = []
    for i in range(20):
        nodes.append({"source": i, "type": "layer1"})
        nodes.append({"source": i, "type": "layer2"})
    network.add_nodes(nodes)

    # Layer 1: star-like (one hub)
    edges1 = []
    for i in range(1, 20):
        edges1.append(
            {"source": 0, "target": i, "source_type": "layer1", "target_type": "layer1"}
        )

    # Layer 2: chain-like
    edges2 = []
    for i in range(19):
        edges2.append(
            {
                "source": i,
                "target": i + 1,
                "source_type": "layer2",
                "target_type": "layer2",
            }
        )

    network.add_edges(edges1 + edges2)
    return network


def run_dsl_pipeline_example():
    """Run example with DSL query steps."""
    print("=" * 70)
    print("DSL Query Steps Examples")
    print("=" * 70)

    # Create network
    net = create_sample_network()
    nodes = list(net.get_nodes())
    edges = list(net.get_edges())
    print(f"\nInitial network:")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {len(edges)}")
    print(f"  Layers: {net.get_layers()}")

    # Example 1: Per-layer statistics
    print("\n" + "=" * 70)
    print("Example 1: Per-Layer Statistics")
    print("=" * 70)
    
    DSLAggregateStep().transform(net)

    # Example 2: Top nodes per layer
    print("\n" + "=" * 70)
    print("Example 2: Top-K Nodes Per Layer")
    print("=" * 70)
    
    DSLTopNodesStep(k=5, metric="degree").transform(net)

    # Example 3: Filter high-degree nodes
    print("\n" + "=" * 70)
    print("Example 3: Filter High-Degree Nodes")
    print("=" * 70)
    
    filtered_net = DSLFilterStep(min_degree=2).transform(net)
    
    print("\n" + "=" * 70)
    print("Filtered Network Results")
    print("=" * 70)
    result_nodes = list(filtered_net.get_nodes())
    result_edges = list(filtered_net.get_edges())
    print(f"\nFiltered network:")
    print(f"  Nodes: {len(result_nodes)} (removed {len(nodes) - len(result_nodes)})")
    print(f"  Edges: {len(result_edges)} (removed {len(edges) - len(result_edges)})")


def main() -> int:
    """Run the DSL pipeline example."""
    try:
        run_dsl_pipeline_example()
        print("\n" + "=" * 70)
        print("DSL pipeline example completed successfully!")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
