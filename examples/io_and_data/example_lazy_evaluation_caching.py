"""
Cache expensive multilayer computations using the lazy-evaluation API.

Demonstrates `CacheManager.cached_method` on a simple multilayer network so the
first centrality call runs once and subsequent calls are instant. Prerequisite:
py3plex installed; no optional extras needed.
"""

from __future__ import annotations

from typing import Any, Dict

from py3plex.algorithms.centrality_toolkit import multilayer_betweenness_centrality
from py3plex.core.lazy_evaluation import CacheManager
from py3plex.core.multinet import multi_layer_network


def build_sample_network() -> multi_layer_network:
    """Create a tiny undirected multilayer network for caching demos."""
    net = multi_layer_network(network_type="multilayer", directed=False)
    net.add_nodes(
        [
            {"source": "A", "type": "social"},
            {"source": "B", "type": "social"},
            {"source": "C", "type": "social"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
            },
        ]
    )
    return net


def main() -> int:
    """Demonstrate lazy evaluation and caching."""
    print("=== Lazy Evaluation and Caching Demo ===\n")

    cache = CacheManager(max_size=10)

    class NetworkAnalyzer:
        """Wrap network methods that should be cached."""

        def __init__(self, network: multi_layer_network):
            self.network = network
            self._cache_manager = cache

        @cache.cached_method("betweenness")
        def compute_betweenness(self) -> Dict[Any, float]:
            print("  Computing betweenness centrality (expensive operation)...")
            return multilayer_betweenness_centrality(self.network)

    analyzer = NetworkAnalyzer(build_sample_network())

    print("First call:")
    result1 = analyzer.compute_betweenness()
    print(f"  Result: {len(result1)} nodes processed")

    print("\nSecond call (cached):")
    result2 = analyzer.compute_betweenness()
    print(f"  Result: {len(result2)} nodes processed")

    print(f"\nCache statistics: {cache.cache_info()}")
    print("Cache hit! Second call was instant.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
