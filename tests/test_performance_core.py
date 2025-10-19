"""
Performance benchmark tests for core multilayer data structures.

This module tests the runtime performance of fundamental multilayer network operations
including network creation, node/edge addition, layer traversal, and basic queries.
These benchmarks pin down core data structure performance to detect regressions.
"""

import time
import pytest
import numpy as np

from py3plex.core import multinet


class TestNetworkCreationBenchmarks:
    """Benchmark tests for network creation and initialization."""
    
    def test_bench_network_init(self, benchmark):
        """Benchmark creating an empty network."""
        result = benchmark(multinet.multi_layer_network, verbose=False)
        assert result is not None
    
    def test_bench_network_with_type(self, benchmark):
        """Benchmark creating network with specific type."""
        result = benchmark(
            multinet.multi_layer_network,
            verbose=False,
            network_type="multilayer",
            directed=True
        )
        assert result is not None


class TestNodeEdgeOperationsBenchmarks:
    """Benchmark tests for node and edge operations."""
    
    @pytest.fixture
    def empty_network(self):
        """Create an empty multilayer network."""
        return multinet.multi_layer_network(verbose=False)
    
    @pytest.fixture
    def small_network(self):
        """Create a small network with 100 nodes across 2 layers."""
        net = multinet.multi_layer_network(verbose=False)
        import networkx as nx
        net.core_network = nx.MultiGraph()
        
        # Add nodes
        for layer in ['layer1', 'layer2']:
            for i in range(50):
                net.core_network.add_node((f'node_{i}', layer))
        
        # Add some edges
        for layer in ['layer1', 'layer2']:
            for i in range(40):
                net.core_network.add_edge(
                    (f'node_{i}', layer),
                    (f'node_{i+1}', layer),
                    weight=1.0
                )
        
        return net
    
    @pytest.fixture
    def medium_network(self):
        """Create a medium network with 1000 nodes across 4 layers."""
        net = multinet.multi_layer_network(verbose=False)
        import networkx as nx
        net.core_network = nx.MultiGraph()
        
        # Add nodes
        for layer in ['layer1', 'layer2', 'layer3', 'layer4']:
            for i in range(250):
                net.core_network.add_node((f'node_{i}', layer))
        
        # Add edges
        for layer in ['layer1', 'layer2', 'layer3', 'layer4']:
            for i in range(240):
                net.core_network.add_edge(
                    (f'node_{i}', layer),
                    (f'node_{i+1}', layer),
                    weight=1.0
                )
        
        return net
    
    def test_bench_add_single_edge(self, empty_network, benchmark):
        """Benchmark adding a single edge to network."""
        net = empty_network
        import networkx as nx
        net.core_network = nx.MultiGraph()
        net.core_network.add_node(('node1', 'layer1'))
        net.core_network.add_node(('node2', 'layer1'))
        
        def add_edge():
            net.core_network.add_edge(
                ('node1', 'layer1'),
                ('node2', 'layer1'),
                weight=1.0
            )
        
        benchmark(add_edge)
        assert net.core_network.number_of_edges() > 0
    
    def test_bench_get_nodes_iteration_small(self, small_network, benchmark):
        """Benchmark iterating through nodes on small network."""
        def iterate_nodes():
            return list(small_network.get_nodes())
        
        result = benchmark(iterate_nodes)
        assert len(result) == 100
    
    def test_bench_get_nodes_iteration_medium(self, medium_network, benchmark):
        """Benchmark iterating through nodes on medium network."""
        def iterate_nodes():
            return list(medium_network.get_nodes())
        
        result = benchmark(iterate_nodes)
        assert len(result) == 1000
    
    def test_bench_get_edges_iteration_small(self, small_network, benchmark):
        """Benchmark iterating through edges on small network."""
        def iterate_edges():
            return list(small_network.get_edges())
        
        result = benchmark(iterate_edges)
        assert len(result) > 0
    
    def test_bench_get_edges_iteration_medium(self, medium_network, benchmark):
        """Benchmark iterating through edges on medium network."""
        def iterate_edges():
            return list(medium_network.get_edges())
        
        result = benchmark(iterate_edges)
        assert len(result) > 0


