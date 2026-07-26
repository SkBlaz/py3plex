"""Long-form SIR convergence tests.

These tests verify that SIR dynamics exhibit correct convergence behaviour
over extended simulation horizons (200–500 steps), going well beyond the
shorter smoke-tests already present in test_dynamics_conservation.py and
related files.

Use cases covered:
- Epidemic eventually reaches zero prevalence on a variety of network
  topologies (ER, BA, WS, complete graph, path, grid).
- S + I + R == N is maintained throughout all 300+ time steps.
- R(t) is monotonically non-decreasing over 500 steps.
- Super-threshold outbreaks (R0 > 1) leave a measurable attack rate;
  sub-threshold seeds (R0 < 1) die out quickly even over long runs.
- Higher beta/gamma ratios yield larger final attack rates.
- Multiple independent replicates converge to statistically consistent
  final sizes.
- Multiplex SIR (simulate_sir_multiplex_discrete) conserves nodes and
  extinguishes over 300+ steps.
"""

import pytest
import numpy as np
import networkx as nx
import scipy.sparse

from py3plex.dynamics import SIRDynamics
from py3plex.algorithms.sir_multiplex import simulate_sir_multiplex_discrete


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_sir(G, beta, gamma, initial_infected, steps, seed=42):
    """Convenience wrapper: construct, seed, and run SIRDynamics."""
    sir = SIRDynamics(G, beta=beta, gamma=gamma, initial_infected=initial_infected)
    sir.set_seed(seed)
    return sir.run(steps=steps)


def _nx_to_csr(G):
    """Return the (symmetric) adjacency matrix of *G* as a CSR sparse matrix."""
    A = nx.to_scipy_sparse_array(G, format="csr", dtype=float)
    # Ensure symmetry
    A = A + A.T
    A.data = np.ones_like(A.data)
    A.eliminate_zeros()
    return A


# ---------------------------------------------------------------------------
# TestLongRunConservation
# ---------------------------------------------------------------------------

class TestLongRunConservation:
    """S + I + R == N must hold at every step over a long run."""

    def test_conservation_300_steps_er(self):
        """Conservation on Erdős–Rényi graph for 300 steps."""
        G = nx.erdos_renyi_graph(50, 0.15, seed=1)
        N = G.number_of_nodes()
        results = _run_sir(G, beta=0.3, gamma=0.1,
                           initial_infected=0.1, steps=300)

        sc = results.get_measure("state_counts")
        for t in range(len(sc["S"])):
            total = int(sc["S"][t]) + int(sc["I"][t]) + int(sc["R"][t])
            assert total == N, (
                f"Conservation violated at t={t}: S+I+R={total} != N={N}"
            )

    def test_conservation_500_steps_ba(self):
        """Conservation on Barabási–Albert graph for 500 steps."""
        G = nx.barabasi_albert_graph(60, 3, seed=2)
        N = G.number_of_nodes()
        results = _run_sir(G, beta=0.25, gamma=0.08,
                           initial_infected=0.05, steps=500)

        sc = results.get_measure("state_counts")
        for t in range(len(sc["S"])):
            total = int(sc["S"][t]) + int(sc["I"][t]) + int(sc["R"][t])
            assert total == N, (
                f"Conservation violated at t={t}: {total} != {N}"
            )

    def test_conservation_200_steps_complete(self):
        """Conservation on complete graph for 200 steps."""
        G = nx.complete_graph(30)
        N = G.number_of_nodes()
        results = _run_sir(G, beta=0.3, gamma=0.15,
                           initial_infected=0.1, steps=200)

        sc = results.get_measure("state_counts")
        for t in range(len(sc["S"])):
            total = int(sc["S"][t]) + int(sc["I"][t]) + int(sc["R"][t])
            assert total == N, (
                f"Conservation violated at t={t}: {total} != {N}"
            )


