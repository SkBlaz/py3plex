"""Correctness-focused tests for dynamics algorithms and contracts."""

import numpy as np
import networkx as nx
import pytest

from py3plex.dynamics.core import ContinuousTimeProcess
from py3plex.dynamics.compartmental import (
    SISContinuousTime,
    CompartmentalDynamics,
)
from py3plex.dynamics.processes import sir_update_factory
from py3plex.dynamics._utils import count_infected_neighbors

try:
    from hypothesis import given, strategies as st
except ImportError:  # pragma: no cover - optional dependency
    given = None


class _NoEventProcess(ContinuousTimeProcess):
    """A ContinuousTimeProcess that never has any enabled events."""

    def initialize_state(self, seed=None):
        return {"node": 0}

    def compute_propensities(self, state):
        return {}

    def apply_event(self, state, event_id):
        raise AssertionError("apply_event should not be called")


class _TwoEventProcess(ContinuousTimeProcess):
    """A process with two events at different rates for Gillespie checks."""

    def initialize_state(self, seed=None):
        return 0

    def compute_propensities(self, state):
        # Order is deterministic: "fast" then "slow"
        return {"fast": 2.0, "slow": 1.0}

    def apply_event(self, state, event_id):
        return state + (0 if event_id == "fast" else 10)


def test_gillespie_no_events_returns_infinite_dt_and_static_time():
    """When no propensities exist, step should terminate with inf dt."""
    process = _NoEventProcess(graph=None, seed=7)
    state = process.initialize_state()

    new_state, dt, event_id = process.step(state)

    assert dt == float("inf")
    assert event_id is None
    assert process.current_time == 0.0
    assert new_state == state  # state unchanged because no event occurred


def test_gillespie_step_uses_exponential_clock_and_rate_weights():
    """Verify dt sampling and event choice align with numpy RNG draws."""
    seed = 3
    process = _TwoEventProcess(graph=None, seed=seed)
    state = process.initialize_state()

    reference_rng = np.random.default_rng(seed)
    expected_dt = reference_rng.exponential(1.0 / 3.0)  # total rate = 2 + 1
    expected_event_idx = reference_rng.choice(2, p=np.array([2.0, 1.0]) / 3.0)
    expected_event = ["fast", "slow"][expected_event_idx]

    new_state, dt, event_id = process.step(state)

    assert dt == pytest.approx(expected_dt)
    assert process.current_time == pytest.approx(expected_dt)
    assert event_id == expected_event
    expected_state = state + (0 if expected_event == "fast" else 10)
    assert new_state == expected_state


def test_sis_propensities_match_neighbor_counts():
    """SISContinuousTime infection propensities scale with infected neighbors."""
    G = nx.path_graph(3)
    model = SISContinuousTime(G, seed=1, beta=0.4, mu=0.2)
    state = {0: "S", 1: "I", 2: "S"}

    propensities = model.compute_propensities(state)

    assert propensities[("recover", 1)] == pytest.approx(0.2)
    assert propensities[("infect", 0)] == pytest.approx(0.4)
    assert propensities[("infect", 2)] == pytest.approx(0.4)
    assert ("infect", 1) not in propensities


def test_compartmental_initialize_state_respects_fractions():
    """Initial fractions should assign counts per compartment without loss."""
    G = nx.path_graph(10)

    def _stay(compartment):
        def fn(node, state, neighbor_counts, rng, params):
            return compartment

        return fn

    compartments = ["S", "I", "R"]
    transition_rules = {c: _stay(c) for c in compartments}
    dynamics = CompartmentalDynamics(
        G,
        seed=5,
        compartments=compartments,
        transition_rules=transition_rules,
        initial_fractions={"I": 0.3, "R": 0.2},
    )

    state = dynamics.initialize_state()
    counts = dynamics.compartment_counts(state)

    assert sum(counts.values()) == G.number_of_nodes()
    assert counts["I"] == 3  # int(10 * 0.3)
    assert counts["R"] == 2  # int(10 * 0.2)
    assert counts["S"] == 5  # remaining nodes fall back to default compartment


def test_sir_update_factory_zero_beta_full_recovery():
    """With beta=0 and gamma=1, infected recover and no new infections occur."""
    adj = np.array(
        [
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0],
        ],
        dtype=float,
    )
    state = np.array([1, 0, 1], dtype=int)  # I, S, I
    rng = np.random.default_rng(0)

    update_step = sir_update_factory({"beta": 0.0, "gamma": 1.0}, coupling={})
    new_state = update_step(adj, state, rng)

    assert np.array_equal(new_state, np.array([2, 0, 2]))  # both infected recover


if given:

    @given(
        st.lists(
            st.sampled_from(["S", "I"]),
            min_size=3,
            max_size=3,
        ).map(lambda vals: dict(zip(range(3), vals)))
    )
    def test_sis_propensity_property_matches_neighbor_counts(state):
        """Infection rate equals beta * infected_neighbors for susceptible nodes."""
        G = nx.path_graph(3)
        beta = 0.6
        mu = 0.25
        model = SISContinuousTime(G, beta=beta, mu=mu)

        propensities = model.compute_propensities(state)

        for node, status in state.items():
            if status == "I":
                assert propensities[("recover", node)] == pytest.approx(mu)
            else:
                infected_neighbors = count_infected_neighbors(
                    G, node, state, infected_value="I"
                )
                infection_key = ("infect", node)
                if infected_neighbors == 0:
                    assert infection_key not in propensities
                else:
                    assert propensities[infection_key] == pytest.approx(
                        beta * infected_neighbors
                    )

else:

    def test_sis_propensity_property_matches_neighbor_counts():
        pytest.skip("hypothesis not installed")
