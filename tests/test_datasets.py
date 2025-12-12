"""
Tests for py3plex.datasets module.

This module tests the built-in datasets functionality, including:
- Loading bundled datasets (Aarhus CS, synthetic multilayer)
- Generating synthetic networks
- Utility functions (list_datasets, get_data_dir)
"""

import os

import pytest

import py3plex.datasets._loaders as loader_module
from py3plex.datasets import (
    fetch_multilayer,
    get_data_dir,
    list_datasets,
    list_multilayer,
    load_aarhus_cs,
    load_synthetic_multilayer,
    make_clique_multiplex,
    make_random_multilayer,
    make_random_multiplex,
    make_social_network,
)


class TestDataLoaders:
    """Tests for built-in dataset loaders."""

    def test_get_data_dir_returns_path(self):
        """get_data_dir should return a valid path."""
        data_dir = get_data_dir()
        assert isinstance(data_dir, str)
        assert os.path.isdir(data_dir)

    def test_get_data_dir_includes_bundled_edge_files(self):
        """Bundled dataset edge files should exist in the data directory."""
        data_dir = get_data_dir()
        for filename in ("aarhus_cs.edges", "synthetic_multilayer.edges"):
            path = os.path.join(data_dir, filename)
            assert os.path.isfile(path), f"Expected bundled file missing: {path}"

    def test_list_datasets_returns_list(self):
        """list_datasets should return a list of tuples."""
        datasets = list_datasets()
        assert isinstance(datasets, list)
        assert len(datasets) >= 2  # At least aarhus_cs and synthetic_multilayer
        for name, desc in datasets:
            assert isinstance(name, str)
            assert isinstance(desc, str)
            assert len(name) > 0
            assert len(desc) > 0

    def test_list_multilayer_includes_all_registered(self):
        """list_multilayer should list all fetchable dataset names."""
        available = dict(list_multilayer())
        for required in ("aarhus_cs", "synthetic_multilayer", "human_ppi_gene_disease_drug"):
            assert required in available

    def test_load_aarhus_cs_basic(self):
        """load_aarhus_cs should return a valid network."""
        net = load_aarhus_cs()
        nodes = list(net.get_nodes())
        edges = list(net.get_edges())
        layers = net.get_layers()
        
        assert len(nodes) > 0, "Network should have nodes"
        assert len(edges) > 0, "Network should have edges"
        assert len(layers) > 0, "Network should have layers"

    def test_load_aarhus_cs_layer_count(self):
        """Aarhus CS should have 5 layers."""
        net = load_aarhus_cs()
        layers = net.get_layers()
        # get_layers() returns tuple (layer_names, layer_graphs) or just layer_names
        layer_names = layers[0] if isinstance(layers, tuple) else layers
        assert len(layer_names) == 5, f"Expected 5 layers, got {len(layer_names)}"

    def test_load_aarhus_cs_directed(self):
        """load_aarhus_cs with directed=True should work."""
        net = load_aarhus_cs(directed=True)
        nodes = list(net.get_nodes())
        assert len(nodes) > 0

    def test_load_aarhus_cs_missing_file_raises(self, monkeypatch):
        """Missing bundled file should raise FileNotFoundError."""
        monkeypatch.setattr(
            "py3plex.datasets._loaders.os.path.exists", lambda path: False
        )
        with pytest.raises(FileNotFoundError):
            load_aarhus_cs()

    def test_load_synthetic_multilayer_basic(self):
        """load_synthetic_multilayer should return a valid network."""
        net = load_synthetic_multilayer()
        nodes = list(net.get_nodes())
        edges = list(net.get_edges())
        layers = net.get_layers()
        
        assert len(nodes) > 0, "Network should have nodes"
        assert len(edges) > 0, "Network should have edges"
        assert len(layers) > 0, "Network should have layers"

    def test_load_synthetic_multilayer_layer_count(self):
        """Synthetic multilayer should have 3 layers."""
        net = load_synthetic_multilayer()
        layers = net.get_layers()
        # get_layers() returns tuple (layer_names, layer_graphs) or just layer_names
        layer_names = layers[0] if isinstance(layers, tuple) else layers
        assert len(layer_names) == 3, f"Expected 3 layers, got {len(layer_names)}"

    def test_load_synthetic_multilayer_missing_file_raises(self, monkeypatch):
        """Missing synthetic file should raise FileNotFoundError."""
        monkeypatch.setattr(
            "py3plex.datasets._loaders.os.path.exists", lambda path: False
        )
        with pytest.raises(FileNotFoundError):
            load_synthetic_multilayer()

    def test_fetch_multilayer_unknown_dataset_raises(self):
        """Unknown dataset names should raise ValueError with available names."""
        with pytest.raises(ValueError) as err:
            fetch_multilayer("missing_dataset")
        assert "Unknown dataset" in str(err.value)
        assert "synthetic_multilayer" in str(err.value)

    def test_fetch_multilayer_uses_loader_and_forwards_directed(self, monkeypatch):
        """fetch_multilayer should dispatch to loader with directed flag."""
        sentinel = object()
        recorded = {}

        def fake_loader(*, directed):
            recorded["directed"] = directed
            return sentinel

        monkeypatch.setattr(loader_module, "load_aarhus_cs", fake_loader)

        result = fetch_multilayer("aarhus_cs", directed=True)

        assert result is sentinel
        assert recorded["directed"] is True


