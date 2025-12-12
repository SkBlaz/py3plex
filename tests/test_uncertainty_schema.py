"""Tests for uncertainty.schema module (canonical attribute names)."""

import pytest

from py3plex.uncertainty import schema
from py3plex.uncertainty.models import UncertainValue


class TestSchemaConstants:
    """Test that all schema constants are defined."""
    
    def test_edge_constants(self):
        """Test edge attribute constants."""
        assert schema.WEIGHT == "weight"
        assert schema.WEIGHT_MEAN == "weight_mean"
        assert schema.WEIGHT_VAR == "weight_var"
        assert schema.WEIGHT_STD == "weight_std"
        assert schema.WEIGHT_DIST == "weight_dist"
        assert schema.P_EXIST == "p_exist"
        assert schema.CERTAINTY == "certainty"
    
    def test_node_constants(self):
        """Test node attribute constants."""
        assert schema.NODE_P_EXIST == "p_exist"
    
    def test_stat_constants(self):
        """Test computed statistic constants."""
        assert schema.CENTRALITY_MEAN == "centrality_mean"
        assert schema.CENTRALITY_STD == "centrality_std"
        assert schema.CENTRALITY_DIST == "centrality_dist"
        assert schema.COMMUNITY_LABEL == "community"
        assert schema.COMMUNITY_STABILITY == "community_stability"
    
    def test_metadata_constants(self):
        """Test metadata constants."""
        assert schema.UNCERTAINTY_SOURCE == "uncertainty_source"
        assert schema.N_SAMPLES == "n_samples"
        assert schema.CONFIDENCE_LEVEL == "confidence_level"


class TestSchemaAttributeSets:
    """Test attribute sets for validation."""
    
    def test_edge_uncertainty_attrs(self):
        """Test edge uncertainty attribute set."""
        attrs = schema.EDGE_UNCERTAINTY_ATTRS
        assert schema.WEIGHT_MEAN in attrs
        assert schema.WEIGHT_VAR in attrs
        assert schema.P_EXIST in attrs
        assert schema.CERTAINTY in attrs
        # Regular weight is NOT an uncertainty attribute
        assert schema.WEIGHT not in attrs
    
    def test_node_uncertainty_attrs(self):
        """Test node uncertainty attribute set."""
        attrs = schema.NODE_UNCERTAINTY_ATTRS
        assert schema.NODE_P_EXIST in attrs
    
    def test_stat_uncertainty_attrs(self):
        """Test stat uncertainty attribute set."""
        attrs = schema.STAT_UNCERTAINTY_ATTRS
        assert schema.CENTRALITY_MEAN in attrs
        assert schema.CENTRALITY_STD in attrs
        assert schema.COMMUNITY_STABILITY in attrs
    
    def test_metadata_attrs(self):
        """Test metadata attribute set."""
        attrs = schema.METADATA_ATTRS
        assert schema.UNCERTAINTY_SOURCE in attrs
        assert schema.N_SAMPLES in attrs
        assert schema.CONFIDENCE_LEVEL in attrs
    
    def test_all_uncertainty_attrs(self):
        """Test that all uncertainty attrs is union of all sets."""
        all_attrs = schema.ALL_UNCERTAINTY_ATTRS
        
        # Check that each category is included
        for attr in schema.EDGE_UNCERTAINTY_ATTRS:
            assert attr in all_attrs
        for attr in schema.NODE_UNCERTAINTY_ATTRS:
            assert attr in all_attrs
        for attr in schema.STAT_UNCERTAINTY_ATTRS:
            assert attr in all_attrs
        for attr in schema.METADATA_ATTRS:
            assert attr in all_attrs


