import importlib

import matplotlib.pyplot as plt
import pytest


MODULE_PATH = "docfiles.generate_visualization_images"


@pytest.fixture(scope="module")
def viz_module():
    # Import the module once to reuse patched functions across tests.
    return importlib.import_module(MODULE_PATH)


def test_save_figure_writes_file_and_closes(viz_module, tmp_path, capsys):
    # Redirect output directory to temporary path
    viz_module.OUTPUT_DIR = tmp_path

    plt.figure()
    viz_module.save_figure("test_image.png", dpi=50)

    saved_file = tmp_path / "test_image.png"
    assert saved_file.exists()

    # matplotlib should close the figure after saving
    assert plt.get_fignums() == []

    captured = capsys.readouterr()
    assert f"[OK] Saved: {saved_file}" in captured.out


def test_main_generates_all_images_with_stubs(monkeypatch, viz_module, tmp_path, capsys):
    # Capture save calls to ensure each generator attempts to write a file
    saved_files = []

    def fake_save_figure(filename, dpi=150, bbox_inches="tight"):
        path = tmp_path / filename
        path.write_text("stub")
        saved_files.append(path.name)

    monkeypatch.setattr(viz_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(viz_module, "save_figure", fake_save_figure)

    # Ensure dataset checks fall back to synthetic generation
    monkeypatch.setattr(viz_module.os.path, "exists", lambda _: False)
    monkeypatch.setattr(viz_module, "get_dataset_path", lambda name: tmp_path / name)

    # Stub out the heavy visualization helpers to just record calls
    viz_calls = []
    draw_calls = []

    def fake_visualize(network, visualization_type=None, **kwargs):
        viz_calls.append(visualization_type)
        return "fig"

    def fake_draw(graphs, **kwargs):
        draw_calls.append(kwargs)
        return "ax"

    monkeypatch.setattr(viz_module, "visualize_multilayer_network", fake_visualize)
    monkeypatch.setattr(viz_module, "draw_multilayer_default", fake_draw)

    # Provide lightweight network objects
    style_calls = []

    class FakeNetwork:
        def __init__(self):
            self.core_network = "core"

        def get_layers(self):
            return ["L1", "L2"], ["G1", "G2"], []

        def visualize_network(self, style=None, show=None, **kwargs):
            style_calls.append(style)
            return f"ax-{style}"

        def get_nodes(self):
            return [("node0", "L1")]

    monkeypatch.setattr(
        viz_module.random_generators, "random_multilayer_ER", lambda *args, **kwargs: FakeNetwork()
    )

    # Force community detection to fall back to the dummy path
    from py3plex.algorithms.community_detection import community_wrapper as cw

    monkeypatch.setattr(cw, "louvain_communities", lambda core: (_ for _ in ()).throw(RuntimeError()))

    viz_module.main()

    expected_files = [
        "multilayer.png",
        "hairball.png",
        "multiplex.png",
        "multilayer_small_multiples_shared.png",
        "multilayer_edge_projection_spring.png",
        "multilayer_supra_heatmap_inter.png",
        "multilayer_radial_with_inter.png",
        "multilayer_ego_node3_1hop.png",
        "multilayer_flow.png",
        "multilayer_sankey_diagram.png",
        "communities.png",
    ]
    assert saved_files == expected_files

    # Visualizations routed through the stubbed helper
    assert set(viz_calls) == {
        "small_multiples",
        "edge_colored_projection",
        "supra_adjacency_heatmap",
        "radial_layers",
        "ego_multilayer",
    }
    # Flow-style visualizations invoked on the network
    assert style_calls == ["flow", "sankey"]
    # draw_multilayer_default should still be exercised
    assert len(draw_calls) >= 3

    captured = capsys.readouterr()
    assert "COMPLETE: Generated 11/11 images" in captured.out
    assert f"Images saved to: {tmp_path}" in captured.out
