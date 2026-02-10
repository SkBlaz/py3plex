#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Ergonomic Helper Functions
================================

Tests for the ergonomic helper functions that make py3plex easier to use.
"""

import pytest
from py3plex.ergonomics import (
    quick_network,
    quick_analysis,
    quick_communities,
    show_network_summary
)


class TestQuickNetwork:
    """Test quick_network helper."""
    
    def test_creates_basic_network(self):
        """Test that quick_network creates a valid network."""
        net = quick_network(
            people=['Alice', 'Bob'],
            layers=['work'],
            connections=[('Alice', 'Bob', 'work')]
        )
        
        assert net is not None
        nodes = list(net.get_nodes())
        edges = list(net.get_edges())
        layers = net.get_layers()[0]  # get_layers returns (layer_list, graphs, dict)
        
        assert len(nodes) == 2  # 2 people in 1 layer
        assert len(edges) == 1
        assert len(layers) == 1
        assert 'work' in layers
    
    def test_creates_multilayer_network(self):
        """Test multilayer network creation."""
        net = quick_network(
            people=['Alice', 'Bob', 'Carol'],
            layers=['work', 'social'],
            connections=[
                ('Alice', 'Bob', 'work'),
                ('Bob', 'Carol', 'social')
            ]
        )
        
        nodes = list(net.get_nodes())
        layers = net.get_layers()[0]  # get_layers returns (layer_list, graphs, dict)
        
        assert len(nodes) == 6  # 3 people × 2 layers
        assert len(layers) == 2
        assert 'work' in layers
        assert 'social' in layers
    
    def test_handles_empty_connections(self):
        """Test network with no connections."""
        net = quick_network(
            people=['Alice', 'Bob'],
            layers=['work'],
            connections=[]
        )
        
        nodes = list(net.get_nodes())
        edges = list(net.get_edges())
        
        assert len(nodes) == 2
        assert len(edges) == 0


class TestQuickAnalysis:
    """Test quick_analysis helper."""
    
    def test_basic_analysis(self):
        """Test basic network analysis."""
        net = quick_network(
            people=['Alice', 'Bob', 'Carol'],
            layers=['work'],
            connections=[
                ('Alice', 'Bob', 'work'),
                ('Bob', 'Carol', 'work')
            ]
        )
        
        results = quick_analysis(
            net,
            metrics=['degree'],
            top_k=3
        )
        
        assert 'dataframe' in results
        assert 'count' in results
        assert 'network_stats' in results
        
        df = results['dataframe']
        assert len(df) == 3
        assert 'degree' in df.columns
    
    def test_multiple_metrics(self):
        """Test analysis with multiple metrics."""
        net = quick_network(
            people=['Alice', 'Bob', 'Carol'],
            layers=['work'],
            connections=[
                ('Alice', 'Bob', 'work'),
                ('Bob', 'Carol', 'work')
            ]
        )
        
        results = quick_analysis(
            net,
            metrics=['degree', 'betweenness_centrality'],
            top_k=2
        )
        
        df = results['dataframe']
        assert 'degree' in df.columns
        assert 'betweenness_centrality' in df.columns
    
    def test_network_stats(self):
        """Test that network stats are included."""
        net = quick_network(
            people=['Alice', 'Bob'],
            layers=['work'],
            connections=[('Alice', 'Bob', 'work')]
        )
        
        results = quick_analysis(net, metrics=['degree'], top_k=2)
        stats = results['network_stats']
        
        assert 'nodes' in stats
        assert 'edges' in stats
        assert 'layers' in stats
        assert stats['nodes'] == 2
        assert stats['edges'] == 1
        # Note: internal implementation may create additional layers for coupling
        assert stats['layers'] >= 1


class TestQuickCommunities:
    """Test quick_communities helper."""
    
    def test_louvain_communities(self):
        """Test Louvain community detection."""
        net = quick_network(
            people=['Alice', 'Bob', 'Carol', 'Diana'],
            layers=['work'],
            connections=[
                ('Alice', 'Bob', 'work'),
                ('Bob', 'Carol', 'work'),
                ('Carol', 'Diana', 'work')
            ]
        )
        
        results = quick_communities(net, algorithm='louvain', seed=42)
        
        assert 'communities' in results  # Changed from 'partition' to 'communities'
        assert 'n_communities' in results
        assert 'sizes' in results
        
        assert results['n_communities'] >= 1
        assert isinstance(results['sizes'], dict)
    
    def test_reproducible_with_seed(self):
        """Test that seed makes results reproducible."""
        net = quick_network(
            people=['Alice', 'Bob', 'Carol'],
            layers=['work'],
            connections=[
                ('Alice', 'Bob', 'work'),
                ('Bob', 'Carol', 'work')
            ]
        )
        
        results1 = quick_communities(net, algorithm='louvain', seed=42)
        results2 = quick_communities(net, algorithm='louvain', seed=42)
        
        assert results1['n_communities'] == results2['n_communities']
        # Community assignments should be identical
        assert results1['communities'] == results2['communities']


class TestShowNetworkSummary:
    """Test show_network_summary helper."""
    
    def test_displays_summary_without_error(self, capsys):
        """Test that summary displays without errors."""
        net = quick_network(
            people=['Alice', 'Bob'],
            layers=['work', 'social'],
            connections=[
                ('Alice', 'Bob', 'work'),
                ('Alice', 'Bob', 'social')
            ]
        )
        
        # Should not raise exception
        show_network_summary(net)
        
        captured = capsys.readouterr()
        assert 'NETWORK SUMMARY' in captured.out
        assert 'Nodes' in captured.out
        assert 'Edges' in captured.out
        assert 'Layers' in captured.out
    
    def test_shows_layer_details(self, capsys):
        """Test that layer details are shown."""
        net = quick_network(
            people=['Alice', 'Bob'],
            layers=['work', 'social'],
            connections=[('Alice', 'Bob', 'work')]
        )
        
        show_network_summary(net)
        
        captured = capsys.readouterr()
        assert 'work' in captured.out
        assert 'social' in captured.out


class TestErgonomicIntegration:
    """Test that ergonomic helpers work together."""
    
    def test_create_analyze_community_pipeline(self):
        """Test complete pipeline from creation to community detection."""
        # Create network
        net = quick_network(
            people=['Alice', 'Bob', 'Carol', 'Diana'],
            layers=['social'],
            connections=[
                ('Alice', 'Bob', 'social'),
                ('Bob', 'Carol', 'social'),
                ('Carol', 'Diana', 'social')
            ]
        )
        
        # Analyze
        analysis = quick_analysis(net, metrics=['degree'], top_k=4)
        assert len(analysis['dataframe']) == 4
        
        # Detect communities
        communities = quick_communities(net, seed=42)
        assert communities['n_communities'] >= 1
        
        # Summary should work
        show_network_summary(net)
    
    def test_multilayer_pipeline(self):
        """Test pipeline with multilayer network."""
        net = quick_network(
            people=['Alice', 'Bob', 'Carol'],
            layers=['work', 'social'],
            connections=[
                ('Alice', 'Bob', 'work'),
                ('Bob', 'Carol', 'work'),
                ('Alice', 'Carol', 'social')
            ]
        )
        
        # Should handle multilayer analysis
        analysis = quick_analysis(
            net,
            metrics=['degree', 'betweenness_centrality'],
            top_k=5
        )
        
        assert len(analysis['dataframe']) == 5
        # Note: internal implementation may create additional layers
        assert analysis['network_stats']['layers'] >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
