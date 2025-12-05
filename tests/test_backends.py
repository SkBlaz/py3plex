"""Tests for the backend system."""

import pytest
import networkx as nx

from py3plex.backends import (
    get_backend,
    set_default_backend,
    list_backends,
    is_backend_available,
    BackendNotAvailableError,
)
from py3plex.backends.base import BaseBackend, BackendRegistry
from py3plex.backends.networkx_backend import NetworkXBackend


class TestBackendRegistry:
    """Tests for the BackendRegistry class."""

    def test_register_backend(self):
        """Test registering a backend."""
        registry = BackendRegistry()
        registry.register("test", NetworkXBackend)
        assert "test" in registry.list_backends()

    def test_register_invalid_backend(self):
        """Test that registering a non-BaseBackend class raises TypeError."""
        registry = BackendRegistry()
        with pytest.raises(TypeError):
            registry.register("invalid", str)

    def test_get_backend(self):
        """Test getting a backend by name."""
        registry = BackendRegistry()
        registry.register("networkx", NetworkXBackend)
        backend = registry.get("networkx")
        assert isinstance(backend, NetworkXBackend)

    def test_get_default_backend(self):
        """Test getting the default backend."""
        registry = BackendRegistry()
        registry.register("networkx", NetworkXBackend)
        backend = registry.get()
        assert isinstance(backend, NetworkXBackend)

    def test_get_nonexistent_backend(self):
        """Test that getting a nonexistent backend raises error."""
        registry = BackendRegistry()
        registry.register("networkx", NetworkXBackend)
        with pytest.raises(BackendNotAvailableError):
            registry.get("nonexistent")

    def test_set_default_backend(self):
        """Test setting the default backend."""
        registry = BackendRegistry()
        registry.register("networkx", NetworkXBackend)
        registry.register("test", NetworkXBackend)
        registry.set_default("test")
        assert registry.default == "test"

    def test_set_invalid_default(self):
        """Test that setting nonexistent default raises error."""
        registry = BackendRegistry()
        registry.register("networkx", NetworkXBackend)
        with pytest.raises(BackendNotAvailableError):
            registry.set_default("nonexistent")

    def test_is_available(self):
        """Test checking backend availability."""
        registry = BackendRegistry()
        registry.register("networkx", NetworkXBackend)
        assert registry.is_available("networkx")
        assert not registry.is_available("nonexistent")


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_backend(self):
        """Test get_backend function."""
        backend = get_backend()
        assert isinstance(backend, BaseBackend)
        assert backend.name == "networkx"

    def test_get_backend_by_name(self):
        """Test get_backend with specific name."""
        backend = get_backend("networkx")
        assert backend.name == "networkx"

    def test_list_backends(self):
        """Test list_backends function."""
        backends = list_backends()
        assert "networkx" in backends

    def test_is_backend_available(self):
        """Test is_backend_available function."""
        assert is_backend_available("networkx")


