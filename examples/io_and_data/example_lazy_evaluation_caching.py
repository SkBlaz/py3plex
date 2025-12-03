"""
Example demonstrating lazy evaluation and caching in py3plex.

This example shows how to use the CacheManager for efficient computation
caching in multilayer network analysis.
"""

from py3plex.core.multinet import multi_layer_network
from py3plex.core.lazy_evaluation import CacheManager
from py3plex.algorithms.centrality_toolkit import multilayer_betweenness_centrality


def main():
    """Demonstrate lazy evaluation and caching."""
    print("=== Lazy Evaluation and Caching Demo ===\n")
    
    # Create a cache manager with LRU eviction
    cache = CacheManager(max_size=10)
    
    # Define a class with cached methods
    class NetworkAnalyzer:
        def __init__(self, network):
            self.network = network
            self._cache_manager = cache
        
        @cache.cached_method('centrality')
        def compute_centrality(self, method='degree'):
            print(f"  Computing {method} centrality (expensive operation)...")
            if method == 'degree':
                return multilayer_betweenness_centrality(self.network)
            return {}
    
    # Create a simple network
    # Using network_type='multilayer' because this is a general multilayer network
    # where each layer can have different nodes. For networks where all layers
    # share the same nodes with different relationship types, use 'multiplex'.
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
    
    # First call - computes and caches result
    print("First call:")
    result1 = analyzer.compute_centrality('degree')
    print(f"  Result: {len(result1)} nodes processed")
    
    # Second call - uses cached result (instant)
    print("\nSecond call (cached):")
    result2 = analyzer.compute_centrality('degree')
    print(f"  Result: {len(result2)} nodes processed")
    
    # Check cache statistics
    print(f"\nCache statistics: {cache.cache_info()}")
    print("Cache hit! Second call was instant.\n")


if __name__ == "__main__":
    main()
