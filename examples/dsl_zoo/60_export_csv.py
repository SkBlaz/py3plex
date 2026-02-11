"""
60. Export to CSV

FAST: <1s runtime
Dependencies: py3plex (core)

Demonstrates .to_csv() for exporting results to CSV file.
"""
from py3plex.core import multinet
from py3plex.dsl import Q, L
import tempfile
import os

# Create small multilayer network
net = multinet.multi_layer_network(directed=False)
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Carol', 'type': 'social'},
])
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
])

# DSL: Query and export to CSV
result = (
    Q.nodes()
     .compute("degree", "betweenness_centrality")
     .execute(net)
)

# Export to temporary CSV file
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
    csv_path = f.name

result.to_csv(csv_path, index=False)
print(f"Exported to: {csv_path}")

# Read and display the CSV content
with open(csv_path, 'r') as f:
    print("\nCSV content:")
    print("=" * 60)
    print(f.read())

# Clean up
os.unlink(csv_path)