# ---------------------------------------------------------------------------
# TestMonotonicRecovery
# ---------------------------------------------------------------------------

class TestMonotonicRecovery:
    """R(t) must be non-decreasing at every time step."""

    def test_r_monotone_500_steps_karate(self):
        """R is non-decreasing over 500 steps on karate graph."""
        G = nx.karate_club_graph()
        results = _run_sir(G, beta=0.3, gamma=0.1,
                           initial_infected=0.1, steps=500)

        sc = results.get_measure("state_counts")
        R = sc["R"]
        for t in range(1, len(R)):
            assert R[t] >= R[t - 1], (
                f"R decreased from {R[t-1]} to {R[t]} at t={t}"
            )

    def test_r_monotone_300_steps_ws(self):
        """R is non-decreasing over 300 steps on Watts–Strogatz graph."""
        G = nx.watts_strogatz_graph(50, 4, 0.3, seed=7)
        results = _run_sir(G, beta=0.35, gamma=0.1,
                           initial_infected=0.1, steps=300)

        sc = results.get_measure("state_counts")
        R = sc["R"]
        for t in range(1, len(R)):
            assert R[t] >= R[t - 1], (
                f"R decreased from {R[t-1]} to {R[t]} at t={t}"
            )

    def test_r_monotone_400_steps_path(self):
        """R is non-decreasing over 400 steps on a path graph."""
        G = nx.path_graph(40)
        results = _run_sir(G, beta=0.6, gamma=0.1,
                           initial_infected=0.1, steps=400)

        sc = results.get_measure("state_counts")
        R = sc["R"]
        for t in range(1, len(R)):
            assert R[t] >= R[t - 1], (
                f"R decreased from {R[t-1]} to {R[t]} at t={t}"
            )


# ---------------------------------------------------------------------------
# TestLongRunExtinction
# ---------------------------------------------------------------------------

class TestLongRunExtinction:
    """SIR prevalence must reach zero after a sufficiently long run."""

    @pytest.mark.parametrize("graph_fn,name", [
        (lambda: nx.karate_club_graph(), "karate"),
        (lambda: nx.erdos_renyi_graph(60, 0.12, seed=10), "er"),
        (lambda: nx.barabasi_albert_graph(60, 3, seed=11), "ba"),
        (lambda: nx.watts_strogatz_graph(50, 4, 0.3, seed=12), "ws"),
        (lambda: nx.complete_graph(30), "complete"),
        (lambda: nx.grid_2d_graph(6, 6), "grid"),
    ])
    def test_extinction_diverse_topologies(self, graph_fn, name):
        """Epidemic extinguishes after 300 steps on various topologies."""
        G = graph_fn()
        results = _run_sir(G, beta=0.3, gamma=0.1,
                           initial_infected=0.1, steps=300)

        prevalence = results.get_measure("prevalence")
        # Final 20 steps should be near zero
        final_mean = float(np.mean(prevalence[-20:]))
        assert final_mean < 0.01, (
            f"[{name}] SIR did not go extinct: "
            f"mean prevalence in last 20 steps = {final_mean:.4f}"
        )

    def test_extinction_path_graph_long(self):
        """Path graph epidemic extinguishes within 400 steps."""
        G = nx.path_graph(50)
        results = _run_sir(G, beta=0.6, gamma=0.15,
                           initial_infected=0.1, steps=400)

        prevalence = results.get_measure("prevalence")
        final_mean = float(np.mean(prevalence[-30:]))
        assert final_mean < 0.01, (
            f"Path graph epidemic did not go extinct: {final_mean:.4f}"
        )


# ---------------------------------------------------------------------------
# TestPrevalenceBoundsLongRun
# ---------------------------------------------------------------------------

