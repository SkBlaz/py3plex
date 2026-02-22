"""
Multilayer Network Entanglement Analysis

Teaches:
- Compute entanglement metrics for multilayer networks
- Analyze how layers are interconnected and interdependent
- Interpret entanglement intensity, homogeneity, and layer-specific metrics

Background:
Entanglement measures the degree of interconnection between layers in a
multilayer network. Higher entanglement indicates more interdependency
between layers. This is useful for understanding multilayer structure.

Citation:
By Benjamin Renoust and Blaz Skrlj, 2019

Prerequisites:
- Dataset: multiL.txt (from py3plex datasets)

SKIP_CI: external_deps - Requires specific dataset files
"""

from py3plex.core import multinet
from py3plex.algorithms.multilayer_algorithms.entanglement import compute_entanglement_analysis
from py3plex.utils import get_dataset_path

print("=" * 70)
print("MULTILAYER NETWORK ENTANGLEMENT ANALYSIS")
print("=" * 70)

# ===============================================================================
# Load and analyze multilayer network
# ===============================================================================

print("\n[1] Loading multilayer network...")
print("-" * 70)
multilayer_network = multinet.multi_layer_network().load_network(
    get_dataset_path("multiL.txt"), directed=True, input_type="multiedgelist")

print("Network loaded successfully!")
print("\nNetwork statistics:")
multilayer_network.basic_stats()

# ===============================================================================
# Compute entanglement analysis
# ===============================================================================

print("\n[2] Computing entanglement analysis...")
print("-" * 70)

analysis = compute_entanglement_analysis(multilayer_network)

print(f"\nEntanglement analysis complete!")
print(f"Found {len(analysis)} connected component(s) of layers\n")

# ===============================================================================
# Display results for each component
# ===============================================================================

for i, block in enumerate(analysis):
    print("=" * 70)
    print(f"Component {i + 1} of {len(analysis)}")
    print("=" * 70)
    
    layer_labels = block['Layer entanglement'].keys()
    print(f"Covering layers: {list(layer_labels)}")
    print()
    
    print(f"Entanglement intensity: {block['Entanglement intensity']:.4f}")
    print(f"  (Measures overall degree of layer interconnection)")
    print()
    
    print("Layer entanglement (per-layer contribution):")
    for layer, value in block['Layer entanglement'].items():
        print(f"  {layer}: {value:.4f}")
    print()
    
    print(f"Entanglement homogeneity: {block['Entanglement homogeneity']:.4f}")
    print(f"  (How evenly distributed entanglement is across layers)")
    print()
    
    print(f"Normalized homogeneity: {block['Normalized homogeneity']:.4f}")
    print(f"  (Homogeneity normalized by number of layers)")

print("\n" + "=" * 70)
print("ENTANGLEMENT ANALYSIS COMPLETE")
print("=" * 70)
print("\nKey takeaways:")
print("  [OK] Entanglement measures layer interdependency in multilayer networks")
print("  [OK] Higher intensity = more interconnected layers")
print("  [OK] Higher homogeneity = more evenly distributed connections")
print("  [OK] Useful for understanding multilayer network structure")

