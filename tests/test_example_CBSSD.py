import importlib.util
import itertools
import sys
import types
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "examples" / "advanced" / "example_CBSSD.py"
_MODULE_COUNTER = itertools.count()


def load_example_with_fakes(monkeypatch):
    """Load the CBSSD example with lightweight fakes to observe side effects."""
    record = []
    dataset_calls = []
    data_calls = []
    context = {}
    fake_partition = {"P12345": 1, "Q8ABC1": 2}

    class FakeNetwork:
        def __init__(self):
            self.monitor_calls = []

        def load_network(self, path, directed=False, input_type=None):
            record.append(("load_network", path, directed, input_type))
            return self

        def basic_stats(self):
            record.append(("basic_stats",))

        def monitor(self, message):
            self.monitor_calls.append(message)
            record.append(("monitor", message))

    class FakeRDF:
        def __init__(self):
            self.serialized = []

        def serialize(self, destination, format="n3"):
            self.serialized.append((destination, format))
            record.append(("serialize", destination, format))

    fake_network = FakeNetwork()

    def fake_multi_layer_network():
        record.append(("multi_layer_network",))
        return fake_network

    def get_dataset_path(name):
        path = f"/datasets/{name}"
        dataset_calls.append((name, path))
        record.append(("get_dataset_path", name, path))
        return path

    def get_data_path(name):
        path = f"/data/{name}"
        data_calls.append((name, path))
        record.append(("get_data_path", name, path))
        return path

    def get_background_knowledge_dir():
        record.append(("get_background_knowledge_dir",))
        return "/bkdir"

    def louvain_communities(network):
        record.append(("louvain_communities", network))
        return fake_partition

    def convert_mapping_to_rdf(partition, annotation_mapping_file, layer_type):
        record.append(("convert_mapping_to_rdf", partition, annotation_mapping_file, layer_type))
        rdf = FakeRDF()
        context["rdf"] = rdf
        return rdf

    def obo2n3(obo_file, output_path, gaf_path):
        record.append(("obo2n3", obo_file, output_path, gaf_path))

    def run(params):
        context["run_params"] = params
        record.append(("run", params))

    # Build fake module tree matching imports used in the example.
    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []

    core_mod = types.ModuleType("py3plex.core")
    core_mod.__path__ = []
    core_mod.multinet = types.SimpleNamespace(multi_layer_network=fake_multi_layer_network)

    algorithms_mod = types.ModuleType("py3plex.algorithms")
    algorithms_mod.__path__ = []

    community_wrapper_mod = types.ModuleType("py3plex.algorithms.community_detection.community_wrapper")
    community_wrapper_mod.louvain_communities = louvain_communities

    community_detection_mod = types.ModuleType("py3plex.algorithms.community_detection")
    community_detection_mod.__path__ = []
    community_detection_mod.community_wrapper = community_wrapper_mod

    hedwig_mod = types.ModuleType("py3plex.algorithms.hedwig")
    hedwig_mod.convert_mapping_to_rdf = convert_mapping_to_rdf
    hedwig_mod.obo2n3 = obo2n3
    hedwig_mod.run = run

    utils_mod = types.ModuleType("py3plex.utils")
    utils_mod.get_dataset_path = get_dataset_path
    utils_mod.get_data_path = get_data_path
    utils_mod.get_background_knowledge_dir = get_background_knowledge_dir

    algorithms_mod.hedwig = hedwig_mod
    algorithms_mod.community_detection = community_detection_mod
    py3plex_mod.core = core_mod
    py3plex_mod.algorithms = algorithms_mod
    py3plex_mod.utils = utils_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core", core_mod)
    monkeypatch.setitem(sys.modules, "py3plex.core.multinet", core_mod.multinet)
    monkeypatch.setitem(sys.modules, "py3plex.algorithms", algorithms_mod)
    monkeypatch.setitem(sys.modules, "py3plex.algorithms.hedwig", hedwig_mod)
    monkeypatch.setitem(sys.modules, "py3plex.algorithms.community_detection", community_detection_mod)
    monkeypatch.setitem(
        sys.modules, "py3plex.algorithms.community_detection.community_wrapper", community_wrapper_mod
    )
    monkeypatch.setitem(sys.modules, "py3plex.utils", utils_mod)

    module_name = f"example_CBSSD_test_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return {
        "module": module,
        "record": record,
        "dataset_calls": dataset_calls,
        "data_calls": data_calls,
        "context": context,
        "fake_network": fake_network,
        "fake_partition": fake_partition,
    }


def test_cbssd_example_triggers_pipeline(monkeypatch, capsys):
    result = load_example_with_fakes(monkeypatch)
    record = result["record"]
    dataset_calls = result["dataset_calls"]
    data_calls = result["data_calls"]
    fake_network = result["fake_network"]
    fake_partition = result["fake_partition"]
    out = capsys.readouterr().out

    # order-sensitive calls around loading and statistics
    event_names = [entry[0] for entry in record]
    assert event_names[:3] == ["multi_layer_network", "get_dataset_path", "load_network"]
    assert event_names[3:5] == ["basic_stats", "louvain_communities"]

    # dataset lookups (paths are derived and reused across the script)
    assert [call[0] for call in dataset_calls] == [
        "intact02.gpickle",
        "example_partition_inputs.n3",
        "goa_human.gaf.gz",
        "go.obo.gz",
        "goa_human.gaf.gz",
        "example_partition_inputs.n3",
    ]
    assert dataset_calls[1][1] == "/datasets/example_partition_inputs.n3"

    # louvain uses the loaded network and the partition is printed
    louvain_call = next(entry for entry in record if entry[0] == "louvain_communities")
    assert louvain_call[1] is fake_network
    assert str(fake_partition) in out

    # mapping conversion and serialization target the computed dataset name
    convert_call = next(entry for entry in record if entry[0] == "convert_mapping_to_rdf")
    assert convert_call[1] == fake_partition
    assert convert_call[2] == "/datasets/goa_human.gaf.gz"
    rdf = result["context"]["rdf"]
    assert rdf.serialized == [("/datasets/example_partition_inputs.n3", "n3")]

    # background knowledge and OBO conversion use derived paths
    assert data_calls == [("background_knowledge/bk.n3", "/data/background_knowledge/bk.n3")]
    obo_call = next(entry for entry in record if entry[0] == "obo2n3")
    assert obo_call[1:] == (
        "/datasets/go.obo.gz",
        "/data/background_knowledge/bk.n3",
        "/datasets/goa_human.gaf.gz",
    )

    # rule learning parameters are propagated intact
    run_params = result["context"]["run_params"]
    assert run_params["bk_dir"] == "/bkdir"
    assert run_params["data"] == "/datasets/example_partition_inputs.n3"
    assert run_params["format"] == "n3"
    assert run_params["beam"] == 300
    assert run_params["support"] == 0.01
    assert run_params["negations"] is True
    assert run_params["leaves"] is True

    # monitor is invoked before launching hedwig.run
    monitor_index = event_names.index("monitor")
    run_index = event_names.index("run")
    assert monitor_index < run_index
    assert fake_network.monitor_calls == ["Starting rule learning"]