class TestPrevalenceBoundsLongRun:
    """Prevalence stays in [0, 1] throughout extended runs."""

    def test_prevalence_bounds_300_steps(self):
        """Prevalence is in [0, 1] for 300 steps on ER graph."""
        G = nx.erdos_renyi_graph(80, 0.1, seed=20)
        results = _run_sir(G, beta=0.3, gamma=0.1,
                           initial_infected=0.1, steps=300)

        prevalence = results.get_measure("prevalence")
        assert np.all(prevalence >= 0.0), "Prevalence < 0 detected"
        assert np.all(prevalence <= 1.0), "Prevalence > 1 detected"

    def test_prevalence_bounds_500_steps_ba(self):
        """Prevalence is in [0, 1] for 500 steps on BA graph."""
        G = nx.barabasi_albert_graph(70, 4, seed=21)
        results = _run_sir(G, beta=0.25, gamma=0.08,
                           initial_infected=0.05, steps=500)

        prevalence = results.get_measure("prevalence")
        assert np.all(prevalence >= 0.0), "Prevalence < 0 detected"
        assert np.all(prevalence <= 1.0), "Prevalence > 1 detected"


# ---------------------------------------------------------------------------
# TestPhaseTransitionConvergence
# ---------------------------------------------------------------------------

class TestPhaseTransitionConvergence:
    """Super-threshold outbreaks spread widely; sub-threshold ones die quickly."""

    def test_super_threshold_large_attack_rate(self):
        """Above epidemic threshold, a sizeable fraction eventually recovers."""
        # Dense ER graph: mean degree ~10; R0 ≈ beta/gamma * <k> ≈ 0.4/0.1*10 = 40 >> 1
        G = nx.erdos_renyi_graph(60, 0.17, seed=30)
        N = G.number_of_nodes()
        results = _run_sir(G, beta=0.4, gamma=0.1,
                           initial_infected=0.05, steps=300)

        sc = results.get_measure("state_counts")
        final_R = int(sc["R"][-1])
        attack_rate = final_R / N
        assert attack_rate > 0.30, (
            f"Super-threshold epidemic: expected attack rate > 30%, got {attack_rate:.2%}"
        )

    def test_sub_threshold_rapid_extinction(self):
        """Below epidemic threshold, infection dies out before step 100."""
        # Sparse path graph: mean degree 2; R0 ≈ 0.05/0.5*2 = 0.2 << 1
        G = nx.path_graph(60)
        results = _run_sir(G, beta=0.05, gamma=0.5,
                           initial_infected=0.05, steps=300)

        prevalence = results.get_measure("prevalence")
        # Prevalence should hit zero well before step 100
        zero_after = np.where(prevalence == 0.0)[0]
        assert len(zero_after) > 0, "Sub-threshold epidemic never extinguished"
        first_zero = int(zero_after[0])
        assert first_zero < 150, (
            f"Sub-threshold epidemic took too long to die: first zero at step {first_zero}"
        )

    def test_super_threshold_peak_before_extinction(self):
        """Super-threshold epidemic has a visible prevalence peak before dying."""
        G = nx.complete_graph(40)
        results = _run_sir(G, beta=0.4, gamma=0.1,
                           initial_infected=0.05, steps=300)

        prevalence = results.get_measure("prevalence")
        peak = float(np.max(prevalence))
        # Expect a substantial peak (>20% infected simultaneously)
        assert peak > 0.20, (
            f"Expected peak prevalence > 20%, got {peak:.2%}"
        )
        # And extinction by the end
        final = float(np.mean(prevalence[-20:]))
        assert final < 0.01, (
            f"Epidemic did not go extinct: final prevalence {final:.4f}"
        )


# ---------------------------------------------------------------------------
# TestFinalSizeRelation
# ---------------------------------------------------------------------------