class TestNetworkXBackend:
    """Tests for the NetworkX backend."""

    @pytest.fixture
    def backend(self):
        """Create a NetworkX backend instance."""
        return NetworkXBackend()

    def test_name(self, backend):
        """Test backend name."""
        assert backend.name == "networkx"

    def test_version(self, backend):
        """Test backend version."""
        assert backend.version == nx.__version__

    def test_create_undirected_graph(self, backend):
        """Test creating an undirected graph."""
        g = backend.create_graph(directed=False)
        assert isinstance(g, nx.MultiGraph)
        assert not g.is_directed()

    def test_create_directed_graph(self, backend):
        """Test creating a directed graph."""
        g = backend.create_graph(directed=True)
        assert isinstance(g, nx.MultiDiGraph)
        assert g.is_directed()

    def test_add_node(self, backend):
        """Test adding a node."""
        g = backend.create_graph()
        backend.add_node(g, ('A', 'layer1'), weight=1.0)
        assert backend.has_node(g, ('A', 'layer1'))
        assert backend.number_of_nodes(g) == 1

    def test_add_edge(self, backend):
        """Test adding an edge."""
        g = backend.create_graph()
        backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'), weight=0.5)
        assert backend.has_edge(g, ('A', 'layer1'), ('B', 'layer1'))
        assert backend.number_of_edges(g) == 1

    def test_remove_node(self, backend):
        """Test removing a node."""
        g = backend.create_graph()
        backend.add_node(g, ('A', 'layer1'))
        backend.remove_node(g, ('A', 'layer1'))
        assert not backend.has_node(g, ('A', 'layer1'))

    def test_remove_edge(self, backend):
        """Test removing an edge."""
        g = backend.create_graph()
        backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))
        backend.remove_edge(g, ('A', 'layer1'), ('B', 'layer1'))
        assert not backend.has_edge(g, ('A', 'layer1'), ('B', 'layer1'))

    def test_nodes_iterator(self, backend):
        """Test iterating over nodes."""
        g = backend.create_graph()
        backend.add_node(g, ('A', 'layer1'))
        backend.add_node(g, ('B', 'layer1'))
        nodes = list(backend.nodes(g))
        assert len(nodes) == 2
        assert ('A', 'layer1') in nodes
        assert ('B', 'layer1') in nodes

    def test_nodes_with_data(self, backend):
        """Test iterating over nodes with data."""
        g = backend.create_graph()
        backend.add_node(g, ('A', 'layer1'), weight=1.0)
        nodes = list(backend.nodes(g, data=True))
        assert len(nodes) == 1
        node, data = nodes[0]
        assert node == ('A', 'layer1')
        assert data['weight'] == 1.0

    def test_edges_iterator(self, backend):
        """Test iterating over edges."""
        g = backend.create_graph()
        backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))
        backend.add_edge(g, ('B', 'layer1'), ('C', 'layer1'))
        edges = list(backend.edges(g))
        assert len(edges) == 2

    def test_edges_with_data(self, backend):
        """Test iterating over edges with data."""
        g = backend.create_graph()
        backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'), weight=0.5)
        edges = list(backend.edges(g, data=True))
        assert len(edges) == 1
        source, target, data = edges[0]
        assert data['weight'] == 0.5

    def test_get_layers(self, backend):
        """Test getting layers."""
        g = backend.create_graph()
        backend.add_node(g, ('A', 'layer1'))
        backend.add_node(g, ('B', 'layer2'))
        layers = backend.get_layers(g)
        assert 'layer1' in layers
        assert 'layer2' in layers

    def test_subgraph_by_nodes(self, backend):
        """Test extracting subgraph by nodes."""
        g = backend.create_graph()
        backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))
        backend.add_edge(g, ('B', 'layer1'), ('C', 'layer1'))
        
        subg = backend.subgraph(g, nodes=[('A', 'layer1'), ('B', 'layer1')])
        assert backend.number_of_nodes(subg) == 2
        assert backend.has_node(subg, ('A', 'layer1'))
        assert backend.has_node(subg, ('B', 'layer1'))
        assert not backend.has_node(subg, ('C', 'layer1'))

    def test_subgraph_by_layers(self, backend):
        """Test extracting subgraph by layers."""
        g = backend.create_graph()
        backend.add_node(g, ('A', 'layer1'))
        backend.add_node(g, ('B', 'layer2'))
        
        subg = backend.subgraph(g, layers=['layer1'])
        assert backend.number_of_nodes(subg) == 1
        assert backend.has_node(subg, ('A', 'layer1'))
        assert not backend.has_node(subg, ('B', 'layer2'))

    def test_copy(self, backend):
        """Test copying a graph."""
        g = backend.create_graph()
        backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))
        
        g_copy = backend.copy(g)
        assert backend.number_of_nodes(g_copy) == 2
        assert backend.number_of_edges(g_copy) == 1
        
        # Modify original, copy should be unaffected
        backend.add_node(g, ('C', 'layer1'))
        assert backend.number_of_nodes(g) == 3
        assert backend.number_of_nodes(g_copy) == 2

    def test_to_networkx(self, backend):
        """Test converting to NetworkX."""
        g = backend.create_graph()
        backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))
        
        nx_g = backend.to_networkx(g)
        assert isinstance(nx_g, nx.Graph)
        assert nx_g.number_of_nodes() == 2

    def test_from_networkx(self, backend):
        """Test creating from NetworkX."""
        nx_g = nx.Graph()
        nx_g.add_node(('A', 'layer1'))
        nx_g.add_node(('B', 'layer1'))
        nx_g.add_edge(('A', 'layer1'), ('B', 'layer1'))
        
        g = backend.from_networkx(nx_g)
        assert backend.number_of_nodes(g) == 2
        assert backend.number_of_edges(g) == 1

    def test_neighbors(self, backend):
        """Test getting neighbors."""
        g = backend.create_graph(directed=False)
        backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))
        backend.add_edge(g, ('A', 'layer1'), ('C', 'layer1'))
        
        neighbors = list(backend.neighbors(g, ('A', 'layer1')))
        assert len(neighbors) == 2
        assert ('B', 'layer1') in neighbors
        assert ('C', 'layer1') in neighbors

    def test_degree(self, backend):
        """Test getting node degree."""
        g = backend.create_graph(directed=False)
        backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))
        backend.add_edge(g, ('A', 'layer1'), ('C', 'layer1'))
        
        assert backend.degree(g, ('A', 'layer1')) == 2
        assert backend.degree(g, ('B', 'layer1')) == 1

    def test_is_directed(self, backend):
        """Test checking if graph is directed."""
        g_directed = backend.create_graph(directed=True)
        g_undirected = backend.create_graph(directed=False)
        
        assert backend.is_directed(g_directed)
        assert not backend.is_directed(g_undirected)


