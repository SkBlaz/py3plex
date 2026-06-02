"""
Multilayer Example: Ollivier-Ricci Curvature and Ricci Flow

This example demonstrates how to compute Ollivier-Ricci curvature and apply
Ricci flow on multilayer networks for geometric analysis of community structure,
bottlenecks, and hierarchical organization.

Features demonstrated:
1. Computing curvature on aggregated (core) networks
2. Computing curvature per layer
3. Computing curvature on supra-graphs (with inter-layer coupling)
4. Applying Ricci flow to reveal community structure
5. Analyzing edge curvatures to identify bottlenecks

Requirements:
    pip install GraphRicciCurvature

SKIP_CI: optional_deps - Requires GraphRicciCurvature
"""

import sys
from py3plex.core import multinet

# Check if GraphRicciCurvature is available
try:
    from GraphRicciCurvature.OllivierRicci import OllivierRicci
    GRAPHRICCICURVATURE_AVAILABLE = True
except ImportError:
    GRAPHRICCICURVATURE_AVAILABLE = False
    print("=" * 70)
    print("ERROR: GraphRicciCurvature is not installed")
    print("=" * 70)
    print("\nThis example requires the GraphRicciCurvature library.")
    print("Install it with:")
    print("    pip install GraphRicciCurvature")
    print("\nFor more information, see:")
    print("    https://github.com/saibalmars/GraphRicciCurvature")
    print("=" * 70)
    sys.exit(1)

print("=" * 70)
print("OLLIVIER-RICCI CURVATURE AND RICCI FLOW DEMONSTRATION")
print("=" * 70)

# ============================================================================
# Create a synthetic multilayer network for demonstration
# ============================================================================

print("\n" + "=" * 70)
print("STEP 1: Creating a synthetic multilayer network")
print("=" * 70)

net = multinet.multi_layer_network(directed=False)

# Layer 1: Create a triangle (dense community) + a bridge node
print("\nAdding Layer 1: Triangle community with bridge...")
net.add_edges([
    ['A', 'layer1', 'B', 'layer1', 1],
    ['B', 'layer1', 'C', 'layer1', 1],
    ['C', 'layer1', 'A', 'layer1', 1],
    ['C', 'layer1', 'D', 'layer1', 1],  # Bridge edge (bottleneck)
    ['D', 'layer1', 'E', 'layer1', 1],
], input_type="list")

# Layer 2: Create another triangle + connections
print("Adding Layer 2: Another community structure...")
net.add_edges([
    ['A', 'layer2', 'B', 'layer2', 1],
    ['B', 'layer2', 'D', 'layer2', 1],
    ['D', 'layer2', 'A', 'layer2', 1],
    ['D', 'layer2', 'E', 'layer2', 1],
], input_type="list")

print(f"\nNetwork created: {net}")
print(f" - Nodes: {net.core_network.number_of_nodes()}")
print(f" - Edges: {net.core_network.number_of_edges()}")

# ============================================================================
# Example 1: Compute Ollivier-Ricci Curvature on Core Network
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 1: Curvature on Aggregated (Core) Network")
print("=" * 70)

print("\nComputing Ollivier-Ricci curvature on the core network...")
print("(This combines all layers into one aggregated graph)")

try:
    result_core = net.compute_ollivier_ricci(
        mode="core",
        alpha=0.5,          # Standard Ollivier-Ricci parameter
        inplace=False,      # Don't modify the original network
    )

    G_core = result_core["core"]
    print(f"\n Curvature computed on {G_core.number_of_edges()} edges")

    # Display edge curvatures
    print("\nEdge Curvatures (sorted by curvature):")
    print("-" * 70)
    print(f"{'Edge':<30} {'Curvature':>10}")
    print("-" * 70)

    edge_curvatures = []
    for u, v, data in G_core.edges(data=True):
        if "ricciCurvature" in data:
            curvature = data["ricciCurvature"]
            edge_curvatures.append((u, v, curvature))

    # Sort by curvature (ascending - negative curvatures first)
    edge_curvatures.sort(key=lambda x: x[2])

    for u, v, curvature in edge_curvatures[:10]:  # Show first 10
        edge_str = f"{u} -- {v}"
        print(f"{edge_str:<30} {curvature:>10.4f}")

    # Identify bottleneck edges (negative curvature)
    bottlenecks = [(u, v, c) for u, v, c in edge_curvatures if c < 0]
    if bottlenecks:
        print(f"\n Identified {len(bottlenecks)} bottleneck edge(s) with negative curvature:")
        for u, v, curvature in bottlenecks:
            print(f"  {u} -- {v}: {curvature:.4f}")
        print("  (These edges likely connect different communities)")

