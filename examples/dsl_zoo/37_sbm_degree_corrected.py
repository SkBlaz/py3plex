"""SBM: Degree-corrected SBM for heterogeneous networks.

This example shows how to use DC-SBM to handle networks with
heterogeneous degree distributions within communities.
"""

from py3plex.core import multinet
from py3plex.algorithms.community_detection import sbm_fit
import numpy as np

# Create network with varying degrees within blocks
np.random.seed(43)
net = multinet.multi_layer_network(directed=False)

nodes = [f'N{i}' for i in range(40)]
for node in nodes:
    net.add_node(node, layer='network')

# Generate edges with block structure AND degree heterogeneity
# Block 0: nodes 0-19 (some hubs, some low-degree)
# Block 1: nodes 20-39 (similar structure)
node_propensities = np.random.gamma(2, 0.5, 40)  # Heterogeneous degrees

for i in range(40):
    for j in range(i+1, 40):
        # Within-block: higher probability
        same_block = (i < 20) == (j < 20)
        base_p = 0.3 if same_block else 0.03
        
        # Modulate by node propensities (creates hubs)
        p = base_p * node_propensities[i] * node_propensities[j] / 4.0
        p = min(p, 0.9)  # Cap probability
        
        if np.random.rand() < p:
            net.add_edge(nodes[i], nodes[j], layer_src='network', layer_dst='network')

# Compare standard SBM vs DC-SBM
print("Fitting standard SBM...")
partition_sbm = sbm_fit(
    net,
    n_blocks=2,
    algorithm="sbm",  # Standard SBM (no degree correction)
    seed=43
)

print("\nFitting degree-corrected SBM...")
partition_dcsbm, model = sbm_fit(
    net,
    n_blocks=2,
    algorithm="dc_sbm",  # Degree-corrected SBM
    return_model=True,
    seed=43
)

# Check degree correction: DC-SBM should handle hubs better
print(f"\nStandard SBM communities: {len(set(partition_sbm.values()))}")
print(f"DC-SBM communities: {len(set(partition_dcsbm.values()))}")

# Print degree parameters (only DC-SBM has these)
if hasattr(model, 'degree_params_'):
    print(f"\nDegree parameters (DC-SBM):")
    print(f"  Range: [{model.degree_params_.min():.3f}, {model.degree_params_.max():.3f}]")
    print(f"  Mean: {model.degree_params_.mean():.3f}")

# Check convergence
if hasattr(model, 'converged_'):
    print(f"\nConvergence status: {model.converged_}")
    print(f"Iterations: {model.n_iter_}")
    print(f"Final ELBO: {model.elbo_history_[-1]:.2f}")
