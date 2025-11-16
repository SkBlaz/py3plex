"""
Ricci-Flow-Based Visualization Example

This example demonstrates the three main visualization styles for Ricci-flow-based
layouts in py3plex:
1. Core (aggregated) visualization
2. Per-layer visualization with shared layout
3. Supra-graph visualization

Requirements:
    pip install GraphRicciCurvature

SKIP_CI: optional_deps - Requires GraphRicciCurvature
"""

import sys

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt

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
print("RICCI-FLOW-BASED VISUALIZATION DEMONSTRATION")
print("=" * 70)

# ============================================================================
# Create a synthetic multilayer network
# ============================================================================

print("\n" + "=" * 70)
print("STEP 1: Creating a synthetic multilayer network")
print("=" * 70)

net = multinet.multi_layer_network(directed=False)

# Layer 1: Create two communities connected by a bridge
print("\nAdding Layer 1: Two communities with a bridge...")
net.add_edges(
    [
        # Community 1
        ["A", "layer1", "B", "layer1", 1],
        ["B", "layer1", "C", "layer1", 1],
        ["C", "layer1", "A", "layer1", 1],
        # Bridge
        ["C", "layer1", "D", "layer1", 1],
        # Community 2
        ["D", "layer1", "E", "layer1", 1],
        ["E", "layer1", "F", "layer1", 1],
        ["F", "layer1", "D", "layer1", 1],
    ],
    input_type="list",
)

# Layer 2: Create a different structure
print("Adding Layer 2: Different community structure...")
net.add_edges(
    [
        ["A", "layer2", "B", "layer2", 1],
        ["B", "layer2", "D", "layer2", 1],
        ["D", "layer2", "E", "layer2", 1],
        ["E", "layer2", "A", "layer2", 1],
        ["C", "layer2", "F", "layer2", 1],
    ],
    input_type="list",
)

print(f"\nNetwork created: {net}")
print(f"  - Nodes: {net.core_network.number_of_nodes()}")
print(f"  - Edges: {net.core_network.number_of_edges()}")
print(f"  - Layers: {len(net.layer_names)}")

# ============================================================================
# Example 1: Core (Aggregated) Visualization
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 1: Core (Aggregated) Ricci-Flow Visualization")
print("=" * 70)

print("\nVisualizing the aggregated core network with Ricci flow...")
print("This automatically computes Ricci flow and creates a layout")

try:
    fig1, ax1, positions1 = net.visualize_ricci_core(
        alpha=0.5,  # Standard Ollivier-Ricci parameter
        iterations=10,  # Number of flow iterations
        layout_type="mds",  # Use MDS layout
        dim=2,  # 2D visualization
        node_color_by="layer_overlap",  # Color by layer participation
        edge_color_by="curvature",  # Color edges by curvature
        figsize=(10, 8),
    )

    print(f"\n✓ Core visualization created")
    print(f"  - {len(positions1)} node positions computed")
    print(f"  - Layout type: MDS (geodesic distances)")
    print(f"  - Red edges = negative curvature (bottlenecks)")
    print(f"  - Blue edges = positive curvature (communities)")

    # Save figure
    fig1.savefig("/tmp/ricci_core_visualization.png", dpi=150, bbox_inches="tight")
    print(f"  - Saved to: /tmp/ricci_core_visualization.png")
    plt.close(fig1)

except Exception as e:
    print(f"\n✗ Error in core visualization: {e}")
    import traceback

    traceback.print_exc()

# ============================================================================
# Example 2: Per-Layer Visualization
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 2: Per-Layer Ricci-Flow Visualization")
print("=" * 70)

print("\nVisualizing each layer with shared coordinate system...")
print("Shared layout makes it easy to compare layer structures")

try:
    fig2, layer_positions = net.visualize_ricci_layers(
        layers=None,  # None means all layers
        alpha=0.5,
        iterations=10,
        layout_type="mds",
        share_layout=True,  # Use shared coordinates
        arrangement="grid",  # Grid of subplots
        figsize=(14, 6),
    )

    print(f"\n✓ Per-layer visualization created")
    print(f"  - {len(layer_positions)} layers visualized")
    for layer_id, positions in layer_positions.items():
        print(f"  - Layer '{layer_id}': {len(positions)} nodes")

    # Save figure
    fig2.savefig("/tmp/ricci_layers_visualization.png", dpi=150, bbox_inches="tight")
    print(f"  - Saved to: /tmp/ricci_layers_visualization.png")
    plt.close(fig2)

