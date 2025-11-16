#!/usr/bin/env python3
"""
Tests for the multilayer network fingerprint functionality.

Tests the get_fingerprint() method which provides comprehensive
network statistics and characterization.
"""

import pytest
import sys
import os

# Add py3plex to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from py3plex.core import multinet


class TestFingerprintBasic:
    """Test basic fingerprint functionality."""

    def test_fingerprint_returns_dataframe(self):
        """Test that fingerprint returns a pandas DataFrame."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'}
        ])
        
        fingerprint = net.get_fingerprint()
        
        # Check it's a DataFrame
        import pandas as pd
        assert isinstance(fingerprint, pd.DataFrame)
        
        # Check it has the expected columns
        assert 'statistic' in fingerprint.columns
        assert 'value' in fingerprint.columns
        assert 'description' in fingerprint.columns
    
    def test_fingerprint_empty_network_raises_error(self):
        """Test that fingerprint raises error for empty network."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        
        with pytest.raises(ValueError, match="Network is empty"):
            net.get_fingerprint()
    
    def test_fingerprint_basic_stats_present(self):
        """Test that basic statistics are present in fingerprint."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'}
        ])
        
        fingerprint = net.get_fingerprint()
        stats = fingerprint['statistic'].tolist()
        
        # Check that essential statistics are present
        assert 'total_node_layer_pairs' in stats
        assert 'unique_nodes' in stats
        assert 'total_edges' in stats
        assert 'num_layers' in stats
        assert 'is_directed' in stats
        assert 'overall_density' in stats
    
    def test_fingerprint_values_correct(self):
        """Test that fingerprint values are computed correctly."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'}
        ])
        
        fingerprint = net.get_fingerprint()
        
        # Check specific values
        def get_stat_value(stat_name):
            row = fingerprint[fingerprint['statistic'] == stat_name]
            if len(row) > 0:
                return row['value'].iloc[0]
            return None
        
        assert get_stat_value('unique_nodes') == 3  # A, B, C
        assert get_stat_value('total_edges') == 2
        assert get_stat_value('num_layers') == 1
        assert get_stat_value('is_directed') == False
    
    def test_fingerprint_multilayer_stats(self):
        """Test fingerprint with multiple layers."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
            {'source': 'A', 'target': 'A', 'source_type': 'L1', 'target_type': 'L2'}
        ])
        
        fingerprint = net.get_fingerprint()
        
        def get_stat_value(stat_name):
            row = fingerprint[fingerprint['statistic'] == stat_name]
            if len(row) > 0:
                return row['value'].iloc[0]
            return None
        
        assert get_stat_value('num_layers') == 2
        assert get_stat_value('intra_layer_edges') == 2
        assert get_stat_value('inter_layer_edges') == 1


class TestFingerprintLayerStats:
    """Test layer-specific statistics in fingerprint."""
    
    def test_fingerprint_with_layer_stats(self):
        """Test that layer statistics are computed when requested."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'B', 'source_type': 'L2', 'target_type': 'L2'}
        ])
        
        fingerprint = net.get_fingerprint(include_layer_stats=True)
        stats = fingerprint['statistic'].tolist()
        
        # Check for layer-specific stats
        assert 'nodes_in_layer_L1' in stats
        assert 'nodes_in_layer_L2' in stats
        assert 'layer_density_L1' in stats
        assert 'layer_density_L2' in stats
    
    def test_fingerprint_without_layer_stats(self):
        """Test that layer stats can be excluded."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'}
        ])
        
        fingerprint = net.get_fingerprint(include_layer_stats=False)
        stats = fingerprint['statistic'].tolist()
        
        # These should not be present
        assert 'layer_density_L1' not in stats
        assert 'nodes_in_layer_L1' not in stats
    
    def test_fingerprint_layer_density(self):
        """Test that layer density is computed correctly."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        # Create a complete graph in L1 with 3 nodes
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'C', 'target': 'A', 'source_type': 'L1', 'target_type': 'L1'}
        ])
        
        fingerprint = net.get_fingerprint(include_layer_stats=True)
        
        def get_stat_value(stat_name):
            row = fingerprint[fingerprint['statistic'] == stat_name]
            if len(row) > 0:
                return row['value'].iloc[0]
            return None
        
        # Complete graph on 3 nodes has density 1.0
        density = get_stat_value('layer_density_L1')
        assert density is not None
        assert abs(density - 1.0) < 0.001  # Float comparison


class TestFingerprintDirected:
    """Test fingerprint with directed networks."""
    
    def test_fingerprint_directed_flag(self):
        """Test that directed flag is correctly reported."""
        net_undirected = multinet.multi_layer_network(directed=False, verbose=False)
        net_undirected.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'}
        ])
        
        net_directed = multinet.multi_layer_network(directed=True, verbose=False)
        net_directed.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'}
        ])
        
        fp_undirected = net_undirected.get_fingerprint()
        fp_directed = net_directed.get_fingerprint()
        
        def get_stat_value(fp, stat_name):
            row = fp[fp['statistic'] == stat_name]
            if len(row) > 0:
                return row['value'].iloc[0]
            return None
        
        assert get_stat_value(fp_undirected, 'is_directed') == False
        assert get_stat_value(fp_directed, 'is_directed') == True


class TestFingerprintErrorHandling:
    """Test error handling in fingerprint computation."""
    
    def test_fingerprint_handles_statistics_errors(self):
        """Test that fingerprint gracefully handles errors in individual statistics."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'}
        ])
        
        # This should not raise an error, even if some stats fail
        fingerprint = net.get_fingerprint()
        
        # Check that we got a DataFrame
        import pandas as pd
        assert isinstance(fingerprint, pd.DataFrame)
        
        # Check that some stats have error values
        values = fingerprint['value'].tolist()
        # Some values might be error strings
        has_some_valid_values = any(
            not isinstance(v, str) or not v.startswith('Error:')
            for v in values
        )
        assert has_some_valid_values


class TestFingerprintComprehensive:
    """Comprehensive integration tests for fingerprint."""
    
    def test_fingerprint_comprehensive_network(self):
        """Test fingerprint on a comprehensive multilayer network."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        
        # Create a more complex network
        edges = [
            # Layer 1
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'C', 'target': 'D', 'source_type': 'L1', 'target_type': 'L1'},
            # Layer 2
            {'source': 'A', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
            {'source': 'B', 'target': 'D', 'source_type': 'L2', 'target_type': 'L2'},
            # Inter-layer
            {'source': 'A', 'target': 'A', 'source_type': 'L1', 'target_type': 'L2'},
            {'source': 'B', 'target': 'B', 'source_type': 'L1', 'target_type': 'L2'},
        ]
        
        net.add_edges(edges)
        
        fingerprint = net.get_fingerprint(include_layer_stats=True)
        
        # Check that we have a good number of statistics
        assert len(fingerprint) >= 10
        
        # Check that all required columns are present
        assert set(fingerprint.columns) == {'statistic', 'value', 'description'}
        
        # Check that all descriptions are strings
        assert all(isinstance(d, str) for d in fingerprint['description'])
    
    def test_fingerprint_export(self):
        """Test that fingerprint can be exported to various formats."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'}
        ])
        
        fingerprint = net.get_fingerprint()
        
        # Test conversion to dict
        as_dict = fingerprint.to_dict('records')
        assert isinstance(as_dict, list)
        assert len(as_dict) > 0
        assert 'statistic' in as_dict[0]
        
        # Test conversion to CSV (in memory)
        csv_string = fingerprint.to_csv(index=False)
        assert isinstance(csv_string, str)
        assert 'statistic,value,description' in csv_string


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
