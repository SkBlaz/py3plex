"""Integration tests for semiring algebra DSL (S builder)."""

import pytest
import math
from py3plex.core import multinet
from py3plex.dsl import S, L


@pytest.fixture
def simple_network():
    """Create a simple multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 2.0},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2', 'weight': 3.0},
        # Cross-layer edge
        {'source': 'A', 'target': 'A', 'source_type': 'layer1', 'target_type': 'layer2', 'weight': 0.5},
    ]
    network.add_edges(edges)
    
    return network


class TestSPathsIntegration:
    """Test S.paths() integration with multilayer networks."""
    
    def test_simple_shortest_path(self, simple_network):
        """Test basic shortest path using S builder."""
        result = (
            S.paths()
            .from_node('A')
            .to_node('C')
            .semiring('min_plus')
            .lift(attr='weight', default=1.0)
            .execute(simple_network)
        )
        
        assert result.target == 'paths'
        assert len(result.items) > 0
        
        # Check provenance
        assert 'provenance' in result.meta
        assert 'algebra' in result.meta['provenance']
        assert result.meta['provenance']['algebra']['semiring']['name'] == 'min_plus'
    
    def test_boolean_reachability(self, simple_network):
        """Test reachability with boolean semiring."""
        result = (
            S.paths()
            .from_node('A')
            .semiring('boolean')
            .lift(attr=None, default=True)
            .execute(simple_network)
        )
        
        assert result.target == 'paths'
        
        # Convert to dict for easier checking
        distances = {item['node']: item['value'] for item in result.items}
        
        # A should reach itself and B
        assert distances['A'] == True
        assert distances['B'] == True
    
    def test_max_times_reliability(self, simple_network):
        """Test most reliable path with max_times semiring."""
        # Add reliability attributes
        net = simple_network
        
        result = (
            S.paths()
            .from_node('A')
            .semiring('max_times')
            .lift(attr='weight', default=1.0, transform=lambda x: 1.0/x)  # Invert for reliability
            .execute(net)
        )
        
        assert result.target == 'paths'
        assert 'provenance' in result.meta
    
    def test_layer_filtering(self, simple_network):
        """Test filtering paths by layer."""
        result = (
            S.paths()
            .from_node('A')
            .semiring('min_plus')
            .lift(attr='weight', default=1.0)
            .from_layers(L['layer1'])
            .execute(simple_network)
        )
        
        assert result.target == 'paths'
        # Should only use layer1 edges
        provenance = result.meta['provenance']['algebra']
        assert 'layer1' in provenance['multilayer']['layers_included']
    
    def test_crossing_layers_allowed(self, simple_network):
        """Test allowing cross-layer edges."""
        result = (
            S.paths()
            .from_node('A')
            .semiring('min_plus')
            .lift(attr='weight', default=1.0)
            .crossing_layers(mode='allowed')
            .execute(simple_network)
        )
        
        assert result.target == 'paths'
        provenance = result.meta['provenance']['algebra']
        assert provenance['multilayer']['crossing_layers_mode'] == 'allowed'
    
    def test_max_hops_constraint(self, simple_network):
        """Test maximum hops constraint."""
        result = (
            S.paths()
            .from_node('A')
            .semiring('min_plus')
            .lift(attr='weight', default=1.0)
            .max_hops(1)
            .execute(simple_network)
        )
        
        assert result.target == 'paths'
        provenance = result.meta['provenance']['algebra']
        assert provenance['problem']['max_hops'] == 1
    
    def test_witness_tracking(self, simple_network):
        """Test path reconstruction with witness tracking."""
        result = (
            S.paths()
            .from_node('A')
            .to_node('C')
            .semiring('min_plus')
            .lift(attr='weight', default=1.0)
            .witness(True)
            .execute(simple_network)
        )
        
        assert result.target == 'paths'
        
        # Find C in results
        c_item = None
        for item in result.items:
            if item['node'] == 'C':
                c_item = item
                break
        
        if c_item and c_item.get('path'):
            # Path should exist
            assert c_item['path'][0] == 'A'
            assert c_item['path'][-1] == 'C'


class TestSClosureIntegration:
    """Test S.closure() integration."""
    
    def test_boolean_closure_reachability(self, simple_network):
        """Test reachability closure with boolean semiring."""
        result = (
            S.closure()
            .semiring('boolean')
            .lift(attr=None, default=True)
            .execute(simple_network)
        )
        
        assert result.target == 'closure'
        assert len(result.items) > 0
        
        # Check provenance
        provenance = result.meta['provenance']['algebra']
        assert provenance['semiring']['name'] == 'boolean'
        assert provenance['problem']['kind'] == 'closure'
    
    def test_min_plus_closure_apsp(self, simple_network):
        """Test all-pairs shortest paths with min-plus closure."""
        result = (
            S.closure()
            .semiring('min_plus')
            .lift(attr='weight', default=1.0)
            .method('floyd_warshall')
            .execute(simple_network)
        )
        
        assert result.target == 'closure'
        
        # Should have pairs
        pairs = {(item['source'], item['target']): item['value'] for item in result.items}
        
        # Self-loops should have distance 0
        if ('A', 'A') in pairs:
            assert pairs[('A', 'A')] == 0.0


class TestProvenanceMetadata:
    """Test provenance metadata in algebra results."""
    
    def test_provenance_structure(self, simple_network):
        """Test that provenance has correct structure."""
        result = (
            S.paths()
            .from_node('A')
            .semiring('min_plus')
            .lift(attr='weight', default=1.0)
            .execute(simple_network)
        )
        
        prov = result.meta['provenance']['algebra']
        
        # Check required fields
        assert 'semiring' in prov
        assert 'name' in prov['semiring']
        assert 'properties' in prov['semiring']
        
        assert 'lift' in prov
        assert 'attr' in prov['lift']
        
        assert 'problem' in prov
        assert 'kind' in prov['problem']
        
        assert 'multilayer' in prov
        assert 'backend' in prov
        assert 'performance' in prov
        assert 'determinism' in prov
    
    def test_determinism_metadata(self, simple_network):
        """Test determinism metadata."""
        result = (
            S.paths()
            .from_node('A')
            .semiring('min_plus')
            .lift(attr='weight', default=1.0)
            .execute(simple_network)
        )
        
        determinism = result.meta['provenance']['algebra']['determinism']
        assert 'stable_ordering' in determinism
        assert determinism['stable_ordering'] == True


class TestResultFormats:
    """Test different result output formats."""
    
    def test_to_pandas(self, simple_network):
        """Test converting results to pandas DataFrame."""
        result = (
            S.paths()
            .from_node('A')
            .semiring('min_plus')
            .lift(attr='weight', default=1.0)
            .execute(simple_network)
        )
        
        df = result.to_pandas()
        assert 'node' in df.columns
        assert 'value' in df.columns
        assert len(df) > 0
    
    def test_closure_to_pandas(self, simple_network):
        """Test converting closure results to pandas."""
        result = (
            S.closure()
            .semiring('boolean')
            .lift(attr=None, default=True)
            .execute(simple_network)
        )
        
        df = result.to_pandas()
        assert 'source' in df.columns
        assert 'target' in df.columns
        assert 'value' in df.columns