except Exception as e:
    print(f"\n✗ Error in per-layer visualization: {e}")
    import traceback

    traceback.print_exc()

# ============================================================================
# Example 3: Supra-Graph Visualization
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 3: Supra-Graph Ricci-Flow Visualization")
print("=" * 70)

print("\nVisualizing the full supra-graph (including inter-layer edges)...")
print("This shows both intra-layer and inter-layer connections")

try:
    fig3, ax3, positions3 = net.visualize_ricci_supra(
        alpha=0.5,
        iterations=10,
        layout_type="spring",  # Spring layout works well for supra-graphs
        dim=2,
        node_color_by="layer",  # Color nodes by layer
        edge_color_by="curvature",
        interlayer_alpha=0.2,  # Make inter-layer edges more transparent
        figsize=(12, 10),
    )

    print(f"\n✓ Supra-graph visualization created")
    print(f"  - {len(positions3)} node-layer pairs positioned")
    print(f"  - Solid edges = intra-layer connections")
    print(f"  - Dashed edges = inter-layer connections")

    # Save figure
    fig3.savefig("/tmp/ricci_supra_visualization.png", dpi=150, bbox_inches="tight")
    print(f"  - Saved to: /tmp/ricci_supra_visualization.png")
    plt.close(fig3)

except Exception as e:
    print(f"\n✗ Error in supra-graph visualization: {e}")
    import traceback

    traceback.print_exc()

# ============================================================================
# Example 4: 3D Supra-Graph Visualization
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE 4: 3D Supra-Graph with Layer Separation")
print("=" * 70)

print("\nVisualizing supra-graph in 3D with layers separated along z-axis...")

try:
    fig4, ax4, positions4 = net.visualize_ricci_supra(
        alpha=0.5,
        iterations=10,
        layout_type="spring",
        dim=3,  # 3D visualization
        layer_separation=2.0,  # Separate layers by 2 units
        node_color_by="layer",
        figsize=(12, 10),
    )

    print(f"\n✓ 3D supra-graph visualization created")
    print(f"  - {len(positions4)} node positions in 3D space")
    print(f"  - Layers separated along z-axis")

    # Save figure
    fig4.savefig("/tmp/ricci_supra_3d_visualization.png", dpi=150, bbox_inches="tight")
    print(f"  - Saved to: /tmp/ricci_supra_3d_visualization.png")
    plt.close(fig4)

except Exception as e:
    print(f"\n✗ Error in 3D supra-graph visualization: {e}")
    import traceback

    traceback.print_exc()

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(
    """
Ricci-Flow-Based Visualization Features:

1. CORE VISUALIZATION:
   • Shows aggregated network structure
   • Automatically computes Ricci flow
   • Edge colors indicate curvature (red=bottleneck, blue=community)
   • Node colors show layer participation

2. PER-LAYER VISUALIZATION:
   • Compare individual layer structures
   • Shared layout for easy comparison
   • Grid arrangement for side-by-side viewing

3. SUPRA-GRAPH VISUALIZATION:
   • Full multilayer structure including inter-layer edges
   • 2D or 3D layouts
   • Layer separation in 3D for hierarchical view

INTERPRETATION:
   • Red edges: Negative curvature → community boundaries/bottlenecks
   • Blue edges: Positive curvature → within-community connections
   • Edge width: Proportional to post-flow weight
   • Node size/color: Customizable (degree, curvature, layer overlap)

BEST PRACTICES:
   • Start with iterations=10 for quick preview
   • Use iterations=20-30 for publication quality
   • MDS layout best for distance preservation
   • Spring layout best for local structure
   • Try different alpha values (0.3-0.7) for different effects
"""
)

print("=" * 70)
print("Example completed successfully!")
print("=" * 70)
print("\nGenerated visualizations:")
print("  - /tmp/ricci_core_visualization.png")
print("  - /tmp/ricci_layers_visualization.png")
print("  - /tmp/ricci_supra_visualization.png")
print("  - /tmp/ricci_supra_3d_visualization.png")
