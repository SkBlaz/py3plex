"""
MDL Metric Benchmark on Synthetic Multilayer LFR Graphs.

Unit tests (see ``tests/test_mdl_score.py``) check that ``mdl_score`` behaves
correctly on hand-built toy graphs, but they cannot show that the metric is
actually a *useful* community-quality signal. This module answers that with
an empirical benchmark against known ground truth:

- Generate multilayer LFR graphs across a range of mixing parameters ``mu``
  (easy -> hard).
- On each graph, score three partitions -- the ground truth, a corrupted/
  degenerate partition, and the output of a real algorithm (Louvain) -- with
  ``mdl_score`` and the baseline metrics ``multilayer_modularity`` and
  ``replica_consistency``.
- Check whether ``mdl_score`` ranks ground truth best as ``mu`` grows, how
  its ranking agrees (or informatively disagrees) with modularity's, and how
  its compute cost compares to the baselines' on the same graphs.

Algorithm choice: this uses ``community_louvain.best_partition`` (run on the
flat supra-graph, i.e. treating each ``(node, layer)`` pair as an opaque
node id) rather than this package's own ``leiden_multilayer``/
``louvain_multilayer``. Both of the latter are single-level greedy local
search with no hierarchical aggregation/coarsening phase, so they reliably
get stuck in a poor local optimum on anything past toy-sized graphs
(confirmed by hand-stepping the local-move loop -- e.g. on a 2-layer,
2-clique graph with default interlayer coupling they converge to a
half-merged partition with modularity 0.03 instead of the true ~0.5).
``community_louvain.best_partition`` implements the real multi-level
Louvain (with ``generate_dendrogram``/``induced_graph`` aggregation) and
was verified to recover ground-truth-comparable modularity on the LFR
graphs here; that upstream local-optimum issue is a separate, unrelated bug
worth fixing on its own.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple
import time
import warnings

import numpy as np
from scipy.stats import spearmanr

from py3plex.algorithms.community_detection.community_louvain import (
    best_partition,
)
from py3plex.algorithms.community_detection.multilayer_benchmark import (
    generate_multilayer_lfr,
)
from py3plex.algorithms.community_detection.multilayer_modularity import (
    multilayer_modularity,
)
from py3plex.algorithms.community_detection.multilayer_quality_metrics import (
    mdl_score,
    replica_consistency,
)

NodeLayer = Tuple[Any, Any]
Partition = Dict[NodeLayer, int]


@dataclass
class PartitionScore:
    """Scores for one (mu, seed, partition_type) combination."""

    mu: float
    seed: int
    n_nodes: int
    n_edges: int
    partition_type: str  # "ground_truth" | "corrupted" | "louvain"
    mdl: float
    modularity: float
    replica_consistency: float
    mdl_time_s: float
    modularity_time_s: float
    rc_time_s: float


def _flatten_ground_truth(communities: Dict[NodeLayer, set]) -> Partition:
    """Collapse each node-layer's community *set* to one representative label.

    ``generate_multilayer_lfr`` returns overlapping-community sets; with the
    default ``overlapping_nodes=0`` every set is a singleton, so taking the
    min element is a lossless, deterministic flattening to the plain
    ``(node, layer) -> community_id`` format ``mdl_score``/``multilayer_modularity``/
    ``replica_consistency`` all expect.
    """
    return {node_layer: min(coms) for node_layer, coms in communities.items()}


def _corrupt_partition(
    partition: Partition, corruption_rate: float, seed: int
) -> Partition:
    """Randomly reassign a fraction of node-layer pairs to a different label.

    A stand-in for a "degenerate" partition: same node coverage and label
    vocabulary as the input, but a chunk of nodes scattered into the wrong
    community.
    """
    rng = np.random.RandomState(seed)
    labels = sorted(set(partition.values()))
    keys = list(partition.keys())
    n_corrupt = int(len(keys) * corruption_rate)
    corrupt_idx = rng.choice(len(keys), size=n_corrupt, replace=False)

    corrupted = dict(partition)
    for idx in corrupt_idx:
        key = keys[idx]
        current = corrupted[key]
        choices = [label for label in labels if label != current] or labels
        corrupted[key] = rng.choice(choices)
    return corrupted


def _louvain_partition(network: Any, resolution: float) -> Partition:
    """Run real multi-level Louvain on the flat supra-graph.

    ``network.core_network`` already has ``(node, layer)`` tuples as node
    ids, so ``best_partition`` naturally treats each node-layer pair as its
    own unit -- this is what makes it usable as a multilayer "real
    algorithm" partition without any extra flattening/expansion step.
    """
    return best_partition(network.core_network, resolution=resolution)


def _score_partition(
    partition: Partition, network: Any
) -> Tuple[float, float, float, float, float, float]:
    """Return (mdl, modularity, replica_consistency, mdl_s, modularity_s, rc_s)."""
    t0 = time.perf_counter()
    with warnings.catch_warnings():
        # mdl_score warns on partial/parallel/weighted inputs; none of that
        # is a bug here, so it would just be report noise.
        warnings.simplefilter("ignore")
        mdl = mdl_score(partition, network)
    t1 = time.perf_counter()

    mod = multilayer_modularity(network, partition)
    t2 = time.perf_counter()

    rc = replica_consistency(partition, network)
    t3 = time.perf_counter()

    return mdl, mod, rc, (t1 - t0), (t2 - t1), (t3 - t2)


def run_benchmark(
    mu_values: Sequence[float] = (0.05, 0.1, 0.2, 0.3, 0.4, 0.5),
    ns: Sequence[int] = (200,),
    layers: Sequence[str] = ("L1", "L2", "L3"),
    avg_degree: float = 10.0,
    min_community: int = 20,
    seeds: Sequence[int] = (0, 1, 2),
    corruption_rate: float = 0.3,
    resolution: float = 1.0,
) -> List[PartitionScore]:
    """Score ground-truth/corrupted/Louvain partitions across an LFR ``mu`` sweep.

    Args:
        mu_values: LFR mixing parameters to sweep (0 = perfect communities,
            1 = random -- i.e. easy to hard).
        ns: Graph sizes (node counts) to sweep. Pass more than one value to
            get a scaling curve for metric compute cost.
        layers: Layer names for the generated multiplex graph.
        avg_degree: Average per-layer degree passed to ``generate_multilayer_lfr``.
        min_community: Minimum community size passed to ``generate_multilayer_lfr``.
        seeds: Random seeds; each is used both for graph generation and for
            the corrupted-partition randomness, so results are reproducible
            per (mu, n, seed).
        corruption_rate: Fraction of node-layer pairs reassigned to a wrong
            community in the corrupted partition.
        resolution: Passed to ``community_louvain.best_partition``.

    Returns:
        One ``PartitionScore`` per (mu, n, seed, partition_type) combination.
    """
    records: List[PartitionScore] = []

    for n in ns:
        for mu in mu_values:
            for seed in seeds:
                network, gt_sets = generate_multilayer_lfr(
                    n=n,
                    layers=list(layers),
                    mu=mu,
                    avg_degree=avg_degree,
                    min_community=min_community,
                    seed=seed,
                )
                ground_truth = _flatten_ground_truth(gt_sets)
                n_nodes = network.core_network.number_of_nodes()
                n_edges = network.core_network.number_of_edges()

                partitions: Dict[str, Partition] = {
                    "ground_truth": ground_truth,
                    "corrupted": _corrupt_partition(
                        ground_truth, corruption_rate, seed
                    ),
                    "louvain": _louvain_partition(network, resolution),
                }

                for partition_type, partition in partitions.items():
                    mdl, mod, rc, t_mdl, t_mod, t_rc = _score_partition(
                        partition, network
                    )
                    records.append(
                        PartitionScore(
                            mu=mu,
                            seed=seed,
                            n_nodes=n_nodes,
                            n_edges=n_edges,
                            partition_type=partition_type,
                            mdl=mdl,
                            modularity=mod,
                            replica_consistency=rc,
                            mdl_time_s=t_mdl,
                            modularity_time_s=t_mod,
                            rc_time_s=t_rc,
                        )
                    )

    return records


def ranking_agreement_report(records: List[PartitionScore]) -> Dict[str, Any]:
    """Check whether ``mdl_score`` ranks ground truth best, and agrees with modularity.

    Returns:
        Dict with:
        - ``ground_truth_best_rate``: fraction of (mu, n, seed) groups where
          ground truth got the lowest (best) MDL score among the three
          partitions.
        - ``mean_spearman_by_mu``: mean Spearman correlation, per ``mu``,
          between the MDL ranking and the modularity ranking of the three
          partitions in each group (1.0 = full agreement, negative = MDL
          flags something modularity doesn't).
        - ``disagreements``: groups where MDL and modularity disagree on
          which partition is best -- the interesting case where MDL might be
          catching a degenerate partition that modularity misses.
    """
    groups: Dict[Tuple[float, int, int], List[PartitionScore]] = defaultdict(list)
    for r in records:
        groups[(r.mu, r.n_nodes, r.seed)].append(r)

    gt_best_count = 0
    spearman_per_mu: Dict[float, List[float]] = defaultdict(list)
    disagreements: List[Dict[str, Any]] = []

    for (mu, n_nodes, seed), group in groups.items():
        by_type = {r.partition_type: r for r in group}
        mdl_vals = [r.mdl for r in group]
        if by_type["ground_truth"].mdl == min(mdl_vals):
            gt_best_count += 1

        if len(group) >= 2:
            # Lower MDL = better; higher modularity = better, so negate
            # modularity to compare both rankings in the same direction.
            rho, _ = spearmanr(
                [r.mdl for r in group], [-r.modularity for r in group]
            )
            spearman_per_mu[mu].append(rho)

        mdl_best = min(group, key=lambda r: r.mdl).partition_type
        mod_best = max(group, key=lambda r: r.modularity).partition_type
        if mdl_best != mod_best:
            disagreements.append(
                {
                    "mu": mu,
                    "n_nodes": n_nodes,
                    "seed": seed,
                    "mdl_best": mdl_best,
                    "modularity_best": mod_best,
                    "scores": {
                        r.partition_type: {
                            "mdl": r.mdl,
                            "modularity": r.modularity,
                        }
                        for r in group
                    },
                }
            )

    n_groups = len(groups)
    return {
        "ground_truth_best_rate": gt_best_count / n_groups if n_groups else float("nan"),
        "mean_spearman_by_mu": {
            mu: float(np.nanmean(vals)) for mu, vals in sorted(spearman_per_mu.items())
        },
        "disagreements": disagreements,
    }


def scaling_report(records: List[PartitionScore]) -> Dict[int, Dict[str, float]]:
    """Average per-metric compute time (seconds), grouped by graph size."""
    by_size: Dict[int, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        by_size[r.n_nodes]["mdl_score"].append(r.mdl_time_s)
        by_size[r.n_nodes]["multilayer_modularity"].append(r.modularity_time_s)
        by_size[r.n_nodes]["replica_consistency"].append(r.rc_time_s)

    return {
        n_nodes: {metric: float(np.mean(times)) for metric, times in metrics.items()}
        for n_nodes, metrics in sorted(by_size.items())
    }


def print_report(records: List[PartitionScore]) -> None:
    """Print a human-readable summary: ranking agreement + scaling."""
    ranking = ranking_agreement_report(records)
    scaling = scaling_report(records)

    print("=" * 72)
    print("MDL METRIC BENCHMARK REPORT")
    print("=" * 72)

    print(
        f"\nGround truth ranked best (lowest MDL) in "
        f"{ranking['ground_truth_best_rate']:.1%} of (mu, n, seed) groups"
    )

    print("\nMDL vs. modularity ranking agreement (Spearman rho) by mu:")
    for mu, rho in ranking["mean_spearman_by_mu"].items():
        print(f"  mu={mu:.2f}: rho={rho:+.3f}")

    if ranking["disagreements"]:
        print(
            f"\n{len(ranking['disagreements'])} group(s) where MDL and "
            "modularity pick a different 'best' partition:"
        )
        for d in ranking["disagreements"]:
            print(
                f"  mu={d['mu']:.2f} n={d['n_nodes']} seed={d['seed']}: "
                f"mdl picks '{d['mdl_best']}', modularity picks "
                f"'{d['modularity_best']}'"
            )
    else:
        print("\nNo disagreements between MDL's and modularity's top pick.")

    print("\nMean metric compute time (seconds) by graph size:")
    header = f"  {'n_nodes':>10} {'mdl_score':>12} {'modularity':>12} {'replica_consistency':>20}"
    print(header)
    for n_nodes, metrics in scaling.items():
        print(
            f"  {n_nodes:>10} {metrics['mdl_score']:>12.4f} "
            f"{metrics['multilayer_modularity']:>12.4f} "
            f"{metrics['replica_consistency']:>20.4f}"
        )
    print("=" * 72)


if __name__ == "__main__":
    results = run_benchmark()
    print_report(results)