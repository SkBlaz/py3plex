import importlib.util
import itertools
import sys
import types
from pathlib import Path

import networkx as nx


MODULE_PATH = Path(__file__).resolve().parents[1] / "examples" / "advanced" / "example_dynamics_core.py"
_MODULE_COUNTER = itertools.count()


def _install_dynamics_fakes(monkeypatch, record, *, hitting_mean=1.0):
    """Install a lightweight py3plex.dynamics stub used by the example."""

    class FakeRandomWalkDynamics:
        def __init__(self, graph, seed=None, start_node=None, lazy_probability=None):
            self.graph = graph
            self.seed = seed
            self.start_node = 0 if start_node is None else start_node
            self.lazy_probability = lazy_probability
            record.append(("RandomWalk_init", seed, start_node, lazy_probability))

        def run(self, steps):
            record.append(("RandomWalk_run", steps))
            return [self.start_node] + [self.start_node + 1 for _ in range(steps)]

        def visit_counts(self, trajectory):
            record.append(("RandomWalk_visit_counts", len(trajectory)))
            counts = {}
            for node in trajectory:
                counts[node] = counts.get(node, 0) + 1
            return counts

    class FakeMultiRandomWalkDynamics:
        def __init__(self, graph, seed=None, n_walkers=None, absorbing_nodes=None, init_strategy=None):
            self.graph = graph
            self.seed = seed
            self.n_walkers = n_walkers
            self.absorbing_nodes = set(absorbing_nodes or [])
            self.init_strategy = init_strategy
            record.append(("Multi_init", n_walkers, tuple(sorted(self.absorbing_nodes))))

        def run(self, steps):
            record.append(("Multi_run", steps))
            trajectory = []
            for t in range(steps + 1):
                state = []
                for walker in range(self.n_walkers):
                    state.append(None if t >= walker + 1 else walker)
                trajectory.append(tuple(state))
            return trajectory

        def hitting_time_statistics(self, trajectory):
            record.append(("Multi_stats", len(trajectory)))
            absorbed_count = sum(1 for pos in trajectory[-1] if pos is None)
            mean = hitting_mean
            std = 0.5 if hitting_mean is not None else None
            return {"hitting_times": [1] * self.n_walkers, "mean": mean, "std": std, "absorbed_count": absorbed_count}

    class FakeSISDynamics:
        def __init__(self, graph, seed=None, beta=None, mu=None, initial_infected=None, backend="python"):
            self.graph = graph
            self.seed = seed
            self.backend = backend
            record.append(("SIS_init", backend))

        def run_with_prevalence(self, steps):
            record.append(("SIS_run_with_prevalence", steps))
            return [0.1 + 0.002 * i for i in range(steps + 1)]

    class FakeAdaptiveSISDynamics:
        def __init__(self, graph, seed=None, beta=None, mu=None, w=None, initial_infected=None):
            self.graph = graph
            self.seed = seed
            record.append(("Adaptive_init", beta, mu, w))

        def run(self, steps):
            record.append(("Adaptive_run", steps))
            nodes = list(self.graph.nodes())
            states = []
            for _ in range(steps + 1):
                state = {node: ("I" if idx < 2 else "S") for idx, node in enumerate(nodes)}
                states.append(state)
            return states

        def edge_type_counts(self, state):
            record.append(("Adaptive_edge_counts",))
            counts = {"S-S": 0, "S-I": 0, "I-I": 0}
            for u, v in self.graph.edges():
                pair = (state.get(u, "S"), state.get(v, "S"))
                if pair == ("I", "I"):
                    counts["I-I"] += 1
                elif pair == ("S", "S"):
                    counts["S-S"] += 1
                else:
                    counts["S-I"] += 1
            return counts

        def prevalence(self, state):
            record.append(("Adaptive_prevalence",))
            total = len(state)
            infected = sum(1 for v in state.values() if v == "I")
            return infected / total if total else 0.0

    class FakeSIRDynamics:
        def __init__(self, graph, seed=None, beta=None, gamma=None, initial_infected=None):
            self.graph = graph
            self.seed = seed
            record.append(("SIR_init", beta, gamma))

        def run(self, steps):
            record.append(("SIR_run", steps))
            nodes = list(self.graph.nodes())
            states = []
            for _ in range(steps + 1):
                state = {}
                for idx, node in enumerate(nodes):
                    if idx % 3 == 0:
                        state[node] = "S"
                    elif idx % 3 == 1:
                        state[node] = "I"
                    else:
                        state[node] = "R"
                states.append(state)
            return states

        def compartment_counts(self, state):
            record.append(("SIR_counts",))
            counts = {"S": 0, "I": 0, "R": 0}
            for value in state.values():
                counts[value] += 1
            return counts

    class FakeSEIRDynamics(FakeSIRDynamics):
        pass

    class FakeSISContinuousTime:
        def __init__(self, graph, seed=None, beta=None, mu=None, initial_infected=None):
            self.graph = graph
            self.seed = seed
            record.append(("SISCT_init", beta, mu))

        def run(self, t_max):
            record.append(("SISCT_run", t_max))
            times = [0.0, t_max / 3, 2 * t_max / 3, t_max]
            nodes = list(self.graph.nodes())
            trajectory = []
            for offset in range(len(times)):
                trajectory.append({node: ("I" if (idx + offset) % 2 == 0 else "S") for idx, node in enumerate(nodes)})
            return trajectory, times

        def prevalence(self, state):
            record.append(("SISCT_prevalence",))
            total = len(state)
            infected = sum(1 for v in state.values() if v == "I")
            return infected / total if total else 0.0

    class FakeTemporalGraph:
        def __init__(self, snapshots=None, get_graph_fn=None):
            self.snapshots = snapshots
            self.get_graph_fn = get_graph_fn
            record.append(("TemporalGraph_init", len(snapshots) if snapshots is not None else None))

        def __len__(self):
            return len(self.snapshots) if self.snapshots is not None else 0

        def get_graph(self, t):
            return self.snapshots[t] if self.snapshots is not None else self.get_graph_fn(t)

    class FakeTemporalRandomWalk:
        def __init__(self, temporal_graph, seed=None, start_node=None):
            self.temporal_graph = temporal_graph
            self.seed = seed
            self.start_node = 0 if start_node is None else start_node
            record.append(("TemporalWalk_init", seed, start_node))

        def run(self, steps):
            record.append(("TemporalWalk_run", steps))
            return [self.start_node + i for i in range(steps + 1)]

    class FakeConfigDynamics:
        def __init__(self, graph, config):
            self.graph = graph
            self.config = config
            self.seed = None

        def set_seed(self, seed):
            record.append(("Config_set_seed", seed))
            self.seed = seed

        def run(self, steps):
            record.append(("Config_run", steps))
            nodes = list(self.graph.nodes())
            states = []
            for step in range(steps + 1):
                infected_target = 2 if step == 0 else 5
                state = {
                    node: ("I" if idx < min(infected_target, len(nodes)) else "S")
                    for idx, node in enumerate(nodes)
                }
                states.append(state)
            return states

    def build_dynamics_from_config(graph, config):
        record.append(("build_dynamics_from_config", tuple(config.get("compartments", []))))
        return FakeConfigDynamics(graph, config)

    dynamics_mod = types.ModuleType("py3plex.dynamics")
    dynamics_mod.RandomWalkDynamics = FakeRandomWalkDynamics
    dynamics_mod.MultiRandomWalkDynamics = FakeMultiRandomWalkDynamics
    dynamics_mod.SISDynamics = FakeSISDynamics
    dynamics_mod.AdaptiveSISDynamics = FakeAdaptiveSISDynamics
    dynamics_mod.SIRDynamics = FakeSIRDynamics
    dynamics_mod.SEIRDynamics = FakeSEIRDynamics
    dynamics_mod.SISContinuousTime = FakeSISContinuousTime
    dynamics_mod.TemporalGraph = FakeTemporalGraph
    dynamics_mod.TemporalRandomWalk = FakeTemporalRandomWalk
    dynamics_mod.build_dynamics_from_config = build_dynamics_from_config

    py3plex_mod = types.ModuleType("py3plex")
    py3plex_mod.__path__ = []
    py3plex_mod.dynamics = dynamics_mod

    monkeypatch.setitem(sys.modules, "py3plex", py3plex_mod)
    monkeypatch.setitem(sys.modules, "py3plex.dynamics", dynamics_mod)