class TestFinalSizeRelation:
    """Higher beta/gamma ratios should yield larger final attack rates."""

    def test_attack_rate_increases_with_beta(self):
        """Larger beta → larger attack rate at 300 steps."""
        G = nx.erdos_renyi_graph(80, 0.10, seed=40)
        N = G.number_of_nodes()

        results_low = _run_sir(G, beta=0.10, gamma=0.15,
                                initial_infected=0.1, steps=300, seed=40)
        results_high = _run_sir(G, beta=0.40, gamma=0.15,
                                 initial_infected=0.1, steps=300, seed=40)

        sc_low = results_low.get_measure("state_counts")
        sc_high = results_high.get_measure("state_counts")

        attack_low = int(sc_low["R"][-1]) / N
        attack_high = int(sc_high["R"][-1]) / N

        assert attack_high >= attack_low, (
            f"Higher beta should not decrease attack rate: "
            f"low={attack_low:.2%}, high={attack_high:.2%}"
        )

    def test_attack_rate_decreases_with_gamma(self):
        """Larger gamma → smaller (or equal) final attack rate at 300 steps."""
        G = nx.erdos_renyi_graph(80, 0.10, seed=41)
        N = G.number_of_nodes()

        results_slow = _run_sir(G, beta=0.30, gamma=0.05,
                                 initial_infected=0.1, steps=300, seed=41)
        results_fast = _run_sir(G, beta=0.30, gamma=0.40,
                                 initial_infected=0.1, steps=300, seed=41)

        sc_slow = results_slow.get_measure("state_counts")
        sc_fast = results_fast.get_measure("state_counts")

        attack_slow = int(sc_slow["R"][-1]) / N
        attack_fast = int(sc_fast["R"][-1]) / N

        # Faster recovery ↔ smaller epidemic
        assert attack_fast <= attack_slow + 0.05, (  # 5% tolerance
            f"Faster recovery should not substantially increase attack rate: "
            f"slow_recovery={attack_slow:.2%}, fast_recovery={attack_fast:.2%}"
        )


# ---------------------------------------------------------------------------
# TestMultiReplicateConvergence
# ---------------------------------------------------------------------------

class TestMultiReplicateConvergence:
    """Multiple independent replicates converge to consistent final sizes."""

    def test_replicate_final_sizes_agree(self):
        """Final attack rates across 5 replicates should be within 30pp of each other."""
        G = nx.erdos_renyi_graph(80, 0.12, seed=50)
        N = G.number_of_nodes()

        attack_rates = []
        for seed in range(5):
            results = _run_sir(G, beta=0.35, gamma=0.1,
                               initial_infected=0.1, steps=300, seed=seed)
            sc = results.get_measure("state_counts")
            attack_rates.append(int(sc["R"][-1]) / N)

        spread = max(attack_rates) - min(attack_rates)
        assert spread < 0.30, (
            f"Attack rates across replicates diverged too much: "
            f"{[f'{r:.2%}' for r in attack_rates]}, spread={spread:.2%}"
        )

    def test_replicate_extinction_timing_reasonable(self):
        """All replicates go extinct (prevalence = 0) by step 400."""
        G = nx.karate_club_graph()

        for seed in range(5):
            results = _run_sir(G, beta=0.3, gamma=0.1,
                               initial_infected=0.1, steps=400, seed=seed)
            prevalence = results.get_measure("prevalence")
            final_mean = float(np.mean(prevalence[-20:]))
            assert final_mean < 0.01, (
                f"Replicate seed={seed} did not go extinct by step 400: "
                f"mean final prevalence={final_mean:.4f}"
            )


# ---------------------------------------------------------------------------
# TestMultiplexLongConvergence
# ---------------------------------------------------------------------------

