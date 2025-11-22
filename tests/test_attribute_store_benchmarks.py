"""
Benchmark tests comparing AttributeStore (Polars) vs NetworkX performance.

This module benchmarks the performance improvements from using Polars-based
attribute storage compared to direct NetworkX graph access.
"""

import pytest
import networkx as nx
from py3plex.core.attribute_store import AttributeStore


class TestAttributeStoreBenchmarks:
    """Benchmark AttributeStore vs NetworkX operations."""
    
    @pytest.fixture
    def sample_nodes(self):
        """Generate sample nodes for benchmarking."""
        nodes = []
        for i in range(1000):
            layer = f"layer{i % 10}"
            nodes.append({
                'node_id': f'node_{i}',
                'layer': layer,
                'weight': i * 0.1,
                'label': f'Node {i}'
            })
        return nodes
    
    @pytest.fixture
    def sample_edges(self):
        """Generate sample edges for benchmarking."""
        edges = []
        for i in range(2000):
            source_layer = f"layer{i % 10}"
            target_layer = f"layer{(i + 1) % 10}"
            edges.append({
                'source_id': f'node_{i % 1000}',
                'source_layer': source_layer,
                'target_id': f'node_{(i + 1) % 1000}',
                'target_layer': target_layer,
                'weight': i * 0.1,
                'edge_type': 'default'
            })
        return edges
    
    @pytest.fixture
    def networkx_graph(self, sample_nodes, sample_edges):
        """Create a NetworkX graph for comparison."""
        G = nx.MultiGraph()
        for node in sample_nodes:
            G.add_node((node['node_id'], node['layer']), **node)
        for edge in sample_edges:
            G.add_edge(
                (edge['source_id'], edge['source_layer']),
                (edge['target_id'], edge['target_layer']),
                weight=edge['weight'],
                edge_type=edge['edge_type']
            )
        return G
    
    @pytest.fixture
    def attribute_store(self, sample_nodes, sample_edges):
        """Create an AttributeStore for comparison."""
        store = AttributeStore()
        store.add_nodes_batch(sample_nodes)
        store.add_edges_batch(sample_edges)
        return store
    
    def test_benchmark_add_nodes_batch_networkx(self, benchmark, sample_nodes):
        """Benchmark batch node addition in NetworkX."""
        def add_nodes_nx():
            G = nx.MultiGraph()
            for node in sample_nodes:
                G.add_node((node['node_id'], node['layer']), **node)
            return G
        
        benchmark(add_nodes_nx)
    
    def test_benchmark_add_nodes_batch_store(self, benchmark, sample_nodes):
        """Benchmark batch node addition in AttributeStore."""
        def add_nodes_store():
            store = AttributeStore()
            store.add_nodes_batch(sample_nodes)
            return store
        
        benchmark(add_nodes_store)
    
    def test_benchmark_add_edges_batch_networkx(self, benchmark, sample_nodes, sample_edges):
        """Benchmark batch edge addition in NetworkX."""
        def add_edges_nx():
            G = nx.MultiGraph()
            # First add nodes
            for node in sample_nodes:
                G.add_node((node['node_id'], node['layer']), **node)
            # Then add edges
            for edge in sample_edges:
                G.add_edge(
                    (edge['source_id'], edge['source_layer']),
                    (edge['target_id'], edge['target_layer']),
                    weight=edge['weight'],
                    edge_type=edge['edge_type']
                )
            return G
        
        benchmark(add_edges_nx)
    
    def test_benchmark_add_edges_batch_store(self, benchmark, sample_nodes, sample_edges):
        """Benchmark batch edge addition in AttributeStore."""
        def add_edges_store():
            store = AttributeStore()
            store.add_nodes_batch(sample_nodes)
            store.add_edges_batch(sample_edges)
            return store
        
        benchmark(add_edges_store)
    
    def test_benchmark_get_all_nodes_networkx(self, benchmark, networkx_graph):
        """Benchmark getting all nodes in NetworkX."""
        def get_nodes_nx():
            return list(networkx_graph.nodes())
        
        benchmark(get_nodes_nx)
    
    def test_benchmark_get_all_nodes_store(self, benchmark, attribute_store):
        """Benchmark getting all nodes in AttributeStore."""
        def get_nodes_store():
            return attribute_store.get_all_nodes()
        
        benchmark(get_nodes_store)
    
    def test_benchmark_filter_by_layer_networkx(self, benchmark, networkx_graph):
        """Benchmark filtering nodes by layer in NetworkX."""
        def filter_by_layer_nx():
            target_layer = 'layer5'
            return [n for n in networkx_graph.nodes() if n[1] == target_layer]
        
        benchmark(filter_by_layer_nx)
    
    def test_benchmark_filter_by_layer_store(self, benchmark, attribute_store):
        """Benchmark filtering nodes by layer in AttributeStore."""
        def filter_by_layer_store():
            return attribute_store.get_nodes_in_layer('layer5')
        
        benchmark(filter_by_layer_store)
    
    def test_benchmark_get_neighbors_networkx(self, benchmark, networkx_graph):
        """Benchmark getting neighbors in NetworkX."""
        def get_neighbors_nx():
            return list(networkx_graph.neighbors(('node_100', 'layer0')))
        
        benchmark(get_neighbors_nx)
    
    def test_benchmark_get_neighbors_store(self, benchmark, attribute_store):
        """Benchmark getting neighbors in AttributeStore."""
        def get_neighbors_store():
            return attribute_store.get_neighbors('node_100', 'layer0')
        
        benchmark(get_neighbors_store)
    
    def test_benchmark_has_node_networkx(self, benchmark, networkx_graph):
        """Benchmark checking node existence in NetworkX."""
        def has_node_nx():
            result = []
            for i in range(100):
                result.append(networkx_graph.has_node((f'node_{i}', 'layer0')))
            return result
        
        benchmark(has_node_nx)
    
    def test_benchmark_has_node_store(self, benchmark, attribute_store):
        """Benchmark checking node existence in AttributeStore."""
        def has_node_store():
            result = []
            for i in range(100):
                result.append(attribute_store.has_node(f'node_{i}', 'layer0'))
            return result
        
        benchmark(has_node_store)
    
    def test_benchmark_get_unique_layers_networkx(self, benchmark, networkx_graph):
        """Benchmark getting unique layers in NetworkX."""
        def get_layers_nx():
            return set(n[1] for n in networkx_graph.nodes())
        
        benchmark(get_layers_nx)
    
    def test_benchmark_get_unique_layers_store(self, benchmark, attribute_store):
        """Benchmark getting unique layers in AttributeStore."""
        def get_layers_store():
            return attribute_store.get_unique_layers()
        
        benchmark(get_layers_store)
    
    def test_benchmark_count_nodes_networkx(self, benchmark, networkx_graph):
        """Benchmark counting nodes in NetworkX."""
        def count_nodes_nx():
            return networkx_graph.number_of_nodes()
        
        benchmark(count_nodes_nx)
    
    def test_benchmark_count_nodes_store(self, benchmark, attribute_store):
        """Benchmark counting nodes in AttributeStore."""
        def count_nodes_store():
            return attribute_store.node_count()
        
        benchmark(count_nodes_store)
    
    def test_benchmark_get_interlayer_edges_networkx(self, benchmark, networkx_graph):
        """Benchmark getting inter-layer edges in NetworkX."""
        def get_interlayer_nx():
            return [(u, v) for u, v in networkx_graph.edges() if u[1] != v[1]]
        
        benchmark(get_interlayer_nx)
    
    def test_benchmark_get_interlayer_edges_store(self, benchmark, attribute_store):
        """Benchmark getting inter-layer edges in AttributeStore."""
        def get_interlayer_store():
            return attribute_store.get_interlayer_edges()
        
        benchmark(get_interlayer_store)


if __name__ == '__main__':
    pytest.main([__file__, '--benchmark-only', '-v'])
