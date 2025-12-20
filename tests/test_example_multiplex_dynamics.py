import importlib.util
import itertools
import sys
import types
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "advanced"
    / "example_multiplex_dynamics.py"
)
_MODULE_COUNTER = itertools.count()


def _install_dynamics_stubs(monkeypatch):
    dataset_requests = []
    load_network_calls = []
    split_calls = []
    remove_calls = []
    fill_tmp_calls = []
    draw_calls = []
    subplot_calls = []
    show_calls = []
    set_style_calls = []
    lineplot_calls = []
    basic_stats_calls = []

    class FakeRow:
        def __init__(self, layer_name):
            self.layer_name = layer_name

    class FakeActivity:
        def __init__(self, rows):
            self._rows = list(rows)
            self.shape = (len(self._rows), 0)

        def __getitem__(self, key):
            return FakeActivity(self._rows[key])

        def iterrows(self):
            for idx, row in enumerate(self._rows):
                yield idx, row

    class FakeNetwork:
        def __init__(self):
            self.real_layer_names = []
            self.activity = None
            self.tmp_layers = []

        def load_network(self, path, directed, input_type):
            load_network_calls.append(
                {
                    "path": path,
                    "directed": directed,
                    "input_type": input_type,
                }
            )
            return self

        def load_layer_name_mapping(self, path):
            self.real_layer_names = ["RT", "MT", "RE"]
            load_network_calls.append({"layer_map": path})
            return self

        def load_network_activity(self, path):
            rows = [FakeRow(1), FakeRow(1), FakeRow(2), FakeRow(3)]
            self.activity = FakeActivity(rows)
            load_network_calls.append({"activity_path": path})
            return self

        def basic_stats(self):
            basic_stats_calls.append({"rows": self.activity.shape[0]})
            print(f"basic stats for {self.activity.shape[0]} rows")

        def split_to_layers(self, style, compute_layouts, layout_parameters, multiplex):
            split_calls.append(
                {
                    "style": style,
                    "compute_layouts": compute_layouts,
                    "layout_parameters": layout_parameters,
                    "multiplex": multiplex,
                }
            )
            self.tmp_layers = [f"layer-{name}" for name in self.real_layer_names]
            return self

        def remove_layer_edges(self):
            remove_calls.append("removed")
            self.tmp_layers = []
            return self

        def fill_tmp_with_edges(self, time_slice):
            fill_tmp_calls.append(time_slice)
            self.tmp_layers = ["filled"]
            return self

    def get_multilayer_dataset_path(name):
        dataset_requests.append(name)
        return f"/fake/{name}"

    def multi_layer_network():
        return FakeNetwork()

    def draw_multilayer_default(*args, **kwargs):
        draw_calls.append({"args": args, "kwargs": kwargs})

    pyplot_mod = types.ModuleType("matplotlib.pyplot")

    def subplot(*args, **kwargs):
        subplot_calls.append(args)

    def title(text):
        subplot_calls.append(("title", text))

    def legend():
        subplot_calls.append(("legend",))

    def xlabel(text):
        subplot_calls.append(("xlabel", text))

    def ylabel(text):
        subplot_calls.append(("ylabel", text))

    def show():
        show_calls.append("show")

    pyplot_mod.subplot = subplot
    pyplot_mod.title = title
    pyplot_mod.legend = legend
    pyplot_mod.xlabel = xlabel
    pyplot_mod.ylabel = ylabel
    pyplot_mod.show = show

    seaborn_mod = types.ModuleType("seaborn")

    def set_style(style):
        set_style_calls.append(style)

    def lineplot(x, y, label=None, color=None):
        lineplot_calls.append({"x": x, "y": y, "label": label, "color": color})

    seaborn_mod.set_style = set_style
    seaborn_mod.lineplot = lineplot

    multinet_mod = types.SimpleNamespace(multi_layer_network=multi_layer_network)
    core_mod = types.ModuleType("py3plex.core")
    core_mod.multinet = multinet_mod

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_multilayer_dataset_path = get_multilayer_dataset_path

    visualization_multilayer_mod = types.ModuleType("py3plex.visualization.multilayer")
    visualization_multilayer_mod.draw_multilayer_default = draw_multilayer_default

    visualization_mod = types.ModuleType("py3plex.visualization")
    visualization_mod.multilayer = visualization_multilayer_mod

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.core = core_mod
    py3plex_mod.utils = utils_mod
    py3plex_mod.visualization = visualization_mod

    matplotlib_mod = types.ModuleType("matplotlib")
    matplotlib_mod.pyplot = pyplot_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", multinet_mod)
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)
    monkeypatch.setitem(sys.modules, "py3plex.visualization", visualization_mod)
    monkeypatch.setitem(sys.modules, "py3plex.visualization.multilayer", visualization_multilayer_mod)
    monkeypatch.setitem(sys.modules, "matplotlib", matplotlib_mod)
    monkeypatch.setitem(sys.modules, "matplotlib.pyplot", pyplot_mod)
    monkeypatch.setitem(sys.modules, "seaborn", seaborn_mod)

    return {
        "dataset_requests": dataset_requests,
        "load_network_calls": load_network_calls,
        "split_calls": split_calls,
        "remove_calls": remove_calls,
        "fill_tmp_calls": fill_tmp_calls,
        "draw_calls": draw_calls,
        "subplot_calls": subplot_calls,
        "show_calls": show_calls,
        "set_style_calls": set_style_calls,
        "lineplot_calls": lineplot_calls,
        "basic_stats_calls": basic_stats_calls,
    }