class TestPymnetBackend:
    """Tests for the pymnet backend (only run if pymnet is available)."""

    @pytest.fixture
    def backend(self):
        """Create a pymnet backend instance."""
        if not is_backend_available("pymnet"):
            pytest.skip("pymnet not available")
        return get_backend("pymnet")

    @pytest.mark.skipif(
        not is_backend_available("pymnet"),
        reason="pymnet not installed"
    )
    def test_name(self, backend):
        """Test backend name."""
        assert backend.name == "pymnet"

    @pytest.mark.skipif(
        not is_backend_available("pymnet"),
        reason="pymnet not installed"
    )
    def test_create_graph(self, backend):
        """Test creating a graph."""
        g = backend.create_graph(directed=False)
        assert g is not None

    @pytest.mark.skipif(
        not is_backend_available("pymnet"),
        reason="pymnet not installed"
    )
    def test_add_node(self, backend):
        """Test adding a node."""
        g = backend.create_graph()
        backend.add_node(g, ('A', 'layer1'))
        assert backend.has_node(g, ('A', 'layer1'))

    @pytest.mark.skipif(
        not is_backend_available("pymnet"),
        reason="pymnet not installed"
    )
    def test_add_edge(self, backend):
        """Test adding an edge."""
        g = backend.create_graph()
        backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))
        assert backend.has_edge(g, ('A', 'layer1'), ('B', 'layer1'))

    @pytest.mark.skipif(
        not is_backend_available("pymnet"),
        reason="pymnet not installed"
    )
    def test_to_networkx(self, backend):
        """Test converting to NetworkX."""
        g = backend.create_graph(directed=False)
        backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))
        
        nx_g = backend.to_networkx(g)
        assert isinstance(nx_g, nx.Graph)

    @pytest.mark.skipif(
        not is_backend_available("pymnet"),
        reason="pymnet not installed"
    )
    def test_from_networkx(self, backend):
        """Test creating from NetworkX."""
        nx_g = nx.Graph()
        nx_g.add_node(('A', 'layer1'))
        nx_g.add_node(('B', 'layer1'))
        nx_g.add_edge(('A', 'layer1'), ('B', 'layer1'))
        
        g = backend.from_networkx(nx_g)
        # Just verify it doesn't crash - exact behavior may vary
        assert g is not None


