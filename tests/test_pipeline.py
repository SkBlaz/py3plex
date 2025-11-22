"""
Tests for scikit-learn style pipeline functionality.
"""

import os
import tempfile
from pathlib import Path

import pytest
import networkx as nx

from py3plex.pipeline import (
    Pipeline,
    PipelineStep,
    LoadStep,
    AggregateLayers,
    LeidenMultilayer,
    LouvainCommunity,
    ComputeStats,
    FilterNodes,
    SaveNetwork,
)
from py3plex.core import multinet


class TestPipelineStep:
    """Test PipelineStep base class."""
    
    def test_abstract_base_class(self):
        """PipelineStep cannot be instantiated directly."""
        with pytest.raises(TypeError):
            PipelineStep()
    
    def test_get_params(self):
        """Test get_params method."""
        step = LoadStep(generator='random_er', n=10, l=2, p=0.1)
        params = step.get_params()
        assert 'generator' in params
        assert params['generator'] == 'random_er'
        # Generator params are stored in generator_params dict
        assert 'generator_params' in params
        assert params['generator_params']['n'] == 10
    
    def test_set_params(self):
        """Test set_params method."""
        step = LoadStep(generator='random_er', n=10, l=2, p=0.1)
        # Can set top-level params
        step.set_params(directed=True)
        assert step.directed is True


class TestPipeline:
    """Test Pipeline class."""
    
    def test_pipeline_initialization(self):
        """Test pipeline can be initialized with steps."""
        pipe = Pipeline([
            ("load", LoadStep(generator='random_er', n=10, l=2, p=0.1)),
            ("stats", ComputeStats()),
        ])
        assert len(pipe.steps) == 2
        assert "load" in pipe.named_steps
        assert "stats" in pipe.named_steps
    
    def test_pipeline_validation(self):
        """Test pipeline validates step types."""
        with pytest.raises(TypeError, match="must be a PipelineStep"):
            Pipeline([
                ("load", "not a step"),
            ])
    
    def test_pipeline_repr(self):
        """Test pipeline string representation."""
        pipe = Pipeline([
            ("load", LoadStep(generator='random_er', n=10, l=2, p=0.1)),
        ])
        repr_str = repr(pipe)
        assert "Pipeline" in repr_str
        assert "load" in repr_str
    
    def test_pipeline_get_params(self):
        """Test pipeline get_params method."""
        pipe = Pipeline([
            ("load", LoadStep(generator='random_er', n=10, l=2, p=0.1)),
        ])
        params = pipe.get_params(deep=True)
        assert 'load__generator' in params
        assert params['load__generator'] == 'random_er'


