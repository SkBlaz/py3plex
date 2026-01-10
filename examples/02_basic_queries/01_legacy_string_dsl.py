"""
Basic queries: Legacy string DSL (backward compatibility only).

Demonstrates:
- String-based query syntax (legacy)
- Simple node selection

Note: Use DSL v2 (Q.nodes()) for new code. This is for backward compatibility.
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.dsl_legacy import execute_query

# 1. Load network
network = load_aarhus_cs()

# 2. Run legacy string query
result = execute_query(network, 'SELECT nodes WHERE layer="lunch"')

# 3. Print result
print(f"Found {result['count']} nodes in lunch layer")
print(f"Sample nodes: {result['nodes'][:5]}")