def _load_module_with_unique_name():
    module_name = f"example_dynamics_core_{next(_MODULE_COUNTER)}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    return spec, module


def test_main_runs_all_examples_with_stubbed_dynamics(monkeypatch, capsys):
    record = []
    _install_dynamics_fakes(monkeypatch, record, hitting_mean=1.5)

    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    module.main()

    out = capsys.readouterr().out

    # Each example uses its respective dynamics class with the expected parameters
    assert ("RandomWalk_init", 42, 0, 0.1) in record
    assert ("RandomWalk_run", 100) in record
    assert ("Multi_init", 5, (0, 33)) in record
    assert ("Multi_run", 200) in record
    assert ("Multi_stats", 201) in record
    assert ("SIS_run_with_prevalence", 100) in record
    assert ("Adaptive_run", 50) in record
    assert ("SIR_run", 100) in record
    assert ("SISCT_run", 10.0) in record
    assert ("TemporalWalk_run", 9) in record
    assert ("Config_run", 50) in record
    assert ("build_dynamics_from_config", ("S", "I")) in record

    # Output contains key metrics derived from the fakes
    assert "Example 1: Random Walk on Karate Club Network" in out
    assert "Total steps: 100" in out
    assert "Example 2: Multiple Walkers with Absorbing States" in out
    assert "Walkers absorbed: 5/5" in out
    assert "Mean hitting time" in out  # Branch when mean is provided
    assert "Example 6: Continuous-Time SIS (Gillespie)" in out
    assert "Number of events: 4" in out
    assert "Example 8: Config-Based Dynamics" in out
    assert "Initial infected: 2/34" in out
    assert "Final infected: 5/34" in out


def test_multi_walker_example_skips_mean_when_not_available(monkeypatch, capsys):
    record = []
    _install_dynamics_fakes(monkeypatch, record, hitting_mean=None)

    spec, module = _load_module_with_unique_name()
    spec.loader.exec_module(module)

    module.example_multi_walker()

    out = capsys.readouterr().out

    assert ("Multi_run", 200) in record
    assert ("Multi_stats", 201) in record
    # Without a mean value, the branch that reports statistics is skipped
    assert "Mean hitting time" not in out
    assert "Std hitting time" not in out