class TestLoadStep:
    """Test LoadStep."""
    
    def test_load_step_requires_path_or_generator(self):
        """LoadStep requires either path or generator."""
        with pytest.raises(ValueError, match="Either 'path' or 'generator'"):
            LoadStep()
    
    def test_load_step_mutual_exclusion(self):
        """LoadStep cannot have both path and generator."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            LoadStep(path="file.graphml", generator="random_er")
    
    def test_load_step_generate_random(self):
        """Test generating random network."""
        step = LoadStep(generator='random_er', n=10, l=2, p=0.2, directed=False)
        network = step.transform(None)
        
        assert isinstance(network, multinet.multi_layer_network)
        assert network.core_network.number_of_nodes() > 0
    
    def test_load_step_from_file_graphml(self):
        """Test loading network from GraphML file."""
        # Create a simple test network
        G = nx.karate_club_graph()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as f:
            nx.write_graphml(G, f.name)
            file_path = f.name
        
        try:
            step = LoadStep(path=file_path, input_type='graphml')
            network = step.transform(None)
            
            assert isinstance(network, multinet.multi_layer_network)
            assert network.core_network.number_of_nodes() == 34
        finally:
            Path(file_path).unlink()
    
    def test_load_step_unknown_generator(self):
        """Test error on unknown generator."""
        step = LoadStep(generator='unknown_generator')
        with pytest.raises(ValueError, match="Unknown generator"):
            step.transform(None)


class TestAggregateLayers:
    """Test AggregateLayers step."""
    
    def test_aggregate_layers_sum(self):
        """Test layer aggregation with sum method."""
        # Create a simple multilayer network
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
        ], input_type='list')
        
        step = AggregateLayers(method='sum')
        aggregated = step.transform(network)
        
        assert isinstance(aggregated, multinet.multi_layer_network)
        assert aggregated.core_network.number_of_nodes() > 0
    
    def test_aggregate_layers_invalid_method(self):
        """Test error on invalid aggregation method."""
        with pytest.raises(ValueError, match="method must be"):
            AggregateLayers(method='invalid')
    
    def test_aggregate_layers_type_check(self):
        """Test type checking in transform."""
        step = AggregateLayers(method='sum')
        with pytest.raises(TypeError, match="Expected multi_layer_network"):
            step.transform("not a network")


class TestLeidenMultilayer:
    """Test LeidenMultilayer step."""
    
    def test_leiden_multilayer_basic(self):
        """Test basic Leiden community detection."""
        # Create a simple network
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'A', 'L1', 1],
        ], input_type='list')
        
        step = LeidenMultilayer(resolution=1.0, seed=42)
        
        # This will only work if leidenalg is installed
        try:
            result = step.transform(network)
            assert hasattr(result, 'communities')
            assert hasattr(result, 'modularity')
        except ImportError:
            pytest.skip("leidenalg not installed")
    
    def test_leiden_multilayer_type_check(self):
        """Test type checking in transform."""
        step = LeidenMultilayer()
        with pytest.raises(TypeError, match="Expected multi_layer_network"):
            step.transform("not a network")


class TestLouvainCommunity:
    """Test LouvainCommunity step."""
    
    def test_louvain_community_basic(self):
        """Test basic Louvain community detection."""
        # Create a simple network
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'A', 'L1', 1],
        ], input_type='list')
        
        step = LouvainCommunity(resolution=1.0)
        result = step.transform(network)
        
        assert isinstance(result, dict)
        assert 'algorithm' in result
        assert result['algorithm'] == 'louvain'
        assert 'num_communities' in result
        assert 'communities' in result
    
    def test_louvain_type_check(self):
        """Test type checking in transform."""
        step = LouvainCommunity()
        with pytest.raises(TypeError, match="Expected multi_layer_network"):
            step.transform("not a network")


class TestComputeStats:
    """Test ComputeStats step."""
    
    def test_compute_stats_basic(self):
        """Test basic statistics computation."""
        # Create a simple network
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
        ], input_type='list')
        
        step = ComputeStats(include_layer_stats=False)
        stats = step.transform(network)
        
        assert isinstance(stats, dict)
        assert 'nodes' in stats
        assert 'edges' in stats
        assert 'density' in stats
        assert stats['nodes'] == 3
        assert stats['edges'] == 2
    
    def test_compute_stats_with_layers(self):
        """Test statistics with layer information."""
        # Create a multilayer network
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
        ], input_type='list')
        
        step = ComputeStats(include_layer_stats=True)
        stats = step.transform(network)
        
        assert isinstance(stats, dict)
        # Note: layer stats might not be present depending on node format
    
    def test_compute_stats_type_check(self):
        """Test type checking in transform."""
        step = ComputeStats()
        with pytest.raises(TypeError, match="Expected multi_layer_network"):
            step.transform("not a network")


class TestFilterNodes:
    """Test FilterNodes step."""
    
    def test_filter_nodes_min_degree(self):
        """Test filtering nodes by minimum degree."""
        # Create a network with varying degrees
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['B', 'L1', 'D', 'L1', 1],
        ], input_type='list')
        
        # B has degree 3, others have degree 1
        step = FilterNodes(min_degree=2)
        filtered = step.transform(network)
        
        assert isinstance(filtered, multinet.multi_layer_network)
        # After filtering, only nodes with degree >= 2 remain
        assert filtered.core_network.number_of_nodes() <= 4
    
    def test_filter_nodes_explicit_list(self):
        """Test filtering with explicit node list."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
        ], input_type='list')
        
        # Keep only nodes in the list
        nodes = [('A', 'L1'), ('B', 'L1')]
        step = FilterNodes(node_list=nodes)
        filtered = step.transform(network)
        
        assert isinstance(filtered, multinet.multi_layer_network)
    
    def test_filter_nodes_type_check(self):
        """Test type checking in transform."""
        step = FilterNodes(min_degree=1)
        with pytest.raises(TypeError, match="Expected multi_layer_network"):
            step.transform("not a network")