except Exception as e:
    print(f"\n Error computing curvature: {e}")

# ============================================================================
# Example 2: Compute Curvature Per Layer
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 2: Curvature on Individual Layers")
print("=" * 70)

print("\nComputing curvature separately for each layer...")

try:
    result_layers = net.compute_ollivier_ricci(
        mode="layers",
        layers=None,  # None means all layers
        alpha=0.5,
        inplace=False,
    )

    print(f"\n Computed curvature on {len(result_layers)} layer(s)")

    for layer_id, G_layer in result_layers.items():
        print(f"\n  Layer: {layer_id}")
        print(f"    Edges: {G_layer.number_of_edges()}")

        # Calculate average curvature for this layer
        curvatures = [
            data.get("ricciCurvature", 0)
            for u, v, data in G_layer.edges(data=True)
        ]
        if curvatures:
            avg_curvature = sum(curvatures) / len(curvatures)
            print(f"    Average curvature: {avg_curvature:.4f}")

        # Show a few edge curvatures
        print(f"    Sample edges:")
        for i, (u, v, data) in enumerate(list(G_layer.edges(data=True))[:3]):
            curvature = data.get("ricciCurvature", 0)
            print(f"      {u} -- {v}: {curvature:.4f}")

except Exception as e:
    print(f"\n Error computing per-layer curvature: {e}")

# ============================================================================
# Example 3: Compute Curvature on Supra-Graph
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 3: Curvature on Supra-Graph (with Inter-Layer Coupling)")
print("=" * 70)

print("\nComputing curvature on the supra-graph...")
print("(This includes both intra-layer edges AND inter-layer coupling edges)")

try:
    result_supra = net.compute_ollivier_ricci(
        mode="supra",
        alpha=0.5,
        interlayer_weight=1.0,  # Weight for coupling edges between layers
        inplace=False,
    )

    G_supra = result_supra["supra"]
    print(f"\n Supra-graph curvature computed")
    print(f"  Total nodes: {G_supra.number_of_nodes()}")
    print(f"  Total edges: {G_supra.number_of_edges()}")

    # Count and analyze inter-layer edges
    inter_layer_edges = []
    intra_layer_edges = []

    for u, v, data in G_supra.edges(data=True):
        if isinstance(u, tuple) and isinstance(v, tuple):
            curvature = data.get("ricciCurvature", 0)
            if u[0] == v[0] and u[1] != v[1]:  # Same node, different layers
                inter_layer_edges.append((u, v, curvature))
            elif u[1] == v[1]:  # Same layer
                intra_layer_edges.append((u, v, curvature))

    print(f"\n  Intra-layer edges: {len(intra_layer_edges)}")
    print(f"  Inter-layer edges: {len(inter_layer_edges)}")

    if inter_layer_edges:
        print(f"\n  Inter-layer coupling curvatures:")
        for u, v, curvature in inter_layer_edges[:5]:  # Show first 5
            print(f"    {u} -- {v}: {curvature:.4f}")

except Exception as e:
    print(f"\n Error computing supra-graph curvature: {e}")

# ============================================================================
# Example 4: Apply Ricci Flow
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 4: Applying Ricci Flow")
print("=" * 70)

print("\nApplying Ricci flow to the core network...")
print("(Ricci flow adjusts edge weights based on curvature)")
print(" - Edges with negative curvature (bottlenecks) -> reduced weight")
print(" - Edges with positive curvature (communities) -> increased weight")

