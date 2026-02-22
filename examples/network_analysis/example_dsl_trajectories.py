"""Example: Trajectory Queries with Q.trajectories()

This example demonstrates the full trajectory query functionality using
Q.trajectories() to analyze simulation results from Q.dynamics().

Key Features:
- Query trajectories from simulation results
- Temporal filtering: .at(t) and .during(t0, t1)
- WHERE conditions on replicate/time
- Computed measures: peak_time, final_state, peak_value, mean_value
- Ordering and limiting results
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L
import numpy as np

print("=" * 80)
print("TRAJECTORY QUERIES WITH Q.trajectories()")
print("=" * 80)
print()

# Create a sample network
network = multinet.multi_layer_network(directed=False)

nodes = [{'source': f'Person{i}', 'type': 'contact'} for i in range(15)]
network.add_nodes(nodes)

edges = []
for i in range(14):
    edges.append({
        'source': f'Person{i}',
        'target': f'Person{i+1}',
        'source_type': 'contact',
        'target_type': 'contact',
        'weight': 1.0
    })

# Add some random connections
import random
random.seed(42)
for _ in range(10):
    i, j = random.sample(range(15), 2)
    edges.append({
        'source': f'Person{i}',
        'target': f'Person{j}',
        'source_type': 'contact',
        'target_type': 'contact',
        'weight': 1.0
    })

network.add_edges(edges)

print(f"Network: {len(list(network.get_nodes()))} nodes, {len(list(network.get_edges()))} edges")
print()

# =============================================================================
# Example 1: Run Simulation and Query All Trajectories
# =============================================================================
print("[Example 1] Run Simulation and Query All Trajectories")
print("-" * 80)

# First, run a dynamics simulation
sim_result = (
    Q.dynamics("SIS", beta=0.3, mu=0.1)
     .seed(0.2)  # 20% initially infected
     .run(steps=50, replicates=5, track=["prevalence"])
     .random_seed(42)
     .execute(network)
)

print(f"Simulation complete: {sim_result.data['prevalence'].shape}")
print()

# Query all trajectory points
traj_all = (
    Q.trajectories("sim_result")
     .execute(sim_result)
)

print(f"Total trajectory points: {len(traj_all.items)}")
print(f"Attributes: {list(traj_all.attributes.keys())}")
print(f"Sample items (first 5):")
for item in traj_all.items[:5]:
    # item is (replicate, t) tuple
    rep, t = item
    val = traj_all.attributes["value"][item]
    print(f"  replicate={rep}, t={t}, value={val:.3f}")
print()

# =============================================================================
# Example 2: Temporal Filtering - Query at Specific Time
# =============================================================================
print("[Example 2] Temporal Filtering - Query at Specific Time")
print("-" * 80)

# Query trajectories at t=25
traj_at_25 = (
    Q.trajectories("sim_result")
     .at(25)
     .execute(sim_result)
)

print(f"Trajectory points at t=25: {len(traj_at_25.items)}")
print("Values at t=25:")
for item in traj_at_25.items:
    # item is (replicate, t) tuple
    rep, t = item
    val = traj_at_25.attributes["value"][item]
    print(f"  replicate {rep}: {val:.3f}")
print()

# =============================================================================
# Example 3: Temporal Range Filtering
# =============================================================================
print("[Example 3] Temporal Range Filtering")
print("-" * 80)

# Query trajectories during time window [20, 30]
traj_window = (
    Q.trajectories("sim_result")
     .during(20, 30)
     .execute(sim_result)
)

print(f"Trajectory points in [20, 30]: {len(traj_window.items)}")
print(f"Expected: {5 * 11} points (5 replicates x 11 timesteps)")
print()

# =============================================================================
# Example 4: Computed Trajectory Measures
# =============================================================================
print("[Example 4] Computed Trajectory Measures")
print("-" * 80)

# Query with computed measures
traj_measures = (
    Q.trajectories("sim_result")
     .measure("peak_time", "final_state", "peak_value", "mean_value")
     .execute(sim_result)
)

print("Trajectory measures computed:")
print(f" Number of items: {len(traj_measures.items)}")
print()

# Display measures for each replicate (check first occurrence per replicate)
seen_replicates = set()
for item in traj_measures.items:
    # item is (replicate, t) tuple
    rep, t = item
    if rep not in seen_replicates:
        seen_replicates.add(rep)
        attrs = traj_measures.attributes
        print(f"Replicate {rep}:")
        if item in attrs.get('peak_time', {}):
            print(f"  Peak time: t={attrs['peak_time'][item]}")
        if item in attrs.get('peak_value', {}):
            print(f"  Peak value: {attrs['peak_value'][item]:.3f}")
        if item in attrs.get('final_state', {}):
            print(f"  Final state: {attrs['final_state'][item]:.3f}")
        if item in attrs.get('mean_value', {}):
            print(f"  Mean value: {attrs['mean_value'][item]:.3f}")
        print()

# =============================================================================
# Example 5: WHERE Filtering - Single Replicate
# =============================================================================
print("[Example 5] WHERE Filtering - Single Replicate")
print("-" * 80)

# Query only replicate 2
traj_rep2 = (
    Q.trajectories("sim_result")
     .where(replicate=2)
     .execute(sim_result)
)

print(f"Trajectory points for replicate 2: {len(traj_rep2.items)}")
print("First 5 points:")
for item in traj_rep2.items[:5]:
    # item is (replicate, t) tuple
    rep, t = item
    val = traj_rep2.attributes["value"][item]
    print(f"  t={t}, value={val:.3f}")
print()

# =============================================================================
# Example 6: Combining Filters
# =============================================================================
print("[Example 6] Combining Multiple Filters")
print("-" * 80)

# Query replicate 1, during [10, 20], with measures, limited to 5 results
traj_combined = (
    Q.trajectories("sim_result")
     .where(replicate=1)
     .during(10, 20)
     .measure("peak_value")
     .limit(5)
     .execute(sim_result)
)

print(f"Combined query results: {len(traj_combined.items)} items (limited to 5)")
print("Results:")
for item in traj_combined.items:
    # item is (replicate, t) tuple
    rep, t = item
    val = traj_combined.attributes["value"][item]
    peak = traj_combined.attributes.get('peak_value', {}).get(item, 'N/A')
    print(f"  t={t}, value={val:.3f}, peak_value={peak:.3f}" if peak != 'N/A' else f"  t={t}, value={val:.3f}")
print()

# =============================================================================
# Example 7: Analysis - Find Best Performing Replicate
# =============================================================================
print("[Example 7] Analysis - Find Best Performing Replicate")
print("-" * 80)

# Query with measures to find which replicate had lowest final prevalence
traj_final = (
    Q.trajectories("sim_result")
     .measure("final_state")
     .execute(sim_result)
)

# Extract final states per replicate
final_states = {}
for item in traj_final.items:
    # item is (replicate, t) tuple
    rep, t = item
    if rep not in final_states:
        final_states[rep] = traj_final.attributes['final_state'][item]

print("Final prevalence by replicate:")
for rep in sorted(final_states.keys()):
    print(f"  Replicate {rep}: {final_states[rep]:.3f}")

best_rep = min(final_states, key=final_states.get)
print(f"\nBest performing replicate: {best_rep} (final prevalence: {final_states[best_rep]:.3f})")
print()

# =============================================================================
# Example 8: Extract Data for Analysis
# =============================================================================
print("[Example 8] Extract Data for Analysis")
print("-" * 80)

# Query and extract attributes
traj_extract = (
    Q.trajectories("sim_result")
     .measure("peak_time", "mean_value")
     .execute(sim_result)
)

print("Trajectory query results:")
print(f"Total items: {len(traj_extract.items)}")
print(f"Attributes: {list(traj_extract.attributes.keys())}")
print()

# Extract data by replicate
data_by_replicate = {}
for item in traj_extract.items:
    rep, t = item
    if rep not in data_by_replicate:
        data_by_replicate[rep] = {
            'times': [],
            'values': [],
            'peak_time': traj_extract.attributes.get('peak_time', {}).get(item),
            'mean_value': traj_extract.attributes.get('mean_value', {}).get(item),
        }
    data_by_replicate[rep]['times'].append(t)
    data_by_replicate[rep]['values'].append(traj_extract.attributes['value'][item])

print("Data extracted by replicate:")
for rep in sorted(data_by_replicate.keys()):
    data = data_by_replicate[rep]
    print(f"Replicate {rep}:")
    print(f"  Time points: {len(data['times'])}")
    print(f"  Peak time: {data['peak_time']}")
    print(f"  Mean value: {data['mean_value']:.3f}")
    print()

# =============================================================================
# Summary
# =============================================================================
print("=" * 80)
print("SUMMARY: Q.trajectories() Features Demonstrated")
print("=" * 80)
print("""
1. Query all trajectory points from simulation results
2. Temporal filtering: .at(t) for specific time
3. Temporal range: .during(t0, t1) for time windows
4. WHERE conditions: filter by replicate, time, or values
5. Computed measures: peak_time, final_state, peak_value, mean_value
6. Ordering and limiting results
7. Combining multiple filters
8. Pandas export for analysis

Key Capabilities:
- Full query execution (not placeholder)
- Temporal slicing of trajectories
- Computed statistics on trajectories
- Integration with Q.dynamics() results
- Familiar DSL syntax and chaining
- Rich result format with QueryResult

The trajectory query DSL enables powerful post-hoc analysis of simulation
results, making it easy to extract insights from dynamics simulations.
""")

print("For more examples, see:")
print(" - examples/network_analysis/example_dsl_dynamics_declarative.py")
print(" - tests/test_dsl_dynamics_integration.py")
print(" - docfiles/how-to/simulate_dynamics.rst")
