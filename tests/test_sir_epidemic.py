import importlib.util
import itertools
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "_downloads"
    / "b240507cb6a9f6e0b9fc5d743f73d786"
    / "sir_epidemic.py"
)
_MODULE_COUNTER = itertools.count()


def load_module():
    module_name = f"sir_epidemic_test_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sir_module():
    return load_module()


def test_create_simple_multilayer_network_ring_structure(sir_module):
    network = sir_module.create_simple_multilayer_network()

    assert len(list(network.get_nodes())) == 40
    assert len(list(network.get_edges())) == 50
    assert set(network.layers) == {"digital", "physical"}

    # Every physical node should connect to its ring neighbors.
    for node_id in range(20):
        right_neighbor = (node_id + 1) % 20
        left_neighbor = (node_id - 1) % 20

        assert network.core_network.has_edge((node_id, "physical"), (right_neighbor, "physical"))
        assert network.core_network.has_edge((node_id, "physical"), (left_neighbor, "physical"))


def test_run_sir_example_uses_sirdynamics_and_skips_plot_without_matplotlib(monkeypatch, capsys):
    module = load_module()
    created = {}

    class FakeResults:
        def __init__(self):
            self.prevalence = np.array([0.0, 0.2, 0.4])
            self.state_counts = {
                "S": np.array([40, 38, 36]),
                "I": np.array([0, 2, 2]),
                "R": np.array([0, 0, 2]),
            }

        def get_measure(self, name):
            if name == "prevalence":
                return self.prevalence
            return self.state_counts

        def __len__(self):
            return len(self.prevalence)

    class FakeSIRDynamics:
        def __init__(self, network, beta, gamma, initial_infected):
            created["instance"] = self
            self.network = network
            self.params = {"beta": beta, "gamma": gamma, "initial_infected": initial_infected}
            self.seed = None
            self.steps = None

        def set_seed(self, seed):
            self.seed = seed

        def run(self, steps):
            self.steps = steps
            return FakeResults()

    monkeypatch.setattr(module, "SIRDynamics", FakeSIRDynamics)
    monkeypatch.setattr(module, "plt", None)
    monkeypatch.setattr(module, "MATPLOTLIB_ERROR", ImportError("no matplotlib installed"))

    results = module.run_sir_example()
    output = capsys.readouterr().out

    assert isinstance(results, FakeResults)
    assert created["instance"].seed == module.DEFAULT_SEED
    assert created["instance"].steps == 100
    assert created["instance"].params == {"beta": 0.3, "gamma": 0.1, "initial_infected": 0.05}
    assert "SIR Epidemic Simulation Example" in output
    assert "Skipping plot" in output
    assert "Peak prevalence" in output


def test_plot_epidemic_curve_writes_file_with_fake_matplotlib(monkeypatch, tmp_path):
    module = load_module()

    class FakeAxis:
        def __init__(self):
            self.calls = []

        def plot(self, *args, **kwargs):
            self.calls.append(("plot", args, kwargs))

        def fill_between(self, *args, **kwargs):
            self.calls.append(("fill_between", args, kwargs))

        def set_xlabel(self, *args, **kwargs):
            self.calls.append(("set_xlabel", args, kwargs))

        def set_ylabel(self, *args, **kwargs):
            self.calls.append(("set_ylabel", args, kwargs))

        def set_title(self, *args, **kwargs):
            self.calls.append(("set_title", args, kwargs))

        def legend(self, *args, **kwargs):
            self.calls.append(("legend", args, kwargs))

        def grid(self, *args, **kwargs):
            self.calls.append(("grid", args, kwargs))

    class FakePlt:
        def __init__(self):
            self.saved = []

        def subplots(self, *args, **kwargs):
            return object(), (FakeAxis(), FakeAxis())

        def tight_layout(self):
            pass

        def savefig(self, path, dpi=None, bbox_inches=None):
            path = Path(path)
            path.write_text("figure")
            self.saved.append(path)

    fake_plt = FakePlt()
    output_dir = tmp_path / "outputs"
    monkeypatch.setattr(module, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(module, "plt", fake_plt)
    monkeypatch.setattr(module, "MATPLOTLIB_ERROR", None)

    prevalence = np.array([0.0, 0.5, 0.2])
    state_counts = {"S": [40, 20, 10], "I": [0, 10, 5], "R": [0, 10, 25]}

    module.plot_epidemic_curve(prevalence, state_counts)

    expected_path = output_dir / "sir_epidemic_example.png"
    assert output_dir.exists()
    assert expected_path.exists()
    assert fake_plt.saved == [expected_path]


def test_run_comparison_skips_when_matplotlib_missing(monkeypatch, capsys):
    module = load_module()
    monkeypatch.setattr(module, "plt", None)
    monkeypatch.setattr(module, "MATPLOTLIB_ERROR", ImportError("missing"))

    def _should_not_run(*args, **kwargs):
        raise AssertionError("SIRDynamics should not be constructed when matplotlib is missing")

    monkeypatch.setattr(module, "SIRDynamics", _should_not_run)

    module.run_comparison_with_different_parameters()
    output = capsys.readouterr().out

    assert "Skipping plot" in output


def test_run_comparison_with_fake_matplotlib_and_sirdynamics(monkeypatch, tmp_path):
    module = load_module()
    created = []

    class FakeResults:
        def __init__(self, prevalence):
            self._prevalence = prevalence

        def get_measure(self, name):
            if name != "prevalence":
                raise ValueError(name)
            return self._prevalence

    class FakeSIRDynamics:
        def __init__(self, network, beta, gamma, initial_infected):
            self.network = network
            self.params = {"beta": beta, "gamma": gamma, "initial_infected": initial_infected}
            self.seed = None
            self.steps = None
            created.append(self)

        def set_seed(self, seed):
            self.seed = seed

        def run(self, steps):
            self.steps = steps
            return FakeResults(prevalence=[self.params["beta"]] * 3)

    class FakePlt:
        def __init__(self):
            self.plots = []
            self.saved = None

        def figure(self, *args, **kwargs):
            return object()

        def plot(self, data, label=None, linewidth=None):
            self.plots.append((tuple(data), label, linewidth))

        def xlabel(self, *args, **kwargs):
            pass

        def ylabel(self, *args, **kwargs):
            pass

        def title(self, *args, **kwargs):
            pass

        def legend(self, *args, **kwargs):
            pass

        def grid(self, *args, **kwargs):
            pass

        def tight_layout(self):
            pass

        def savefig(self, path, dpi=None, bbox_inches=None):
            path = Path(path)
            path.write_text("comparison")
            self.saved = path

    fake_plt = FakePlt()
    output_dir = tmp_path / "out"
    monkeypatch.setattr(module, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(module, "plt", fake_plt)
    monkeypatch.setattr(module, "MATPLOTLIB_ERROR", None)
    monkeypatch.setattr(module, "SIRDynamics", FakeSIRDynamics)

    module.run_comparison_with_different_parameters()

    assert all(instance.seed == module.DEFAULT_SEED for instance in created)
    assert all(instance.steps == 50 for instance in created)
    assert fake_plt.saved == output_dir / "sir_parameter_comparison.png"
    assert len(fake_plt.plots) == 4
    labels_seen = {label for _, label, _ in fake_plt.plots}
    assert labels_seen == {"Low transmission", "High transmission", "Slow recovery", "Fast recovery"}
