"""
Multiplex Community Detection Example

This example demonstrates community detection using multiple approaches:
1. Pipeline-based approach with chaining (simpler, more elegant)
2. DSL-based approach for declarative queries
3. Interoperability: Pipeline network -> DSL analysis

The key point is that all py3plex objects are interoperable - you can generate
a network with Pipeline and analyze it with DSL, or vice versa.

SKIP_CI: external_deps - Requires specific dataset files (simple_multiplex.edgelist)
"""

from py3plex.pipeline import Pipeline, LoadStep, LouvainCommunity
from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.core import multinet
from py3plex.dsl import execute_query, detect_communities
from py3plex.utils import get_dataset_path

# ============================================================================
# Approach 1: Pipeline-based community detection (elegant chaining)
# ============================================================================
print("=" * 60)
print("Approach 1: Pipeline-based community detection (chaining)")
print("=" * 60)

# Using Pipeline for elegant chaining: generate -> detect communities
pipe = Pipeline([
    ("generate", LoadStep(generator='random_er', n=50, l=8, p=0.05)),
    ("community", LouvainCommunity()),
])

result = pipe.run()
print(f"Communities found: {result['num_communities']}")
print(f"Sample assignments: {dict(list(result['communities'].items())[:5])}")

# ============================================================================
# Approach 2: DSL-based community detection (declarative)
# ============================================================================
print("\n" + "=" * 60)
print("Approach 2: DSL-based community detection (declarative)")
print("=" * 60)

# Generate network and use DSL for community detection
network = LoadStep(generator='random_er', n=30, l=3, p=0.1).transform(None)
dsl_result = execute_query(network, 'SELECT nodes COMPUTE communities')
print(f"DSL query: SELECT nodes COMPUTE communities")
print(f"Communities found: {len(set(dsl_result['computed']['communities'].values()))}")

# ============================================================================
# Approach 3: Interoperability - Pipeline + DSL working together
# ============================================================================
print("\n" + "=" * 60)
print("Approach 3: Interoperability - Pipeline network -> DSL analysis")
print("=" * 60)

# Generate network via Pipeline step (returns multi_layer_network)
generated_net = LoadStep(generator='random_er', n=40, l=4, p=0.08).transform(None)

# Use DSL to analyze the same network (objects are interoperable)
dsl_analysis = detect_communities(generated_net)
print(f"Network has {dsl_analysis['num_communities']} communities")
print(f"Biggest community: {dsl_analysis['biggest_community']}")

# Also run traditional method on same network
traditional_part = cw.louvain_communities(generated_net)
print(f"Traditional Louvain partitions: {len(set(traditional_part.values()))}")

# ============================================================================
# Approach 4: Traditional approach for file-based networks
# ============================================================================
print("\n" + "=" * 60)
print("Approach 4: Traditional approach (file-based network)")
print("=" * 60)

comNet = multinet.multi_layer_network().load_network(
    get_dataset_path('simple_multiplex.edgelist'),
    directed=False,
    input_type='multiplex_edges')
comNet.load_layer_name_mapping(get_dataset_path('simple_multiplex.txt'))
comNet.basic_stats()
part = cw.louvain_communities(comNet)
print(f"Partition: {part}")

print("\n" + "=" * 60)
print("Summary: All approaches use interoperable multi_layer_network objects")
print("=" * 60)
