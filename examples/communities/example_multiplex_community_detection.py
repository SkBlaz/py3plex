"""
Multiplex Community Detection Example

This example demonstrates community detection using two approaches:
1. Pipeline-based approach with chaining (simpler, more elegant)
2. Traditional approach for networks loaded from files

SKIP_CI: external_deps - Requires specific dataset files (simple_multiplex.edgelist)
"""

from py3plex.pipeline import Pipeline, LoadStep, LouvainCommunity
from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.core import multinet
from py3plex.utils import get_dataset_path

# ============================================================================
# Approach 1: Pipeline-based community detection (elegant chaining)
# ============================================================================
print("=" * 60)
print("Pipeline-based community detection (chaining)")
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
# Approach 2: Traditional approach for file-based networks
# ============================================================================
print("\n" + "=" * 60)
print("Traditional approach (file-based network)")
print("=" * 60)

comNet = multinet.multi_layer_network().load_network(
    get_dataset_path('simple_multiplex.edgelist'),
    directed=False,
    input_type='multiplex_edges')
comNet.load_layer_name_mapping(get_dataset_path('simple_multiplex.txt'))
comNet.basic_stats()
part = cw.louvain_communities(comNet)
print(f"Partition: {part}")
