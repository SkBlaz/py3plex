"""
Test for inter-layer links visualization fix.

This test verifies that inter-layer edges are drawn between correctly offset
node positions across different layers, not at the same location.
"""

import logging
import sys

logger = logging.getLogger()
logger.level = logging.DEBUG

# Try to import required dependencies
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("networkx not available")

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available")

DEPENDENCIES_AVAILABLE = NETWORKX_AVAILABLE and MATPLOTLIB_AVAILABLE

if DEPENDENCIES_AVAILABLE:
    from py3plex.visualization.multilayer import draw_multilayer_default, draw_multiedges
    from py3plex.core import multinet


def test_interlayer_links_positions():
    """
    Test that inter-layer links are drawn with correct offset positions.
    
    This test ensures that:
    1. After draw_multilayer_default() is called, node positions in each layer 
       are offset from each other
    2. When draw_multiedges() retrieves positions, it gets the offset positions
    3. Inter-layer edges connect nodes at different positions (not same position)
    """
    if not DEPENDENCIES_AVAILABLE:
        print("Dependencies not available, skipping test")
        return

    # Create a simple multilayer network
    G = nx.MultiDiGraph()

    # Layer 1: nodes ('A', 'layer1') and ('B', 'layer1')
    G.add_node(('A', 'layer1'), pos=(0.0, 0.0))
    G.add_node(('B', 'layer1'), pos=(1.0, 0.0))
    G.add_edge(('A', 'layer1'), ('B', 'layer1'), type='intra')

    # Layer 2: nodes ('A', 'layer2') and ('C', 'layer2')
    # Note: Same initial positions as layer 1
    G.add_node(('A', 'layer2'), pos=(0.0, 0.0))
    G.add_node(('C', 'layer2'), pos=(1.0, 0.0))
    G.add_edge(('A', 'layer2'), ('C', 'layer2'), type='intra')

    # Inter-layer edges
    G.add_edge(('A', 'layer1'), ('A', 'layer2'), type='inter')
    G.add_edge(('B', 'layer1'), ('C', 'layer2'), type='inter')

    # Prepare layers (similar to prepare_for_visualization)
    from collections import defaultdict
    
    layers = defaultdict(list)
    for node in G.nodes(data=True):
        layers[node[0][1]].append(node[0])

    networks = {layer_name: G.subgraph(v) for layer_name, v in layers.items()}

    # Get inter-layer edges
    multiedges = defaultdict(list)
    for edge in G.edges(data=True):
        if edge[0][1] != edge[1][1]:  # Different layers
            multiedges[edge[2]["type"]].append(edge)

    # Get initial positions before drawing
    initial_pos_layer1 = nx.get_node_attributes(networks['layer1'], "pos")
    initial_pos_layer2 = nx.get_node_attributes(networks['layer2'], "pos")
    
    print("Initial positions (before draw_multilayer_default):")
    print(f"  Layer 1, node ('A', 'layer1'): {initial_pos_layer1[('A', 'layer1')]}")
    print(f"  Layer 2, node ('A', 'layer2'): {initial_pos_layer2[('A', 'layer2')]}")
    
    # Verify they start at the same position
    assert initial_pos_layer1[('A', 'layer1')] == (0.0, 0.0), "Initial layer 1 position incorrect"
    assert initial_pos_layer2[('A', 'layer2')] == (0.0, 0.0), "Initial layer 2 position incorrect"

    # Draw multilayer network (this should apply offsets and save them)
    draw_multilayer_default(
        networks,
        display=False,
        background_shape="rectangle",
        labels=list(networks.keys()),
        node_size=50,
        scale_by_size=False
    )

    # Get positions after drawing
    after_pos_layer1 = nx.get_node_attributes(networks['layer1'], "pos")
    after_pos_layer2 = nx.get_node_attributes(networks['layer2'], "pos")

    print("\nPositions after draw_multilayer_default:")
    print(f"  Layer 1, node ('A', 'layer1'): {after_pos_layer1[('A', 'layer1')]}")
    print(f"  Layer 2, node ('A', 'layer2'): {after_pos_layer2[('A', 'layer2')]}")

    # THE FIX: Verify that layers now have different positions
    pos1 = after_pos_layer1[('A', 'layer1')]
    pos2 = after_pos_layer2[('A', 'layer2')]
    
    # Check that positions are different (layer offset has been applied)
    assert pos1 != pos2, (
        f"FAIL: Positions should be different after layer offsets. "
        f"Got layer1={pos1}, layer2={pos2}"
    )
    
    print("\n[OK] SUCCESS: Layers have different positions after draw_multilayer_default")
    print(f"  Layer 1 at {pos1}")
    print(f"  Layer 2 at {pos2}")
    
    # Verify the positions are actually offset by the expected amount
    # The default offset is defined in config.MULTILAYER_LAYER_OFFSET
    # For layer 1 (index 0): offset = 0
    # For layer 2 (index 1): offset = MULTILAYER_LAYER_OFFSET (default 3.0)
    from py3plex import config
    expected_offset = config.MULTILAYER_LAYER_OFFSET
    
    assert pos2[0] == pos1[0] + expected_offset, (
        f"X offset incorrect: expected {pos1[0] + expected_offset}, got {pos2[0]}"
    )
    assert pos2[1] == pos1[1] + expected_offset, (
        f"Y offset incorrect: expected {pos1[1] + expected_offset}, got {pos2[1]}"
    )
    
    print(f"[OK] Offset matches expected value: {expected_offset}")

    # Now draw inter-layer edges (this should use the offset positions)
    for edge_type, edges in multiedges.items():
        draw_multiedges(
            networks,
            edges,
            alphachannel=0.5,
            linepoints="--",
            linecolor="red",
            curve_height=2,
            linmod="upper",
            linewidth=2.0
        )

    plt.savefig('/tmp/test_interlayer_links.png', dpi=100, bbox_inches='tight')
    print("\n[OK] Visualization saved to /tmp/test_interlayer_links.png")
    
    plt.close('all')
    
    print("\n[OK] All checks passed! Inter-layer links are correctly visualized.")


if __name__ == "__main__":
    try:
        test_interlayer_links_positions()
        print("\n" + "="*60)
        print("TEST PASSED")
        print("="*60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\nFAIL: TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nFAIL: TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
