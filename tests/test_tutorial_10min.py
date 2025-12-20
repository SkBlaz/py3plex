import importlib.util
import itertools
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "_downloads"
    / "896b3638d484addf6b5766d377915175"
    / "tutorial_10min.py"
)
_MODULE_COUNTER = itertools.count()


def load_module():
    """Load the tutorial module with a unique name to avoid state leakage."""
    module_name = f"tutorial_10min_test_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def tutorial_module():
    return load_module()


def test_example_1_creates_expected_structure(tutorial_module):
    network = tutorial_module.example_1_create_network()

    assert len(list(network.get_nodes())) == 6
    assert len(list(network.get_edges())) == 4
    assert set(network.layers) == {"layer1", "layer2"}


def test_example_2_load_network_handles_missing_dataset(tutorial_module, monkeypatch, capsys):
    missing_path = MODULE_PATH.parent / "nonexistent.txt"
    monkeypatch.setattr(tutorial_module, "DATASET_PATH", missing_path)

    network = tutorial_module.example_2_load_network()
    output = capsys.readouterr().out

    assert network is None
    assert "Warning: Dataset not found" in output
    assert "Skipping this example" in output


def test_example_2_load_network_loads_custom_multiedgelist(monkeypatch, tmp_path):
    module = load_module()
    dataset = tmp_path / "custom_multilayer.txt"
    dataset.write_text(
        "\n".join(
            [
                "u layerX v layerX 1",
                "v layerX w layerX 1",
                "u layerY v layerY 1",
            ]
        )
    )
    monkeypatch.setattr(module, "DATASET_PATH", dataset)

    network = module.example_2_load_network()

    assert network is not None
    assert set(network.layers) == {"layerX", "layerY"}
    assert len(list(network.get_nodes())) == 5
    assert len(list(network.get_edges())) == 3


def test_examples_3_through_5_emit_headings_and_stats(tutorial_module, capsys):
    network = tutorial_module.example_1_create_network()

    tutorial_module.example_3_explore_structure(network)
    tutorial_module.example_4_compute_metrics(network)
    tutorial_module.example_5_multilayer_statistics(network)

    output = capsys.readouterr().out

    assert "Example 3: Exploring Network Structure" in output
    assert "First 5 nodes:" in output
    assert "Example 4: Computing Network Metrics" in output
    assert "Degree centrality" in output
    assert "Betweenness centrality" in output
    assert "Example 5: Multilayer Network Statistics" in output
    assert output.count("density:") >= 2
    assert "Layer diversity (entropy):" in output
    assert "Network Robustness" in output


def test_example_6_community_detection_can_be_stubbed(monkeypatch, capsys):
    module = load_module()
    network = module.example_1_create_network()

    def fake_louvain(net, gamma, omega, random_state):
        nodes = list(net.get_nodes())
        return {node: idx % 2 for idx, node in enumerate(nodes)}

    monkeypatch.setattr(module, "louvain_multilayer", fake_louvain)

    partition = module.example_6_community_detection(network)
    output = capsys.readouterr().out

    assert partition is not None
    assert set(partition.values()) == {0, 1}
    assert "Communities found: 2" in output
    assert "Community sizes" in output


def test_example_7_visualization_saves_outputs(monkeypatch, tmp_path):
    module = load_module()
    network = module.example_1_create_network()
    partition = {node: idx % 2 for idx, node in enumerate(network.get_nodes())}

    import py3plex.visualization.multilayer as multilayer_vis

    calls = []
    monkeypatch.setattr(multilayer_vis, "hairball_plot", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(module, "EXAMPLE_IMAGES_DIR", tmp_path)

    module.example_7_visualization(network, partition)

    assert len(calls) == 2  # one plain and one community plot
    assert (tmp_path / "tutorial_network.png").exists()
    assert (tmp_path / "tutorial_network_communities.png").exists()


def test_complete_example_uses_simple_network_when_dataset_missing(monkeypatch, tmp_path, capsys):
    module = load_module()
    missing_path = tmp_path / "missing.txt"
    monkeypatch.setattr(module, "DATASET_PATH", missing_path)
    monkeypatch.setattr(module, "EXAMPLE_IMAGES_DIR", tmp_path)

    import py3plex.visualization.multilayer as multilayer_vis

    calls = []
    monkeypatch.setattr(multilayer_vis, "hairball_plot", lambda *args, **kwargs: calls.append((args, kwargs)))

    def fake_louvain(net, gamma, omega, random_state):
        return {node: 0 for node in net.get_nodes()}

    monkeypatch.setattr(module, "louvain_multilayer", fake_louvain)

    module.complete_example()
    output = capsys.readouterr().out

    assert "Dataset not found" in output
    assert "Using simple network instead" in output
    assert "Number of communities: 1" in output
    assert len(calls) == 1
    assert (tmp_path / "complete_analysis.png").exists()
