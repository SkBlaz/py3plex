"""Tests for community DSL features.

Tests cover:
- Q.communities() basic queries
- Community filtering
- Community metrics
- Bridge methods (members, boundary_edges)
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, Target, CommunityRecord


@pytest.fixture
def sample_network_with_communities():
    """Create a sample network with assigned communities."""
    network = multinet.multi_layer_network(directed=False)

    # Add nodes in three clear communities
    nodes = [
        # Community 0: A, B, C
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        # Community 1: D, E, F, G
        {'source': 'D', 'type': 'social'},
        {'source': 'E', 'type': 'social'},
        {'source': 'F', 'type': 'social'},
        {'source': 'G', 'type': 'social'},
        # Community 2: H, I
        {'source': 'H', 'type': 'social'},
        {'source': 'I', 'type': 'social'},
    ]
    network.add_nodes(nodes)

    # Add edges within communities
    edges = [
        # Community 0: densely connected
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        
        # Community 1: densely connected
        {'source': 'D', 'target': 'E', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'D', 'target': 'F', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'D', 'target': 'G', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'E', 'target': 'F', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'E', 'target': 'G', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'F', 'target': 'G', 'source_type': 'social', 'target_type': 'social'},
        
        # Community 2: single edge
        {'source': 'H', 'target': 'I', 'source_type': 'social', 'target_type': 'social'},
        
        # Inter-community edges
        {'source': 'C', 'target': 'D', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'G', 'target': 'H', 'source_type': 'social', 'target_type': 'social'},
    ]
    network.add_edges(edges)

    # Assign partition
    partition = {
        ('A', 'social'): 0,
        ('B', 'social'): 0,
        ('C', 'social'): 0,
        ('D', 'social'): 1,
        ('E', 'social'): 1,
        ('F', 'social'): 1,
        ('G', 'social'): 1,
        ('H', 'social'): 2,
        ('I', 'social'): 2,
    }
    network.assign_partition(partition)

    return network


class TestCommunityQueries:
    """Test basic community query functionality."""
    
    def test_communities_basic(self, sample_network_with_communities):
        """Test basic community query."""
        result = Q.communities().execute(sample_network_with_communities)
        
        assert result.target == "communities"
        assert len(result.items) == 3  # Three communities
        assert set(result.items) == {0, 1, 2}
    
    def test_communities_with_size_filter(self, sample_network_with_communities):
        """Test filtering communities by size."""
        # Get communities with more than 2 members
        result = Q.communities().where(size__gt=2).execute(sample_network_with_communities)
        
        assert len(result.items) == 2  # Communities 0 and 1
        assert set(result.items) == {0, 1}
    
    def test_communities_compute_conductance(self, sample_network_with_communities):
        """Test computing conductance for communities."""
        result = (
            Q.communities()
            .compute("conductance")
            .execute(sample_network_with_communities)
        )
        
        # Check that conductance was computed
        assert "conductance" in result.attributes
        assert len(result.attributes["conductance"]) == 3
    
    def test_communities_order_by_size(self, sample_network_with_communities):
        """Test ordering communities by size."""
        result = (
            Q.communities()
            .order_by("size", desc=True)
            .execute(sample_network_with_communities)
        )
        
        # Largest community should be first
        assert result.items[0] == 1  # Community 1 has 4 members
        assert result.items[1] == 0  # Community 0 has 3 members
        assert result.items[2] == 2  # Community 2 has 2 members
    
    def test_communities_limit(self, sample_network_with_communities):
        """Test limiting number of communities returned."""
        result = (
            Q.communities()
            .order_by("size", desc=True)
            .limit(2)
            .execute(sample_network_with_communities)
        )
        
        assert len(result.items) == 2
        assert result.items == [1, 0]  # Two largest communities
    
    def test_communities_to_pandas(self, sample_network_with_communities):
        """Test exporting community results to pandas."""
        result = Q.communities().execute(sample_network_with_communities)
        df = result.to_pandas()
        
        assert len(df) == 3
        assert 'community_id' in df.columns
        assert 'size' in df.columns
        assert 'density_intra' in df.columns
        assert set(df['community_id']) == {0, 1, 2}


class TestCommunityAttributes:
    """Test community attribute access."""
    
    def test_community_has_builtin_attributes(self, sample_network_with_communities):
        """Test that communities have built-in attributes."""
        result = Q.communities().execute(sample_network_with_communities)
        
        # Check built-in attributes are present
        assert 'size' in result.attributes
        assert 'intra_edges' in result.attributes
        assert 'inter_edges' in result.attributes
        assert 'density_intra' in result.attributes
        assert 'cut_size' in result.attributes
        assert 'layer_scope' in result.attributes


class TestNamedPartitions:
    """Test named partition support."""
    
    def test_multiple_partitions(self, sample_network_with_communities):
        """Test storing and querying multiple partitions."""
        network = sample_network_with_communities
        
        # Create a second partition with different assignments
        partition2 = {
            ('A', 'social'): 0,
            ('B', 'social'): 0,
            ('C', 'social'): 1,
            ('D', 'social'): 1,
            ('E', 'social'): 1,
            ('F', 'social'): 2,
            ('G', 'social'): 2,
            ('H', 'social'): 2,
            ('I', 'social'): 2,
        }
        network.assign_partition(partition2, name="alternative")
        
        # Query default partition
        result_default = Q.communities().execute(network)
        assert len(result_default.items) == 3
        
        # Query alternative partition
        result_alt = Q.communities(partition="alternative").execute(network)
        assert len(result_alt.items) == 3
        
        # Lists of partitions
        partitions = network.list_partitions()
        assert "default" in partitions
        assert "alternative" in partitions


class TestCommunityBridges:
    """Test bridge methods between communities and nodes/edges."""
    
    def test_communities_members_structure(self, sample_network_with_communities):
        """Test that .members() returns a node query builder."""
        builder = Q.communities().where(size__gt=2).members()
        
        # Check that it returns a QueryBuilder with NODES target
        assert hasattr(builder, '_select')
        assert builder._select.target == Target.NODES
    
    def test_communities_members_execution(self, sample_network_with_communities):
        """Test that .members() actually returns member nodes."""
        result = Q.communities().where(size__gt=2).members().execute(sample_network_with_communities)
        
        # Should get members of communities 0 and 1 (size > 2)
        # Community 0: A, B, C (3 members)
        # Community 1: D, E, F, G (4 members)
        # Total: 7 members
        assert result.target == "nodes"
        assert len(result.items) == 7
        
        # Extract node names
        node_names = {item[0] for item in result.items}
        expected = {'A', 'B', 'C', 'D', 'E', 'F', 'G'}
        assert node_names == expected
    
    def test_communities_members_with_compute(self, sample_network_with_communities):
        """Test computing metrics on community members."""
        result = (
            Q.communities()
            .where(size__eq=3)  # Community 0
            .members()
            .compute("degree")
            .execute(sample_network_with_communities)
        )
        
        assert result.target == "nodes"
        assert len(result.items) == 3
        assert "degree" in result.attributes
    
    def test_communities_boundary_edges_structure(self, sample_network_with_communities):
        """Test that .boundary_edges() returns an edge query builder."""
        builder = Q.communities().boundary_edges()
        
        # Check that it returns a QueryBuilder with EDGES target
        assert hasattr(builder, '_select')
        assert builder._select.target == Target.EDGES
    
    def test_communities_boundary_edges_execution(self, sample_network_with_communities):
        """Test that .boundary_edges() returns inter-community edges."""
        result = Q.communities().boundary_edges().execute(sample_network_with_communities)
        
        # Should get the two inter-community edges: C-D and G-H
        assert result.target == "edges"
        assert len(result.items) == 2
        
        # Extract edge info
        edges_set = set()
        for edge in result.items:
            src, dst = edge[0], edge[1]
            src_name = src[0] if isinstance(src, tuple) else src
            dst_name = dst[0] if isinstance(dst, tuple) else dst
            edges_set.add(tuple(sorted([src_name, dst_name])))
        
        expected = {('C', 'D'), ('G', 'H')}
        assert edges_set == expected


class TestCommunityErrors:
    """Test error handling for community queries."""
    
    def test_missing_partition_error(self):
        """Test that querying without a partition gives a clear error."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{'source': 'A', 'type': 'social'}])
        
        from py3plex.dsl.errors import DslExecutionError
        
        with pytest.raises(DslExecutionError) as exc_info:
            Q.communities().execute(network)
        
        assert "No partition named 'default' found" in str(exc_info.value)
        assert "assign_partition" in str(exc_info.value)