def _load_module_with_unique_name():
    module_name = f"example_multiplex_dynamics_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_multiplex_dynamics_example(monkeypatch, capsys):
    trackers = _install_dynamics_stubs(monkeypatch)
    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    out = capsys.readouterr().out

    # Dataset discovery and loading paths
    assert trackers["dataset_requests"] == [
        "MLKing/MLKing2013_multiplex.edges",
        "MLKing/MLKing2013_layers.txt",
        "MLKing/MLKing2013_activity.txt",
    ]
    assert trackers["load_network_calls"][0] == {
        "path": "/fake/MLKing/MLKing2013_multiplex.edges",
        "directed": True,
        "input_type": "multiplex_edges",
    }
    assert {"layer_map": "/fake/MLKing/MLKing2013_layers.txt"} in trackers["load_network_calls"]
    assert {"activity_path": "/fake/MLKing/MLKing2013_activity.txt"} in trackers["load_network_calls"]

    # Core workflow
    assert trackers["basic_stats_calls"] == [{"rows": 4}]
    assert "basic stats for 4 rows" in out

    assert trackers["split_calls"] == [
        {
            "style": "diagonal",
            "compute_layouts": "force",
            "layout_parameters": {"iterations": 1},
            "multiplex": True,
        }
    ]
    # Initial cleanup plus per-slice cleanup
    assert trackers["remove_calls"] == ["removed", "removed"]
    assert len(trackers["fill_tmp_calls"]) == 1

    # Visualization steps
    assert len(trackers["draw_calls"]) == 1
    draw_kwargs = trackers["draw_calls"][0]["kwargs"]
    assert draw_kwargs["labels"] == ["RT", "MT", "RE"]
    assert draw_kwargs["remove_isolated_nodes"] is True

    # Matplotlib and seaborn calls capture subplots and temporal lines
    assert trackers["subplot_calls"][0] == (4, 3, 1)
    assert ("title", "Time slice: 1") in trackers["subplot_calls"]
    assert (1, 1, 1) in trackers["subplot_calls"]
    assert ("xlabel", "Time slice") in trackers["subplot_calls"]
    assert ("ylabel", "Number of edges") in trackers["subplot_calls"]
    assert trackers["show_calls"] == ["show", "show"]

    assert trackers["set_style_calls"] == ["whitegrid"]
    assert {call["label"] for call in trackers["lineplot_calls"]} == {"RT", "MT", "RE"}
    # Confirm x-axis and y-axis data sizes reflect the counted edges per layer
    assert all(call["x"] == [0] for call in trackers["lineplot_calls"])
    edge_counts = {call["label"]: call["y"][0] for call in trackers["lineplot_calls"]}
    assert edge_counts == {"RT": 2, "MT": 1, "RE": 1}