class TestLayerOperationsBenchmarks:
    """Benchmark tests for layer-related operations."""
    
    @pytest.fixture
    def multilayer_network_small(self):
        """Create small multilayer network."""
        net = multinet.multi_layer_network(verbose=False)
        import networkx as nx
        net.core_network = nx.MultiGraph()
        
        # Create 2 layers with 25 nodes each
        for layer in ['A', 'B']:
            for i in range(25):
                for j in range(i+1, min(i+4, 25)):
                    net.core_network.add_edge(
                        (f'n{i}', layer),
                        (f'n{j}', layer),
                        weight=1.0
                    )
        
        return net
    
    @pytest.fixture
    def multilayer_network_medium(self):
        """Create medium multilayer network."""
        net = multinet.multi_layer_network(verbose=False)
        import networkx as nx
        net.core_network = nx.MultiGraph()
        
        # Create 4 layers with 100 nodes each
        for layer in ['A', 'B', 'C', 'D']:
            for i in range(100):
                for j in range(i+1, min(i+3, 100)):
                    net.core_network.add_edge(
                        (f'n{i}', layer),
                        (f'n{j}', layer),
                        weight=1.0
                    )
        
        return net
    
    def test_bench_get_layers_small(self, multilayer_network_small, benchmark):
        """Benchmark getting layers on small network."""
        result = benchmark(multilayer_network_small.get_layers)
        assert result is not None
    
    def test_bench_get_layers_medium(self, multilayer_network_medium, benchmark):
        """Benchmark getting layers on medium network."""
        result = benchmark(multilayer_network_medium.get_layers)
        assert result is not None
    
    def test_bench_split_to_layers_small(self, multilayer_network_small, benchmark):
        """Benchmark splitting to individual layers on small network."""
        benchmark(
            multilayer_network_small.split_to_layers,
            verbose=False
        )
        # split_to_layers sets attributes on the object
        assert hasattr(multilayer_network_small, 'layer_names')
        assert hasattr(multilayer_network_small, 'separate_layers')


class TestNetworkQueryBenchmarks:
    """Benchmark tests for network queries and statistics."""
    
    @pytest.fixture
    def query_network(self):
        """Create network for query benchmarks."""
        net = multinet.multi_layer_network(verbose=False)
        import networkx as nx
        net.core_network = nx.MultiGraph()
        
        # Create a network with 3 layers, 50 nodes each
        for layer in ['X', 'Y', 'Z']:
            for i in range(50):
                for j in range(i+1, min(i+5, 50)):
                    net.core_network.add_edge(
                        (f'node_{i}', layer),
                        (f'node_{j}', layer),
                        weight=np.random.random()
                    )
        
        return net
    
    def test_bench_summary(self, query_network, benchmark):
        """Benchmark computing network summary statistics."""
        result = benchmark(query_network.summary)
        assert result is not None
        assert 'Nodes' in result
        assert 'Edges' in result
    
    def test_bench_get_unique_entity_counts(self, query_network, benchmark):
        """Benchmark counting unique entities."""
        result = benchmark(query_network.get_unique_entity_counts)
        assert len(result) == 3
        total_nodes, unique_ids, nodes_per_layer = result
        assert total_nodes > 0
        assert unique_ids > 0
        assert len(nodes_per_layer) == 3
    
    def test_bench_get_neighbors(self, query_network, benchmark):
        """Benchmark getting neighbors of a node."""
        result = benchmark(query_network.get_neighbors, 'node_5', 'X')
        assert result is not None


class TestNetworkTransformationBenchmarks:
    """Benchmark tests for network transformations."""
    
    @pytest.fixture
    def transform_network(self):
        """Create network for transformation benchmarks."""
        net = multinet.multi_layer_network(verbose=False)
        import networkx as nx
        net.core_network = nx.MultiGraph()
        
        # Create simple network
        for i in range(30):
            for j in range(i+1, min(i+4, 30)):
                net.core_network.add_edge(
                    (f'n{i}', 'layer1'),
                    (f'n{j}', 'layer1'),
                    weight=1.0
                )
        
        return net
    
    def test_bench_to_sparse_matrix(self, transform_network, benchmark):
        """Benchmark conversion to sparse matrix."""
        result = benchmark(transform_network.to_sparse_matrix, return_only=True)
        assert result is not None
    
    def test_bench_to_json(self, transform_network, benchmark):
        """Benchmark conversion to JSON."""
        result = benchmark(transform_network.to_json)
        assert result is not None
        assert 'nodes' in result or 'links' in result