class TestSyntheticGenerators:
    """Tests for synthetic network generators."""

    def test_make_random_multilayer_basic(self):
        """make_random_multilayer should generate a network."""
        net = make_random_multilayer(n_nodes=30, n_layers=3, p=0.1)
        nodes = list(net.get_nodes())
        assert len(nodes) > 0

    def test_make_random_multilayer_directed_graph(self):
        """Directed multilayer generation should produce directed core_network."""
        net = make_random_multilayer(
            n_nodes=10, n_layers=2, p=0.2, directed=True, random_state=0
        )
        assert net.core_network.is_directed()

    def test_make_random_multilayer_reproducibility(self):
        """make_random_multilayer with random_state should be reproducible."""
        net1 = make_random_multilayer(n_nodes=20, n_layers=2, p=0.1, random_state=42)
        net2 = make_random_multilayer(n_nodes=20, n_layers=2, p=0.1, random_state=42)
        
        nodes1 = set(net1.get_nodes())
        nodes2 = set(net2.get_nodes())
        assert nodes1 == nodes2, "Same random_state should produce same nodes"

    def test_make_random_multilayer_validation(self):
        """make_random_multilayer should validate inputs."""
        with pytest.raises(ValueError):
            make_random_multilayer(n_nodes=0, n_layers=3, p=0.1)
        with pytest.raises(ValueError):
            make_random_multilayer(n_nodes=30, n_layers=0, p=0.1)
        with pytest.raises(ValueError):
            make_random_multilayer(n_nodes=30, n_layers=3, p=-0.1)
        with pytest.raises(ValueError):
            make_random_multilayer(n_nodes=30, n_layers=3, p=1.5)

    def test_make_random_multiplex_basic(self):
        """make_random_multiplex should generate a network."""
        net = make_random_multiplex(n_nodes=20, n_layers=3, p=0.1)
        nodes = list(net.get_nodes())
        layers = net.get_layers()
        
        assert len(nodes) > 0
        assert len(layers) == 3

    def test_make_random_multiplex_directed(self):
        """make_random_multiplex should support directed networks."""
        net = make_random_multiplex(n_nodes=15, n_layers=2, p=0.15, directed=True)
        nodes = list(net.get_nodes())
        assert len(nodes) > 0

    def test_make_random_multiplex_validation(self):
        """make_random_multiplex should validate inputs."""
        with pytest.raises(ValueError):
            make_random_multiplex(n_nodes=-5, n_layers=3, p=0.1)
        with pytest.raises(ValueError):
            make_random_multiplex(n_nodes=5, n_layers=1, p=2)
        with pytest.raises(ValueError):
            make_random_multiplex(n_nodes=5, n_layers=1, p=-0.5)

    def test_make_clique_multiplex_basic(self):
        """make_clique_multiplex should generate a network with cliques."""
        net = make_clique_multiplex(n_nodes=15, n_layers=2, clique_size=4, n_cliques=3)
        nodes = list(net.get_nodes())
        edges = list(net.get_edges())
        
        assert len(nodes) > 0
        assert len(edges) > 0

    def test_make_clique_multiplex_reproducibility(self):
        """make_clique_multiplex with random_state should be reproducible."""
        net1 = make_clique_multiplex(n_nodes=10, n_layers=2, random_state=123)
        net2 = make_clique_multiplex(n_nodes=10, n_layers=2, random_state=123)
        
        edges1 = set(net1.get_edges())
        edges2 = set(net2.get_edges())
        assert edges1 == edges2

    def test_make_clique_multiplex_validation(self):
        """make_clique_multiplex should validate inputs."""
        with pytest.raises(ValueError):
            make_clique_multiplex(n_nodes=0)
        with pytest.raises(ValueError):
            make_clique_multiplex(n_nodes=10, n_layers=0)
        with pytest.raises(ValueError):
            make_clique_multiplex(n_nodes=10, clique_size=-1)

    def test_make_social_network_basic(self):
        """make_social_network should generate a social network."""
        net = make_social_network(n_people=25)
        nodes = list(net.get_nodes())
        layers = net.get_layers()
        
        assert len(nodes) > 0
        assert len(layers) == 3  # friendship, work, family

    def test_make_social_network_layer_names(self):
        """make_social_network should have named layers."""
        net = make_social_network(n_people=20, random_state=42)
        layers = net.get_layers()
        
        # Layers should be friendship=0, work=1, family=2
        assert len(layers) == 3

    def test_make_social_network_reproducibility(self):
        """make_social_network with random_state should be reproducible."""
        net1 = make_social_network(n_people=15, random_state=99)
        net2 = make_social_network(n_people=15, random_state=99)
        
        nodes1 = set(net1.get_nodes())
        nodes2 = set(net2.get_nodes())
        assert nodes1 == nodes2

    def test_make_social_network_validation(self):
        """make_social_network should validate inputs."""
        with pytest.raises(ValueError):
            make_social_network(n_people=0)
        with pytest.raises(ValueError):
            make_social_network(n_people=-10)


class TestDatasetIntegration:
    """Integration tests for datasets with other py3plex features."""

    def test_loaded_dataset_can_compute_stats(self):
        """Loaded datasets should work with basic_stats()."""
        net = load_aarhus_cs()
        # Should not raise
        net.basic_stats()

    def test_generated_network_can_compute_stats(self):
        """Generated networks should work with basic_stats()."""
        net = make_random_multilayer(n_nodes=20, n_layers=2, random_state=42)
        # Should not raise
        net.basic_stats()

    def test_loaded_dataset_with_dsl(self):
        """Loaded datasets should work with DSL queries."""
        from py3plex.dsl import execute_query
        
        net = load_synthetic_multilayer()
        result = execute_query(net, "SELECT nodes")
        assert result["count"] > 0

    def test_generated_network_with_dsl(self):
        """Generated networks should work with DSL queries."""
        from py3plex.dsl import execute_query
        
        net = make_random_multiplex(n_nodes=15, n_layers=2, p=0.2, random_state=42)
        result = execute_query(net, "SELECT nodes")
        assert result["count"] > 0
