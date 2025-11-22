"""
Demonstration of new py3plex features: lazy evaluation, caching, schema validation,
immutable mode, centrality toolkit, community comparison, and more.

This example shows how to use the new features added to py3plex.
"""

from py3plex.core.multinet import multi_layer_network
from py3plex.core.lazy_evaluation import CacheManager
from py3plex.core.schema_validation import NetworkSchema, FieldValidator, ValidationError
from py3plex.core.immutable import make_immutable
from py3plex.algorithms.centrality_toolkit import (
    multilayer_pagerank,
    multilayer_betweenness_centrality,
    versatility_score,
)
from py3plex.algorithms.advanced_random_generators import multilayer_erdos_renyi
from py3plex.algorithms.layer_similarity import jaccard_layer_similarity, layer_correlation_matrix
from py3plex.algorithms.statistical_report import generate_statistical_report


def demo_lazy_evaluation_and_caching():
    """Demonstrate lazy evaluation and caching."""
    print("\n=== Lazy Evaluation and Caching Demo ===")
    
    # Create a cache manager
    cache = CacheManager(max_size=10)
    
    # Define a class with cached methods
    class NetworkAnalyzer:
        def __init__(self, network):
            self.network = network
            self._cache_manager = cache
        
        @cache.cached_method('centrality')
        def compute_centrality(self, method='degree'):
            print(f"  Computing {method} centrality (expensive)...")
            if method == 'degree':
                return multilayer_betweenness_centrality(self.network)
            return {}
    
    # Create network
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
    ])
    
    analyzer = NetworkAnalyzer(net)
    
    # First call - computes
    print("First call:")
    result1 = analyzer.compute_centrality('degree')
    
    # Second call - uses cache
    print("Second call (cached):")
    result2 = analyzer.compute_centrality('degree')
    
    print(f"Cache info: {cache.cache_info()}")


def demo_schema_validation():
    """Demonstrate schema validation."""
    print("\n=== Schema Validation Demo ===")
    
    # Create a schema
    schema = NetworkSchema(strict=False)
    schema.node_schema.add_field('weight', FieldValidator(float, required=True, min_value=0))
    schema.layer_schema.set_allowed_layers(['social', 'biological'])
    
    # Create network
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
    ])
    
    # Validate
    try:
        is_valid = schema.validate_network(net)
        print(f"Network validation result: {is_valid}")
    except ValidationError as e:
        print(f"Validation error: {e}")


def demo_immutable_mode():
    """Demonstrate immutable network mode."""
    print("\n=== Immutable Mode Demo ===")
    
    # Create network
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
    ])
    
    # Make immutable with copy-on-write
    immutable = make_immutable(net, copy_on_write=True)
    
    print(f"Original nodes: {immutable.number_of_nodes()}")
    print("Network is now immutable - modifications create copies")
    
    # Read operations work fine
    nodes = immutable.get_nodes()
    print(f"Can read nodes: {len(list(nodes))}")


def demo_centrality_toolkit():
    """Demonstrate multilayer centrality algorithms."""
    print("\n=== Centrality Toolkit Demo ===")
    
    # Create a simple multilayer network
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2'},
    ])
    
    # Compute centrality
    try:
        betweenness = multilayer_betweenness_centrality(net)
        print(f"Betweenness centrality computed: {len(betweenness)} nodes")
        
        # Show top 3 nodes
        top_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:3]
        print("Top 3 nodes by betweenness:")
        for node, score in top_nodes:
            print(f"  {node}: {score:.4f}")
        
        # Compute versatility
        versatility = versatility_score(betweenness)
        print(f"\nVersatility scores: {versatility}")
    except Exception as e:
        print(f"Centrality computation: {e}")


def demo_random_generators():
    """Demonstrate random graph generators."""
    print("\n=== Random Graph Generators Demo ===")
    
    # Generate multilayer ER network
    G = multilayer_erdos_renyi(n=20, p=0.2, num_layers=3, interlayer_prob=0.1, seed=42)
    
    print(f"Generated multilayer ER network:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    
    # Convert to py3plex network
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.load_network(G, input_type='nx')
    
    print(f"Converted to py3plex network:")
    print(f"  {net}")


def demo_layer_similarity():
    """Demonstrate layer similarity metrics."""
    print("\n=== Layer Similarity Demo ===")
    
    # Create network with multiple layers
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'L1'},
        {'source': 'B', 'type': 'L1'},
        {'source': 'C', 'type': 'L1'},
        {'source': 'A', 'type': 'L2'},
        {'source': 'B', 'type': 'L2'},
        {'source': 'C', 'type': 'L2'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        {'source': 'A', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
    ])
    
    # Compute Jaccard similarity
    try:
        sim = jaccard_layer_similarity(net, 'L1', 'L2', element='nodes')
        print(f"Jaccard node similarity (L1, L2): {sim:.4f}")
        
        # Compute correlation matrix
        sim_matrix, layers = layer_correlation_matrix(net, method='jaccard')
        print(f"\nLayer correlation matrix shape: {sim_matrix.shape}")
        print(f"Layers: {layers}")
    except Exception as e:
        print(f"Layer similarity: {e}")


def demo_statistical_report():
    """Demonstrate statistical report generation."""
    print("\n=== Statistical Report Demo ===")
    
    # Create network
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2'},
    ])
    
    # Generate report
    report = generate_statistical_report(
        net,
        output_format='text',
        include_sections=['basic', 'degree', 'layers']
    )
    
    print(report[:500] + "...")  # Print first 500 chars


if __name__ == "__main__":
    print("=" * 70)
    print("Py3plex New Features Demonstration")
    print("=" * 70)
    
    demo_lazy_evaluation_and_caching()
    demo_schema_validation()
    demo_immutable_mode()
    demo_centrality_toolkit()
    demo_random_generators()
    demo_layer_similarity()
    demo_statistical_report()
    
    print("\n" + "=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)