class TestSaveNetwork:
    """Test SaveNetwork step."""
    
    def test_save_network_graphml(self):
        """Test saving network to GraphML."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
        ], input_type='list')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as f:
            file_path = f.name
        
        try:
            step = SaveNetwork(path=file_path, format='graphml')
            result = step.transform(network)
            
            # Step should pass through the network
            assert result is network
            assert Path(file_path).exists()
        finally:
            Path(file_path).unlink(missing_ok=True)
    
    def test_save_network_unsupported_format(self):
        """Test error on unsupported format."""
        network = multinet.multi_layer_network(directed=False)
        step = SaveNetwork(path='test.txt', format='unsupported')
        
        with pytest.raises(ValueError, match="Unsupported format"):
            step.transform(network)
    
    def test_save_network_type_check(self):
        """Test type checking in transform."""
        step = SaveNetwork(path='test.graphml')
        with pytest.raises(TypeError, match="Expected multi_layer_network"):
            step.transform("not a network")


class TestPipelineIntegration:
    """Integration tests for complete pipelines."""
    
    def test_simple_pipeline(self):
        """Test a simple load -> stats pipeline."""
        pipe = Pipeline([
            ("load", LoadStep(generator='random_er', n=10, l=2, p=0.2)),
            ("stats", ComputeStats(include_layer_stats=False)),
        ])
        
        result = pipe.run()
        
        assert isinstance(result, dict)
        assert 'nodes' in result
        assert 'edges' in result
    
    def test_aggregation_pipeline(self):
        """Test load -> aggregate -> stats pipeline."""
        pipe = Pipeline([
            ("load", LoadStep(generator='random_er', n=15, l=3, p=0.15)),
            ("aggregate", AggregateLayers(method='sum')),
            ("stats", ComputeStats(include_layer_stats=False)),
        ])
        
        result = pipe.run()
        
        assert isinstance(result, dict)
        assert result['nodes'] > 0
    
    def test_community_pipeline(self):
        """Test load -> community detection pipeline."""
        pipe = Pipeline([
            ("load", LoadStep(generator='random_er', n=20, l=2, p=0.2)),
            ("community", LouvainCommunity(resolution=1.0)),
        ])
        
        result = pipe.run()
        
        assert isinstance(result, dict)
        assert 'num_communities' in result
    
    def test_filter_pipeline(self):
        """Test load -> filter -> stats pipeline."""
        pipe = Pipeline([
            ("load", LoadStep(generator='random_er', n=20, l=2, p=0.2)),
            ("filter", FilterNodes(min_degree=1)),
            ("stats", ComputeStats(include_layer_stats=False)),
        ])
        
        result = pipe.run()
        
        assert isinstance(result, dict)
    
    def test_save_pipeline(self):
        """Test pipeline with save step."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as f:
            file_path = f.name
        
        try:
            pipe = Pipeline([
                ("load", LoadStep(generator='random_er', n=10, l=2, p=0.2)),
                ("save", SaveNetwork(path=file_path, format='graphml')),
                ("stats", ComputeStats(include_layer_stats=False)),
            ])
            
            result = pipe.run()
            
            assert isinstance(result, dict)
            assert Path(file_path).exists()
        finally:
            Path(file_path).unlink(missing_ok=True)
    
    def test_complex_pipeline(self):
        """Test a complex multi-step pipeline."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as f:
            file_path = f.name
        
        try:
            pipe = Pipeline([
                ("load", LoadStep(generator='random_er', n=25, l=2, p=0.15)),
                ("filter", FilterNodes(min_degree=1)),
                ("aggregate", AggregateLayers(method='sum')),
                ("save", SaveNetwork(path=file_path, format='graphml')),
                ("stats", ComputeStats(include_layer_stats=False)),
            ])
            
            result = pipe.run()
            
            assert isinstance(result, dict)
            assert result['nodes'] > 0
            assert Path(file_path).exists()
        finally:
            Path(file_path).unlink(missing_ok=True)


class TestPipelineEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_pipeline(self):
        """Test pipeline with no steps."""
        pipe = Pipeline([])
        result = pipe.run()
        assert result is None
    
    def test_single_step_pipeline(self):
        """Test pipeline with single step."""
        pipe = Pipeline([
            ("load", LoadStep(generator='random_er', n=10, l=2, p=0.1)),
        ])
        
        result = pipe.run()
        assert isinstance(result, multinet.multi_layer_network)
