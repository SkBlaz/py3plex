"""Tests for AutoCommunity .explain() feature.

Tests cover:
- Q.communities().auto().explain()
- Q.nodes().community_auto().explain()
- No re-run of AutoCommunity
- Structured explanation output
- Deterministic results
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q


@pytest.fixture
def simple_network():
    """Create a simple test network."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {"source": f"N{i}", "type": "layer1"} for i in range(10)
    ]
    network.add_nodes(nodes)
    
    edges = [
        {"source": f"N{i}", "target": f"N{i+1}", 
         "source_type": "layer1", "target_type": "layer1"}
        for i in range(9)
    ]
    network.add_edges(edges)
    
    return network


class TestCommunitiesAutoExplain:
    """Test Q.communities().auto().explain()"""
    
    def test_auto_method_exists(self):
        """Test that .auto() method exists on CommunitiesBuilder."""
        builder = Q.communities().auto(seed=42, fast=True)
        
        assert hasattr(builder._select, 'auto_select_config')
        assert builder._select.auto_select_config['enabled'] is True
        assert builder._select.auto_select_config['seed'] == 42
    
    def test_explain_method_exists_after_auto(self):
        """Test that .explain() can be called after .auto()."""
        builder = Q.communities().auto(seed=42, fast=True).explain()
        
        assert hasattr(builder._select, 'auto_select_config')
        assert builder._select.auto_select_config['explain_requested'] is True
    
    @pytest.mark.slow
    def test_auto_explain_returns_explanation(self, simple_network):
        """Test that .auto().explain().execute() returns structured explanation."""
        result = Q.communities().auto(seed=42, fast=True).explain().execute(simple_network)
        
        # Check that result has explanation structure
        assert hasattr(result, 'payload')
        assert hasattr(result, 'tables')
        
        # Check required fields in payload
        assert 'selected' in result.payload
        assert 'uq' in result.payload
        assert 'null_model' in result.payload
        assert 'runtime' in result.payload
        assert 'provenance' in result.payload
        
        # Check selected algorithm info
        selected = result.payload['selected']
        assert 'algorithm' in selected
        assert 'selection_strategy' in selected
        assert 'seed' in selected
        assert selected['seed'] == 42
        assert selected['join_policy'] is None  # Should be None for communities query
    
    @pytest.mark.slow
    def test_auto_explain_has_candidates_table(self, simple_network):
        """Test that explanation includes candidates table."""
        result = Q.communities().auto(seed=42, fast=True).explain().execute(simple_network)
        
        assert 'candidates' in result.tables
        candidates_df = result.tables['candidates']
        assert len(candidates_df) > 0  # Should have at least one candidate


class TestNodesCommunityAutoExplain:
    """Test Q.nodes().community_auto().explain()"""
    
    def test_community_auto_method_exists(self):
        """Test that .community_auto() method exists on QueryBuilder."""
        builder = Q.nodes().community_auto(seed=42, fast=True)
        
        assert hasattr(builder._select, 'community_auto_config')
        assert builder._select.community_auto_config['enabled'] is True
        assert builder._select.community_auto_config['seed'] == 42
    
    def test_explain_method_exists_after_community_auto(self):
        """Test that .explain() can be called after .community_auto()."""
        builder = Q.nodes().community_auto(seed=42, fast=True).explain()
        
        assert hasattr(builder._select, 'community_auto_config')
        assert builder._select.community_auto_config['explain_requested'] is True
    
    @pytest.mark.slow
    def test_community_auto_explain_returns_explanation(self, simple_network):
        """Test that .community_auto().explain().execute() returns structured explanation."""
        result = Q.nodes().community_auto(seed=42, fast=True, join="max_confidence").explain().execute(simple_network)
        
        # Check that result has explanation structure
        assert hasattr(result, 'payload')
        assert hasattr(result, 'tables')
        
        # Check required fields in payload
        assert 'selected' in result.payload
        assert 'uq' in result.payload
        assert 'null_model' in result.payload
        assert 'runtime' in result.payload
        assert 'provenance' in result.payload
        
        # Check selected algorithm info (should include join_policy)
        selected = result.payload['selected']
        assert 'algorithm' in selected
        assert 'selection_strategy' in selected
        assert 'seed' in selected
        assert 'join_policy' in selected
        assert selected['seed'] == 42
        assert selected['join_policy'] == "max_confidence"
    
    @pytest.mark.slow
    def test_community_auto_explain_has_candidates_table(self, simple_network):
        """Test that explanation includes candidates table."""
        result = Q.nodes().community_auto(seed=42, fast=True).explain().execute(simple_network)
        
        assert 'candidates' in result.tables
        candidates_df = result.tables['candidates']
        assert len(candidates_df) > 0  # Should have at least one candidate


class TestNoRerun:
    """Test that .explain() does not re-run AutoCommunity."""
    
    @pytest.mark.slow
    def test_auto_explain_deterministic(self, simple_network):
        """Test that running same query twice gives same results."""
        result1 = Q.communities().auto(seed=42, fast=True).explain().execute(simple_network)
        result2 = Q.communities().auto(seed=42, fast=True).explain().execute(simple_network)
        
        # Same algorithm should be selected
        assert result1.payload['selected']['algorithm'] == result2.payload['selected']['algorithm']
        assert result1.payload['selected']['contestant_id'] == result2.payload['selected']['contestant_id']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
