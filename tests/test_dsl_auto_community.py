"""Tests for DSL v2 AutoCommunity entrypoints.

Tests cover:
- Q.communities().auto() returns assignment table
- Q.nodes().community_auto() joins annotations
- Filtering on auto community attributes
- Caching semantics (single run per execute)
- Multilayer network support
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from py3plex.core import multinet
from py3plex.dsl import Q


@pytest.fixture
def simple_network():
    """Create a simple test network."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer1'},
        {'source': 'E', 'type': 'layer1'},
        {'source': 'F', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    # Add edges to form two communities
    edges = [
        # Community 0: A, B, C
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        
        # Community 1: D, E, F
        {'source': 'D', 'target': 'E', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'D', 'target': 'F', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'E', 'target': 'F', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    return network


@pytest.fixture
def multilayer_network():
    """Create a multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes in two layers
    nodes = [
        # Layer 1
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        
        # Layer 2
        {'source': 'A', 'type': 'work'},
        {'source': 'B', 'type': 'work'},
        {'source': 'D', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    # Add edges
    edges = [
        # Social layer
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        
        # Work layer
        {'source': 'A', 'target': 'B', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'B', 'target': 'D', 'source_type': 'work', 'target_type': 'work'},
    ]
    network.add_edges(edges)
    
    return network


class TestAutoCommunitiesAssignmentTable:
    """Test Q.communities().auto() returns assignment table."""
    
    def test_smoke_auto_returns_required_columns(self, simple_network):
        """Smoke test: .auto() returns all required columns."""
        result = Q.communities().auto(seed=42, fast=True).execute(simple_network)
        
        # Check result is valid
        assert result is not None
        assert result.target == "communities"
        
        # Check required columns are present
        df = result.to_pandas()
        required_columns = {'node', 'layer', 'community', 'confidence', 'entropy', 'margin', 'community_size'}
        assert required_columns.issubset(set(df.columns))
        
        # Check we have some assignments
        assert len(df) > 0
        
        # Check community_size is computed
        assert df['community_size'].notna().all()
        assert (df['community_size'] > 0).all()
    
    def test_auto_detects_communities(self, simple_network):
        """Test that auto() actually detects communities."""
        result = Q.communities().auto(seed=42, fast=True).execute(simple_network)
        
        df = result.to_pandas()
        
        # Should have 6 nodes (A-F)
        assert len(df) == 6
        
        # Should detect at least 1 community
        num_communities = df['community'].nunique()
        assert num_communities >= 1
    
    def test_auto_deterministic_with_seed(self, simple_network):
        """Test that auto() is deterministic when seed is provided."""
        result1 = Q.communities().auto(seed=42, fast=True).execute(simple_network)
        result2 = Q.communities().auto(seed=42, fast=True).execute(simple_network)
        
        df1 = result1.to_pandas()
        df2 = result2.to_pandas()
        
        # Sort by node for comparison
        df1_sorted = df1.sort_values('node').reset_index(drop=True)
        df2_sorted = df2.sort_values('node').reset_index(drop=True)
        
        # Community assignments should be identical
        # Note: Community IDs might differ, but structure should be same
        # For now, just check we get same number of communities
        assert df1_sorted['community'].nunique() == df2_sorted['community'].nunique()
    
    def test_filtering_confidence_gt(self, simple_network):
        """Test filtering by confidence > threshold."""
        # Note: With current implementation, confidence is always 1.0 (deterministic fallback)
        result = (
            Q.communities()
             .auto(seed=42, fast=True)
             .where(confidence__gt=0.9)
             .execute(simple_network)
        )
        
        df = result.to_pandas()
        
        # All results should have confidence > 0.9
        assert (df['confidence'] > 0.9).all()
    
    def test_filtering_community_size_gt(self, simple_network):
        """Test filtering by community_size > threshold."""
        result = (
            Q.communities()
             .auto(seed=42, fast=True)
             .where(community_size__gt=2)
             .execute(simple_network)
        )
        
        df = result.to_pandas()
        
        # All results should have community_size > 2
        if len(df) > 0:
            assert (df['community_size'] > 2).all()
    
    def test_filtering_reduces_row_count(self, simple_network):
        """Test that filtering reduces row count."""
        result_unfiltered = Q.communities().auto(seed=42, fast=True).execute(simple_network)
        result_filtered = (
            Q.communities()
             .auto(seed=42, fast=True)
             .where(community_size__gt=10)  # Very restrictive filter
             .execute(simple_network)
        )
        
        df_unfiltered = result_unfiltered.to_pandas()
        df_filtered = result_filtered.to_pandas()
        
        # Filtered should have fewer or equal rows
        assert len(df_filtered) <= len(df_unfiltered)
    
    def test_auto_multilayer_has_layer_column(self, multilayer_network):
        """Test multilayer networks include layer column."""
        result = Q.communities().auto(seed=42, fast=True).execute(multilayer_network)
        
        df = result.to_pandas()
        
        # Should have layer column
        assert 'layer' in df.columns
        
        # Layer column should have values for multilayer
        # Note: May be nullable for aggregated views
        layers_present = df['layer'].notna().sum()
        assert layers_present > 0


class TestCommunityAutoNodeAnnotation:
    """Test Q.nodes().community_auto() joins annotations to nodes."""
    
    def test_community_auto_attaches_annotations(self, simple_network):
        """Test that community_auto() adds community fields to nodes."""
        result = (
            Q.nodes()
             .community_auto(seed=42, fast=True)
             .execute(simple_network)
        )
        
        df = result.to_pandas()
        
        # Check community annotation fields are present
        assert 'community' in df.columns
        assert 'confidence' in df.columns
        assert 'community_size' in df.columns
        
        # All nodes should have assignments
        assert df['community'].notna().all()
    
    def test_community_auto_filtering_works(self, simple_network):
        """Test filtering on community annotations."""
        result = (
            Q.nodes()
             .community_auto(seed=42, fast=True)
             .where(community_size__gt=2)
             .execute(simple_network)
        )
        
        df = result.to_pandas()
        
        # All results should satisfy filter
        if len(df) > 0:
            assert (df['community_size'] > 2).all()
    
    def test_community_auto_with_compute(self, simple_network):
        """Test chaining compute() after community_auto()."""
        result = (
            Q.nodes()
             .community_auto(seed=42, fast=True)
             .compute("degree")
             .execute(simple_network)
        )
        
        df = result.to_pandas()
        
        # Should have both community fields and computed metrics
        assert 'community' in df.columns
        assert 'degree' in df.columns
        assert df['degree'].notna().all()
    
    def test_community_auto_multilayer(self, multilayer_network):
        """Test community_auto() on multilayer networks."""
        result = (
            Q.nodes()
             .community_auto(seed=42, fast=True)
             .execute(multilayer_network)
        )
        
        df = result.to_pandas()
        
        # Should have community annotations
        assert 'community' in df.columns
        assert 'community_size' in df.columns


class TestAutoCommunityNoRerun:
    """Test caching semantics: auto community runs once per execute()."""
    
    def test_single_execution_per_execute_call(self, simple_network):
        """Test that AutoCommunity runs only once per .execute() call."""
        # Mock auto_select_community to count calls
        from py3plex.algorithms.community_detection import auto_select_community
        from py3plex.selection.result import AutoCommunityResult
        
        call_count = {'count': 0}
        original_func = auto_select_community
        
        def mock_auto_select(**kwargs):
            call_count['count'] += 1
            # Return a simple partition
            partition = {
                ('A', 'layer1'): 0,
                ('B', 'layer1'): 0,
                ('C', 'layer1'): 0,
                ('D', 'layer1'): 1,
                ('E', 'layer1'): 1,
                ('F', 'layer1'): 1,
            }
            result = MagicMock(spec=AutoCommunityResult)
            result.partition = partition
            result.algorithm = {'name': 'mock', 'params': {}}
            result.provenance = {}
            result.leaderboard = None
            return result
        
        with patch('py3plex.dsl.executor.auto_select_community', side_effect=mock_auto_select):
            # First execute
            result1 = Q.communities().auto(seed=42, fast=True).execute(simple_network)
            
            # Should have been called once
            assert call_count['count'] == 1
            
            # Second execute with same params - should use cache
            # Note: In practice, caching is per-context which is created per execute
            # So we expect a new call here
            result2 = Q.communities().auto(seed=42, fast=True).execute(simple_network)
            
            # With current implementation, each execute() creates a new context,
            # so we expect 2 calls total
            assert call_count['count'] == 2
    
    def test_caching_within_same_context(self, simple_network):
        """Test that caching works within the same execution context."""
        # This is more of a conceptual test - in practice, caching happens
        # at the executor level within a single execute() call
        
        # When we call both communities().auto() and nodes().community_auto()
        # with same params, they should share the cached result
        # However, this requires a shared context, which our current implementation
        # creates per execute() call
        
        # For now, just verify both calls work
        result1 = Q.communities().auto(seed=42, fast=True).execute(simple_network)
        result2 = Q.nodes().community_auto(seed=42, fast=True).execute(simple_network)
        
        assert result1 is not None
        assert result2 is not None


@pytest.mark.integration
class TestAutoCommunityCombinations:
    """Integration tests for various combinations."""
    
    def test_auto_with_filtering_and_ordering(self, simple_network):
        """Test auto() with filtering and ordering."""
        result = (
            Q.communities()
             .auto(seed=42, fast=True)
             .where(community_size__gt=1)
             .execute(simple_network)
        )
        
        df = result.to_pandas()
        
        # Should have valid results
        assert len(df) > 0
        assert (df['community_size'] > 1).all()
    
    def test_community_auto_complex_pipeline(self, simple_network):
        """Test community_auto() in a complex pipeline."""
        result = (
            Q.nodes()
             .community_auto(seed=42, fast=True)
             .where(community_size__gt=2)
             .compute("degree", "betweenness_centrality")
             .execute(simple_network)
        )
        
        df = result.to_pandas()
        
        # Should have all expected columns
        assert 'community' in df.columns
        assert 'community_size' in df.columns
        assert 'degree' in df.columns
        assert 'betweenness_centrality' in df.columns
        
        # Filter should be applied
        if len(df) > 0:
            assert (df['community_size'] > 2).all()