class TestIsUncertaintyAttr:
    """Test is_uncertainty_attr function."""
    
    def test_edge_uncertainty_attrs(self):
        """Test edge uncertainty attributes."""
        assert schema.is_uncertainty_attr("weight_mean")
        assert schema.is_uncertainty_attr("weight_var")
        assert schema.is_uncertainty_attr("p_exist")
        assert schema.is_uncertainty_attr("certainty")
    
    def test_node_uncertainty_attrs(self):
        """Test node uncertainty attributes."""
        assert schema.is_uncertainty_attr("p_exist")
    
    def test_stat_uncertainty_attrs(self):
        """Test stat uncertainty attributes."""
        assert schema.is_uncertainty_attr("centrality_mean")
        assert schema.is_uncertainty_attr("centrality_std")
    
    def test_non_uncertainty_attrs(self):
        """Test non-uncertainty attributes."""
        assert not schema.is_uncertainty_attr("weight")
        assert not schema.is_uncertainty_attr("label")
        assert not schema.is_uncertainty_attr("color")
        assert not schema.is_uncertainty_attr("random_attr")


class TestIsDeterministicEdge:
    """Test is_deterministic_edge function."""
    
    def test_deterministic_edge(self):
        """Test deterministic edge (no uncertainty attrs)."""
        edge_data = {"weight": 1.0, "label": "A"}
        assert schema.is_deterministic_edge(edge_data)
    
    def test_uncertain_edge_weight_mean(self):
        """Test uncertain edge with weight_mean."""
        edge_data = {"weight_mean": 1.0, "weight_var": 0.1}
        assert not schema.is_deterministic_edge(edge_data)
    
    def test_uncertain_edge_p_exist(self):
        """Test uncertain edge with p_exist."""
        edge_data = {"p_exist": 0.8}
        assert not schema.is_deterministic_edge(edge_data)
    
    def test_uncertain_edge_certainty(self):
        """Test uncertain edge with certainty (legacy)."""
        edge_data = {"certainty": 0.9}
        assert not schema.is_deterministic_edge(edge_data)
    
    def test_uncertain_edge_weight_dist(self):
        """Test uncertain edge with weight_dist."""
        edge_data = {"weight_dist": UncertainValue(kind="normal", params={"mu": 1.0, "sigma": 0.1})}
        assert not schema.is_deterministic_edge(edge_data)
    
    def test_empty_edge(self):
        """Test empty edge data."""
        assert schema.is_deterministic_edge({})


class TestIsDeterministicNode:
    """Test is_deterministic_node function."""
    
    def test_deterministic_node(self):
        """Test deterministic node (no uncertainty attrs)."""
        node_data = {"label": "A", "color": "red"}
        assert schema.is_deterministic_node(node_data)
    
    def test_uncertain_node(self):
        """Test uncertain node with p_exist."""
        node_data = {"p_exist": 0.95}
        assert not schema.is_deterministic_node(node_data)
    
    def test_empty_node(self):
        """Test empty node data."""
        assert schema.is_deterministic_node({})


class TestGetEdgeWeight:
    """Test get_edge_weight function."""
    
    def test_deterministic_weight(self):
        """Test getting deterministic weight."""
        edge_data = {"weight": 2.0}
        assert schema.get_edge_weight(edge_data) == 2.0
    
    def test_weight_mean(self):
        """Test getting weight from weight_mean."""
        edge_data = {"weight_mean": 3.5}
        assert schema.get_edge_weight(edge_data) == 3.5
    
    def test_weight_dist(self):
        """Test getting weight from weight_dist."""
        v = UncertainValue(kind="normal", params={"mu": 4.5, "sigma": 0.5})
        edge_data = {"weight_dist": v}
        assert schema.get_edge_weight(edge_data) == 4.5
    
    def test_default_weight(self):
        """Test default weight when no weight attribute."""
        edge_data = {"label": "A"}
        assert schema.get_edge_weight(edge_data) == 1.0
        assert schema.get_edge_weight(edge_data, default=2.0) == 2.0
    
    def test_priority_weight_over_weight_mean(self):
        """Test that 'weight' has priority over 'weight_mean'."""
        edge_data = {"weight": 2.0, "weight_mean": 3.0}
        assert schema.get_edge_weight(edge_data) == 2.0
    
    def test_priority_weight_mean_over_weight_dist(self):
        """Test that 'weight_mean' has priority over 'weight_dist'."""
        v = UncertainValue(kind="normal", params={"mu": 4.0, "sigma": 0.5})
        edge_data = {"weight_mean": 3.0, "weight_dist": v}
        assert schema.get_edge_weight(edge_data) == 3.0