class TestBackendInteroperability:
    """Tests for backend interoperability."""

    def test_networkx_to_networkx_roundtrip(self):
        """Test NetworkX -> NetworkX roundtrip."""
        backend = NetworkXBackend()
        
        # Create original graph
        g1 = backend.create_graph(directed=False)
        backend.add_edge(g1, ('A', 'layer1'), ('B', 'layer1'), weight=1.0)
        backend.add_edge(g1, ('B', 'layer1'), ('C', 'layer1'), weight=2.0)
        
        # Convert to NetworkX and back
        nx_g = backend.to_networkx(g1)
        g2 = backend.from_networkx(nx_g)
        
        # Verify structure
        assert backend.number_of_nodes(g1) == backend.number_of_nodes(g2)
        assert backend.number_of_edges(g1) == backend.number_of_edges(g2)

    @pytest.mark.skipif(
        not is_backend_available("pymnet"),
        reason="pymnet not installed"
    )
    def test_networkx_to_pymnet(self):
        """Test converting NetworkX graph to pymnet."""
        nx_backend = get_backend("networkx")
        pymnet_backend = get_backend("pymnet")
        
        # Create graph with NetworkX backend
        g1 = nx_backend.create_graph(directed=False)
        nx_backend.add_edge(g1, ('A', 'layer1'), ('B', 'layer1'))
        
        # Convert to NetworkX and then to pymnet
        nx_g = nx_backend.to_networkx(g1)
        g2 = pymnet_backend.from_networkx(nx_g)
        
        # Basic verification
        assert g2 is not None


class TestConversionFunctions:
    """Tests for to_pymnet and from_pymnet conversion functions."""

    def test_to_pymnet_raises_without_pymnet(self):
        """Test that to_pymnet raises error when pymnet not available."""
        from py3plex.backends import to_pymnet
        from py3plex import multi_layer_network

        if is_backend_available("pymnet"):
            pytest.skip("pymnet is available, cannot test unavailable case")

        net = multi_layer_network()
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'}
        ])

        with pytest.raises(BackendNotAvailableError):
            to_pymnet(net)

    def test_from_pymnet_raises_without_pymnet(self):
        """Test that from_pymnet raises error when pymnet not available."""
        from py3plex.backends import from_pymnet

        if is_backend_available("pymnet"):
            pytest.skip("pymnet is available, cannot test unavailable case")

        with pytest.raises(BackendNotAvailableError):
            from_pymnet(None)

    @pytest.mark.skipif(
        not is_backend_available("pymnet"),
        reason="pymnet not installed"
    )
    def test_to_pymnet_conversion(self):
        """Test converting py3plex network to pymnet."""
        from py3plex.backends import to_pymnet
        from py3plex import multi_layer_network

        # Create py3plex network
        net = multi_layer_network(directed=False)
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])

        # Convert to pymnet
        pymnet_net = to_pymnet(net)
        assert pymnet_net is not None

    @pytest.mark.skipif(
        not is_backend_available("pymnet"),
        reason="pymnet not installed"
    )
    def test_from_pymnet_conversion(self):
        """Test importing pymnet network to py3plex."""
        from py3plex.backends import from_pymnet, get_backend

        # Create a simple pymnet network using the backend
        pymnet_backend = get_backend("pymnet")
        pymnet_net = pymnet_backend.create_graph(directed=False)
        pymnet_backend.add_edge(pymnet_net, ('A', 'layer1'), ('B', 'layer1'))

        # Convert to py3plex
        net = from_pymnet(pymnet_net)
        assert net is not None
        assert hasattr(net, 'core_network')

    @pytest.mark.skipif(
        not is_backend_available("pymnet"),
        reason="pymnet not installed"
    )
    def test_roundtrip_conversion(self):
        """Test py3plex -> pymnet -> py3plex roundtrip."""
        from py3plex.backends import to_pymnet, from_pymnet
        from py3plex import multi_layer_network

        # Create original network
        net1 = multi_layer_network(directed=False)
        net1.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])

        # Convert to pymnet and back
        pymnet_net = to_pymnet(net1)
        net2 = from_pymnet(pymnet_net)

        # Verify basic structure
        assert net2.core_network is not None