class TestScalabilityBenchmarks:
    """Test scaling behavior with different network sizes."""
    
    def test_node_iteration_scaling(self):
        """Test that node iteration scales linearly with network size."""
        np.random.seed(42)
        
        times = []
        sizes = [100, 500, 1000, 2000]
        
        for n_nodes in sizes:
            net = multinet.multi_layer_network(verbose=False)
            import networkx as nx
            net.core_network = nx.MultiGraph()
            
            # Add nodes
            for i in range(n_nodes):
                net.core_network.add_node((f'n{i}', 'layer1'))
            
            # Time iteration
            t0 = time.perf_counter()
            _ = list(net.get_nodes())
            times.append(time.perf_counter() - t0)
        
        # Check roughly linear: time ratio ≈ size ratio
        ratio_size = sizes[-1] / sizes[0]
        ratio_time = times[-1] / times[0]
        
        print(f"\nNode iteration scaling test:")
        for size, time_val in zip(sizes, times):
            print(f"  {size:5d} nodes: {time_val:.6f}s")
        print(f"  Size ratio: {ratio_size:.1f}×")
        print(f"  Time ratio: {ratio_time:.1f}×")
        
        # Allow some overhead but expect roughly linear scaling
        assert ratio_time < ratio_size * 2.0, "Non-linear scaling detected"
    
    def test_layer_count_scaling(self):
        """Test that layer operations scale well with number of layers."""
        np.random.seed(42)
        
        times = {}
        layer_counts = [2, 4, 8, 16]
        nodes_per_layer = 50
        
        for n_layers in layer_counts:
            net = multinet.multi_layer_network(verbose=False)
            import networkx as nx
            net.core_network = nx.MultiGraph()
            
            # Create layers
            for layer_idx in range(n_layers):
                layer_name = f'L{layer_idx}'
                for i in range(nodes_per_layer):
                    for j in range(i+1, min(i+3, nodes_per_layer)):
                        net.core_network.add_edge(
                            (f'n{i}', layer_name),
                            (f'n{j}', layer_name),
                            weight=1.0
                        )
            
            # Time getting layers
            t0 = time.perf_counter()
            _ = net.get_layers()
            times[n_layers] = time.perf_counter() - t0
        
        print(f"\nLayer scaling test (fixed {nodes_per_layer} nodes per layer):")
        for n_layers, time_val in times.items():
            print(f"  {n_layers:2d} layers: {time_val:.6f}s")
        
        # More layers should increase time, but not excessively
        assert times[16] < times[2] * 10.0, "Excessive slowdown with more layers"


class TestMultiplexNetworkBenchmarks:
    """Benchmark tests specific to multiplex networks."""
    
    @pytest.fixture
    def multiplex_network_small(self):
        """Create small multiplex network with coupling edges."""
        net = multinet.multi_layer_network(
            verbose=False,
            network_type="multiplex",
            coupling_weight=1.0
        )
        import networkx as nx
        net.core_network = nx.MultiGraph()
        
        # Add nodes across 2 layers
        for layer in ['L1', 'L2']:
            for i in range(20):
                net.core_network.add_node((f'n{i}', layer))
        
        # Add intra-layer edges
        for layer in ['L1', 'L2']:
            for i in range(15):
                net.core_network.add_edge(
                    (f'n{i}', layer),
                    (f'n{i+1}', layer),
                    type='intra',
                    weight=1.0
                )
        
        # Add coupling edges
        for i in range(20):
            net.core_network.add_edge(
                (f'n{i}', 'L1'),
                (f'n{i}', 'L2'),
                type='coupling',
                weight=1.0
            )
        
        return net
    
    def test_bench_get_edges_multiplex_no_coupling(self, multiplex_network_small, benchmark):
        """Benchmark getting edges without coupling edges in multiplex network."""
        def get_edges_no_coupling():
            return list(multiplex_network_small.get_edges(multiplex_edges=False))
        
        result = benchmark(get_edges_no_coupling)
        assert len(result) > 0
    
    def test_bench_get_edges_multiplex_with_coupling(self, multiplex_network_small, benchmark):
        """Benchmark getting all edges including coupling in multiplex network."""
        def get_all_edges():
            return list(multiplex_network_small.get_edges(multiplex_edges=True))
        
        result = benchmark(get_all_edges)
        assert len(result) > 0


if __name__ == "__main__":
    # Allow running as standalone script for quick profiling
    print("Running core performance benchmark suite...")
    pytest.main([__file__, "-v", "--benchmark-only"])