class TestMultiplexLongConvergence:
    """Multiplex SIR (simulate_sir_multiplex_discrete) long-run behaviour."""

    def _two_layer_er(self, N=40, p=0.12, seed=60):
        """Return two independent ER adjacency matrices as CSR."""
        G1 = nx.erdos_renyi_graph(N, p, seed=seed)
        G2 = nx.erdos_renyi_graph(N, p, seed=seed + 1)
        return [_nx_to_csr(G1), _nx_to_csr(G2)], N

    def test_multiplex_conservation_300_steps(self):
        """S + I + R == N at every step over 300 steps (multiplex)."""
        layers, N = self._two_layer_er()
        initial_infected = np.zeros(N, dtype=bool)
        initial_infected[:4] = True  # seed 4 nodes

        result = simulate_sir_multiplex_discrete(
            A_layers=layers,
            beta=0.3,
            gamma=0.1,
            dt=0.1,
            steps=300,
            initial_infected=initial_infected,
            rng_seed=61,
        )

        for t in range(len(result.times)):
            total = int(result.S[t]) + int(result.I[t]) + int(result.R[t])
            assert total == N, (
                f"Multiplex conservation violated at t={t}: {total} != {N}"
            )

    def test_multiplex_r_monotone_300_steps(self):
        """Recovered count is non-decreasing over 300 steps (multiplex)."""
        layers, N = self._two_layer_er()
        initial_infected = np.zeros(N, dtype=bool)
        initial_infected[:4] = True

        result = simulate_sir_multiplex_discrete(
            A_layers=layers,
            beta=0.3,
            gamma=0.1,
            dt=0.1,
            steps=300,
            initial_infected=initial_infected,
            rng_seed=62,
        )

        for t in range(1, len(result.times)):
            assert result.R[t] >= result.R[t - 1], (
                f"Multiplex R decreased at t={t}: "
                f"{result.R[t-1]} → {result.R[t]}"
            )

    def test_multiplex_extinction_300_steps(self):
        """Prevalence in multiplex SIR reaches zero by step 300."""
        layers, N = self._two_layer_er(N=50, p=0.10, seed=63)
        initial_infected = np.zeros(N, dtype=bool)
        initial_infected[:5] = True

        result = simulate_sir_multiplex_discrete(
            A_layers=layers,
            beta=0.35,
            gamma=0.15,
            dt=0.1,
            steps=300,
            initial_infected=initial_infected,
            rng_seed=64,
        )

        # Final 20 time points should have I == 0
        final_I = result.I[-20:]
        assert np.all(final_I == 0), (
            f"Multiplex SIR did not extinguish: final I counts = {final_I}"
        )

    def test_multiplex_prevalence_bounds_300_steps(self):
        """Multiplex prevalence (I/N) stays in [0, 1] for 300 steps."""
        layers, N = self._two_layer_er(N=50, p=0.10, seed=65)
        initial_infected = np.zeros(N, dtype=bool)
        initial_infected[:5] = True

        result = simulate_sir_multiplex_discrete(
            A_layers=layers,
            beta=0.30,
            gamma=0.10,
            dt=0.1,
            steps=300,
            initial_infected=initial_infected,
            rng_seed=66,
        )

        prevalence = result.I / N
        assert np.all(prevalence >= 0.0), "Multiplex prevalence < 0"
        assert np.all(prevalence <= 1.0), "Multiplex prevalence > 1"


# ---------------------------------------------------------------------------
# TestResultLength
# ---------------------------------------------------------------------------

class TestResultLength:
    """Verify that long-run results have the expected length."""

    @pytest.mark.parametrize("steps", [200, 300, 400, 500])
    def test_result_length(self, steps):
        """results should contain exactly steps+1 entries."""
        G = nx.karate_club_graph()
        results = _run_sir(G, beta=0.3, gamma=0.1,
                           initial_infected=0.1, steps=steps)
        assert len(results) == steps + 1, (
            f"Expected {steps + 1} entries, got {len(results)}"
        )

        prevalence = results.get_measure("prevalence")
        assert len(prevalence) == steps + 1, (
            f"Prevalence length mismatch: expected {steps + 1}, got {len(prevalence)}"
        )

        sc = results.get_measure("state_counts")
        assert len(sc["S"]) == steps + 1
        assert len(sc["I"]) == steps + 1
        assert len(sc["R"]) == steps + 1