class TestGetEdgeExistenceProb:
    """Test get_edge_existence_prob function."""
    
    def test_p_exist(self):
        """Test getting p_exist."""
        edge_data = {"p_exist": 0.8}
        assert schema.get_edge_existence_prob(edge_data) == 0.8
    
    def test_certainty_legacy(self):
        """Test getting certainty (legacy)."""
        edge_data = {"certainty": 0.9}
        assert schema.get_edge_existence_prob(edge_data) == 0.9
    
    def test_default_existence_prob(self):
        """Test default existence probability."""
        edge_data = {"weight": 1.0}
        assert schema.get_edge_existence_prob(edge_data) == 1.0
        assert schema.get_edge_existence_prob(edge_data, default=0.5) == 0.5
    
    def test_priority_p_exist_over_certainty(self):
        """Test that 'p_exist' has priority over 'certainty'."""
        edge_data = {"p_exist": 0.8, "certainty": 0.9}
        assert schema.get_edge_existence_prob(edge_data) == 0.8


class TestGetNodeExistenceProb:
    """Test get_node_existence_prob function."""
    
    def test_p_exist(self):
        """Test getting node p_exist."""
        node_data = {"p_exist": 0.95}
        assert schema.get_node_existence_prob(node_data) == 0.95
    
    def test_default_existence_prob(self):
        """Test default node existence probability."""
        node_data = {"label": "A"}
        assert schema.get_node_existence_prob(node_data) == 1.0
        assert schema.get_node_existence_prob(node_data, default=0.5) == 0.5


class TestSchemaIntegration:
    """Integration tests for schema usage."""
    
    def test_create_uncertain_edge_data(self):
        """Test creating uncertain edge data with schema constants."""
        edge_data = {
            schema.WEIGHT_MEAN: 2.5,
            schema.WEIGHT_VAR: 0.1,
            schema.P_EXIST: 0.9,
            schema.UNCERTAINTY_SOURCE: "bootstrap",
            schema.N_SAMPLES: 100,
        }
        
        # Check that it's recognized as uncertain
        assert not schema.is_deterministic_edge(edge_data)
        
        # Check accessor functions
        assert schema.get_edge_weight(edge_data) == 2.5
        assert schema.get_edge_existence_prob(edge_data) == 0.9
    
    def test_create_uncertain_node_data(self):
        """Test creating uncertain node data with schema constants."""
        node_data = {
            schema.NODE_P_EXIST: 0.85,
            "label": "Node A",
        }
        
        # Check that it's recognized as uncertain
        assert not schema.is_deterministic_node(node_data)
        
        # Check accessor function
        assert schema.get_node_existence_prob(node_data) == 0.85
    
    def test_create_stat_data_with_uncertainty(self):
        """Test creating stat data with schema constants."""
        stat_data = {
            schema.CENTRALITY_MEAN: 0.25,
            schema.CENTRALITY_STD: 0.05,
            schema.UNCERTAINTY_SOURCE: "perturbation",
            schema.N_SAMPLES: 50,
            schema.CONFIDENCE_LEVEL: 0.95,
        }
        
        # All stat uncertainty attributes should be recognized
        assert schema.is_uncertainty_attr(schema.CENTRALITY_MEAN)
        assert schema.is_uncertainty_attr(schema.CENTRALITY_STD)
    
    def test_backward_compat_certainty(self):
        """Test backward compatibility with 'certainty' attribute."""
        # Old code might use 'certainty'
        edge_data_old = {"certainty": 0.7}
        
        # Should be recognized as uncertain
        assert not schema.is_deterministic_edge(edge_data_old)
        
        # Should be accessible via get_edge_existence_prob
        assert schema.get_edge_existence_prob(edge_data_old) == 0.7
        
        # New code should use 'p_exist'
        edge_data_new = {schema.P_EXIST: 0.7}
        assert schema.get_edge_existence_prob(edge_data_new) == 0.7