try:
    result_flow = net.compute_ollivier_ricci_flow(
        mode="core",
        alpha=0.5,
        iterations=10,  # Number of flow iterations
        method="OTD",   # Optimal Transport Distance (recommended)
        inplace=False,
    )

    G_flow = result_flow["core"]
    print(f"\n Ricci flow applied ({10} iterations)")

    # Compare edge weights before and after flow
    print("\nEdge weight changes after Ricci flow:")
    print("-" * 70)
    print(f"{'Edge':<30} {'Original':>10} {'After Flow':>12} {'Change':>10}")
    print("-" * 70)

    weight_changes = []
    for u, v, data in G_flow.edges(data=True):
        flow_weight = data.get("weight", 1.0)
        original_weight = 1.0  # Our original edges had weight 1
        change = flow_weight - original_weight
        curvature = data.get("ricciCurvature", 0)
        weight_changes.append((u, v, original_weight, flow_weight, change, curvature))

    # Sort by magnitude of change
    weight_changes.sort(key=lambda x: abs(x[4]), reverse=True)

    for u, v, orig, flow_w, change, curv in weight_changes[:10]:
        edge_str = f"{u} -- {v}"
        print(f"{edge_str:<30} {orig:>10.4f} {flow_w:>12.4f} {change:>10.4f}")

    print("\nInterpretation:")
    print("  - Edges with increased weights are likely within communities")
    print("  - Edges with decreased weights are likely community boundaries")
    print("  - This makes community detection more effective!")

except Exception as e:
    print(f"\n Error applying Ricci flow: {e}")

# ============================================================================
# Example 5: Using Ricci Flow for Community Detection
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 5: Enhanced Community Detection with Ricci Flow")
print("=" * 70)

print("\nRicci flow can improve community detection by:")
print(" 1. Reducing weights on community boundary edges")
print(" 2. Increasing weights within communities")
print(" 3. Making communities more separable")

try:
    # Apply flow
    flow_result = net.compute_ollivier_ricci_flow(
        mode="core",
        iterations=20,  # More iterations for stronger effect
        inplace=False,
    )

    G_flow = flow_result["core"]

    # Try community detection (if available)
    try:
        from py3plex.algorithms.community_detection import community_wrapper

        print("\nRunning community detection on flow-enhanced network...")
        communities = community_wrapper.best_partition(G_flow)

        # Count communities
        from collections import defaultdict
        comm_sizes = defaultdict(int)
        for node, comm_id in communities.items():
            comm_sizes[comm_id] += 1

        print(f"\n Detected {len(comm_sizes)} communities:")
        for comm_id, size in sorted(comm_sizes.items()):
            print(f"  Community {comm_id}: {size} nodes")

    except ImportError:
        print("\n(Community detection library not available)")
        print("Install with: pip install python-louvain")

except Exception as e:
    print(f"\n Error in community detection example: {e}")

# ============================================================================
# Summary and Best Practices
# ============================================================================

print("\n" + "=" * 70)
print("SUMMARY AND BEST PRACTICES")
print("=" * 70)

print("""
Ollivier-Ricci Curvature in Multilayer Networks:

1. CURVATURE INTERPRETATION:
   - Positive curvature: Dense, well-connected regions (communities)
   - Negative curvature: Sparse connections, bottlenecks (boundaries)
   - Near-zero: Transitional regions

2. THREE MODES OF ANALYSIS:
   - mode="core": Analyze the aggregated network (all layers combined)
   - mode="layers": Analyze each layer independently
   - mode="supra": Full multilayer structure with inter-layer coupling

3. RICCI FLOW APPLICATIONS:
   - Reveals hidden community structure
   - Identifies critical edges and bottlenecks
   - Enhances standard community detection algorithms
   - Useful for hierarchical analysis

4. PERFORMANCE TIPS:
   - Start with small networks or subgraphs
   - Use lower alpha values (e.g., 0.3) for faster computation
   - Reduce iterations for Ricci flow (start with 5-10)
   - Use parallel computation: backend_kwargs={"proc": 4}

5. FURTHER READING:
   - Ni et al. (2019): Community detection on networks with Ricci flow
   - Ollivier (2009): Ricci curvature of Markov chains on metric spaces
   - GraphRicciCurvature docs: https://github.com/saibalmars/GraphRicciCurvature
""")

print("=" * 70)
print("Example completed successfully!")
print("=" * 70)
