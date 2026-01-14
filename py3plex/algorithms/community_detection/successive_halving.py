"""Successive Halving racing strategy for community detection algorithm selection.

This module implements Successive Halving (SH), a principled racing strategy
for efficient algorithm selection under multiple metrics and uncertainty.
"""

from __future__ import annotations

import math
import time
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from py3plex.algorithms.community_detection.budget import BudgetSpec, CommunityResult
from py3plex.algorithms.community_detection.runner import run_community_algorithm
from py3plex._parallel import spawn_seeds


@dataclass
class RacingHistory:
    """History of a Successive Halving racing run.

    Tracks which algorithms ran in each round, their performance, and
    elimination decisions.

    Attributes:
        rounds: List of round records (one per round)
        winner_algo_id: Winning algorithm ID
        finalists: List of finalist algorithm IDs (if underdetermined)
        status: Status string ("ok", "underdetermined", "error")
        total_runtime_ms: Total runtime across all rounds
    """

    rounds: List[Dict[str, Any]] = field(default_factory=list)
    winner_algo_id: Optional[str] = None
    finalists: List[str] = field(default_factory=list)
    status: str = "ok"
    total_runtime_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "rounds": self.rounds,
            "winner_algo_id": self.winner_algo_id,
            "finalists": self.finalists,
            "status": self.status,
            "total_runtime_ms": self.total_runtime_ms,
        }


@dataclass
class SuccessiveHalvingConfig:
    """Configuration for Successive Halving racer.

    Attributes:
        eta: Elimination factor (keep top 1/eta each round)
        rounds: Number of rounds (None = auto-compute)
        budget0: Initial budget
        budget_growth: Budget growth factor per round
        early_stop: Stop early if winner is clear
        tie_mode: How to handle ties ("keep_more" or "underdetermined")
        utility_method: Utility function ("mean_minus_std", "expected_regret", "prob_near_best")
        utility_lambda: Lambda parameter for mean_minus_std
        metric_weights: Dict of metric weights (None = equal weights)
        normalize_metrics: Whether to normalize metrics per round
    """

    eta: int = 3
    rounds: Optional[int] = None
    budget0: Optional[BudgetSpec] = None
    budget_growth: Optional[float] = None
    early_stop: bool = True
    tie_mode: str = "keep_more"
    utility_method: str = "mean_minus_std"
    utility_lambda: float = 1.0
    metric_weights: Optional[Dict[str, float]] = None
    normalize_metrics: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.eta < 2:
            raise ValueError(f"eta must be >= 2, got {self.eta}")

        if self.tie_mode not in ("keep_more", "underdetermined"):
            raise ValueError(
                f"tie_mode must be 'keep_more' or 'underdetermined', got '{self.tie_mode}'"
            )

        if self.utility_method not in (
            "mean_minus_std",
            "expected_regret",
            "prob_near_best",
        ):
            raise ValueError(
                f"utility_method must be 'mean_minus_std', 'expected_regret', or "
                f"'prob_near_best', got '{self.utility_method}'"
            )

        # Set defaults
        if self.budget0 is None:
            self.budget0 = BudgetSpec(
                max_iter=5,
                n_restarts=1,
                resolution_trials=3,
                uq_samples=10,
            )

        if self.budget_growth is None:
            self.budget_growth = float(self.eta)


class SuccessiveHalvingRacer:
    """Successive Halving racer for community detection algorithm selection.

    Implements a racing strategy that:
    1. Starts with all candidate algorithms
    2. Evaluates on increasing budgets across rounds
    3. Eliminates worst performers each round (keeps top 1/eta)
    4. Returns winner when one algorithm remains

    The racer is UQ-aware: utilities are computed from distributions over
    metrics, accounting for uncertainty in algorithm performance.

    Examples:
        >>> from py3plex.core import multinet
        >>> from py3plex.algorithms.community_detection.successive_halving import (
        ...     SuccessiveHalvingRacer, SuccessiveHalvingConfig, BudgetSpec
        ... )
        >>>
        >>> # Create network
        >>> net = multinet.multi_layer_network(directed=False)
        >>> # ... add nodes and edges ...
        >>>
        >>> # Configure racer
        >>> config = SuccessiveHalvingConfig(
        ...     eta=3,
        ...     budget0=BudgetSpec(max_iter=5, uq_samples=10),
        ...     utility_method="mean_minus_std",
        ... )
        >>>
        >>> # Run race
        >>> racer = SuccessiveHalvingRacer(config, seed=42)
        >>> result = racer.race(
        ...     network=net,
        ...     algorithm_ids=["louvain", "leiden"],
        ...     metric_names=["modularity", "coverage"],
        ... )
        >>>
        >>> print(f"Winner: {result.winner_algo_id}")
        >>> print(f"Rounds: {len(result.rounds)}")
    """

    def __init__(self, config: SuccessiveHalvingConfig, seed: int = 0):
        """Initialize racer.

        Args:
            config: Racing configuration
            seed: Base random seed for reproducibility
        """
        self.config = config
        self.seed = seed

    def race(
        self,
        network: Any,
        algorithm_ids: List[str],
        metric_names: List[str],
        n_jobs: int = 1,
    ) -> RacingHistory:
        """Run successive halving race.

        Args:
            network: Multilayer network
            algorithm_ids: List of candidate algorithm IDs
            metric_names: List of metric names to evaluate
            n_jobs: Number of parallel jobs (not yet implemented)

        Returns:
            RacingHistory with winner and full round-by-round history
        """
        if not algorithm_ids:
            raise ValueError("Must provide at least one algorithm")

        if not metric_names:
            raise ValueError("Must provide at least one metric")

        start_time = time.time()

        # Compute number of rounds if not specified
        n_rounds = self.config.rounds
        if n_rounds is None:
            n_rounds = math.ceil(
                math.log(len(algorithm_ids)) / math.log(self.config.eta)
            )

        # Build budget schedule
        budgets = self._build_budget_schedule(n_rounds)

        # Initialize history
        history = RacingHistory()

        # Survivors start as all algorithms
        survivors = list(algorithm_ids)

        # Run rounds
        for round_idx in range(n_rounds):
            if len(survivors) <= 1:
                # Only one survivor left, stop early
                break

            budget = budgets[round_idx]

            # Spawn seeds for this round (deterministic per round and algorithm)
            round_seeds = self._spawn_round_seeds(round_idx, len(survivors))

            # Run all survivors on this budget
            round_results = self._run_round(
                network=network,
                algorithm_ids=survivors,
                budget=budget,
                round_seeds=round_seeds,
            )

            # Evaluate metrics for all survivors
            metrics_df = self._evaluate_metrics(
                network=network,
                round_results=round_results,
                metric_names=metric_names,
            )

            # Aggregate metrics to scalar scores
            scores = self._aggregate_metrics(
                metrics_df=metrics_df,
                metric_names=metric_names,
            )

            # Compute utilities (UQ-aware)
            utilities = self._compute_utilities(
                scores=scores,
                round_results=round_results,
            )

            # Select survivors for next round
            survivors, eliminated = self._select_survivors(
                survivors=survivors,
                utilities=utilities,
                round_idx=round_idx,
                n_rounds=n_rounds,
            )

            # Record round history
            round_record = {
                "round": round_idx,
                "budget": budget.to_dict(),
                "algorithms": [r.algo_id for r in round_results],
                "metrics": metrics_df.to_dict(orient="records"),
                "utilities": utilities,
                "survivors": survivors,
                "eliminated": eliminated,
            }
            history.rounds.append(round_record)

            # Check early stopping
            if self.config.early_stop and len(survivors) == 1:
                break

        # Determine winner
        if len(survivors) == 1:
            history.winner_algo_id = survivors[0]
            history.finalists = [survivors[0]]
            history.status = "ok"
        elif len(survivors) > 1:
            # Underdetermined
            history.winner_algo_id = survivors[0]  # Arbitrary choice
            history.finalists = survivors
            history.status = "underdetermined"
        else:
            # Should not happen
            history.status = "error"
            warnings.warn("No survivors remaining after race", stacklevel=2)

        history.total_runtime_ms = (time.time() - start_time) * 1000

        return history

    def _build_budget_schedule(self, n_rounds: int) -> List[BudgetSpec]:
        """Build sequence of budgets for rounds.

        Args:
            n_rounds: Number of rounds

        Returns:
            List of BudgetSpec (one per round)
        """
        budgets = []
        current = self.config.budget0

        # Default caps to avoid explosion
        caps = {
            "max_iter": 1000,
            "n_restarts": 20,
            "resolution_trials": 50,
            "uq_samples": 200,
        }

        for _ in range(n_rounds):
            budgets.append(current)
            # Grow for next round
            current = current.scale(self.config.budget_growth, caps=caps)

        return budgets

    def _spawn_round_seeds(self, round_idx: int, n_algorithms: int) -> List[int]:
        """Spawn deterministic seeds for a round.

        Args:
            round_idx: Round index
            n_algorithms: Number of algorithms in this round

        Returns:
            List of seeds (one per algorithm)
        """
        # Derive round seed from base seed and round index
        round_seed = hash((self.seed, round_idx)) & 0xFFFFFFFF

        # Spawn algorithm seeds from round seed
        algo_seeds = spawn_seeds(round_seed, n_algorithms)

        return algo_seeds

    def _run_round(
        self,
        network: Any,
        algorithm_ids: List[str],
        budget: BudgetSpec,
        round_seeds: List[int],
    ) -> List[CommunityResult]:
        """Run all algorithms in a round.

        Args:
            network: Multilayer network
            algorithm_ids: List of algorithm IDs to run
            budget: Budget for this round
            round_seeds: Seeds for each algorithm

        Returns:
            List of CommunityResult
        """
        results = []

        for algo_id, seed in zip(algorithm_ids, round_seeds):
            try:
                result = run_community_algorithm(
                    algorithm_id=algo_id,
                    network=network,
                    budget=budget,
                    seed=seed,
                )
                results.append(result)
            except Exception as e:
                warnings.warn(f"Algorithm {algo_id} failed: {e}", stacklevel=2)
                # Continue without this algorithm
                continue

        return results

    def _evaluate_metrics(
        self,
        network: Any,
        round_results: List[CommunityResult],
        metric_names: List[str],
    ) -> pd.DataFrame:
        """Evaluate metrics for all algorithms in a round.

        Args:
            network: Multilayer network
            round_results: Results from all algorithms
            metric_names: Metrics to evaluate

        Returns:
            DataFrame with columns: algo_id, metric1, metric2, ...
        """
        from py3plex.algorithms.community_detection import multilayer_modularity
        from py3plex.algorithms.community_detection.multilayer_quality_metrics import (
            replica_consistency,
            layer_entropy,
        )

        rows = []

        for result in round_results:
            row = {"algo_id": result.algo_id}

            for metric_name in metric_names:
                try:
                    if metric_name == "modularity":
                        value = multilayer_modularity(
                            network=network,
                            communities=result.partition,
                        )
                    elif metric_name == "coverage":
                        # Fraction of nodes in non-singleton communities
                        comm_sizes = {}
                        for node, comm in result.partition.items():
                            comm_sizes[comm] = comm_sizes.get(comm, 0) + 1

                        non_singleton = sum(
                            1
                            for node, comm in result.partition.items()
                            if comm_sizes[comm] > 1
                        )
                        value = (
                            non_singleton / len(result.partition)
                            if result.partition
                            else 0.0
                        )

                    elif metric_name == "stability":
                        # Use UQ data if available
                        if result.get("uq_data"):
                            # Compute stability from co-assignment matrix
                            if hasattr(result["uq_data"], "node_confidence"):
                                confidence = result["uq_data"].node_confidence()
                                value = float(np.mean(confidence))
                            else:
                                value = np.nan  # UQ data present but no confidence
                        else:
                            value = np.nan  # UQ not available

                    elif metric_name == "replica_consistency":
                        # Multilayer coherence metric
                        value = replica_consistency(result.partition, network)

                    elif metric_name == "layer_entropy":
                        # Multilayer degeneracy guardrail
                        value = layer_entropy(result.partition, network)

                    else:
                        warnings.warn(
                            f"Metric '{metric_name}' not implemented", stacklevel=2
                        )
                        value = 0.0

                    row[metric_name] = value

                except Exception as e:
                    warnings.warn(
                        f"Failed to compute {metric_name} for {result.algo_id}: {e}",
                        stacklevel=2,
                    )
                    row[metric_name] = np.nan

            rows.append(row)

        return pd.DataFrame(rows)

    def _aggregate_metrics(
        self,
        metrics_df: pd.DataFrame,
        metric_names: List[str],
    ) -> Dict[str, float]:
        """Aggregate multiple metrics into scalar scores.

        Args:
            metrics_df: DataFrame with metrics
            metric_names: List of metric names

        Returns:
            Dict mapping algo_id -> scalar score
        """
        # Normalize metrics if enabled
        if self.config.normalize_metrics:
            normalized_df = metrics_df.copy()

            for metric in metric_names:
                if metric in normalized_df.columns:
                    values = normalized_df[metric].values

                    # Robust min-max normalization
                    valid_values = values[~np.isnan(values)]
                    if len(valid_values) > 0:
                        min_val = np.min(valid_values)
                        max_val = np.max(valid_values)

                        if max_val > min_val:
                            normalized_df[metric] = (values - min_val) / (
                                max_val - min_val
                            )
                        else:
                            normalized_df[metric] = 0.5  # All same, neutral
                    else:
                        normalized_df[metric] = 0.0
        else:
            normalized_df = metrics_df

        # Apply weights
        weights = self.config.metric_weights
        if weights is None:
            # Equal weights
            weights = {m: 1.0 / len(metric_names) for m in metric_names}
        else:
            # Normalize weights
            total = sum(weights.get(m, 0.0) for m in metric_names)
            if total > 0:
                weights = {m: weights.get(m, 0.0) / total for m in metric_names}
            else:
                weights = {m: 1.0 / len(metric_names) for m in metric_names}

        # Compute weighted sum
        scores = {}
        for _, row in normalized_df.iterrows():
            algo_id = row["algo_id"]
            score = 0.0

            for metric in metric_names:
                if metric in row and not np.isnan(row[metric]):
                    score += weights[metric] * row[metric]

            scores[algo_id] = score

        return scores

    def _compute_utilities(
        self,
        scores: Dict[str, float],
        round_results: List[CommunityResult],
    ) -> Dict[str, float]:
        """Compute UQ-aware utilities from scores.

        For now, we use point estimates. True UQ-aware utility would require
        running each algorithm multiple times or using distributional data.

        Args:
            scores: Dict of algo_id -> scalar score
            round_results: Results from algorithms

        Returns:
            Dict of algo_id -> utility
        """
        # For mean_minus_std: U = mean(score) - lambda * std(score)
        # Since we have point estimates, std = 0, so U = score

        utilities = {}

        if self.config.utility_method == "mean_minus_std":
            # Point estimate: utility = score
            for algo_id, score in scores.items():
                utilities[algo_id] = score

        elif self.config.utility_method == "expected_regret":
            # E[max(scores) - score]
            # With point estimates: regret = max(scores) - score
            max_score = max(scores.values()) if scores else 0.0
            for algo_id, score in scores.items():
                regret = max_score - score
                utilities[algo_id] = -regret  # Negative regret (higher is better)

        elif self.config.utility_method == "prob_near_best":
            # P(score >= max - eps)
            # With point estimates: binary (1 if near best, 0 otherwise)
            max_score = max(scores.values()) if scores else 0.0
            eps = 0.01
            for algo_id, score in scores.items():
                utilities[algo_id] = 1.0 if score >= max_score - eps else 0.0

        return utilities

    def _select_survivors(
        self,
        survivors: List[str],
        utilities: Dict[str, float],
        round_idx: int,
        n_rounds: int,
    ) -> Tuple[List[str], List[str]]:
        """Select survivors for next round.

        Args:
            survivors: Current survivors
            utilities: Utilities for each algorithm
            round_idx: Current round index
            n_rounds: Total rounds

        Returns:
            Tuple of (new_survivors, eliminated)
        """
        # Sort by utility (descending)
        sorted_algos = sorted(
            survivors, key=lambda a: utilities.get(a, -float("inf")), reverse=True
        )

        # Compute number to keep
        n_keep = max(1, math.ceil(len(survivors) / self.config.eta))

        # Keep top algorithms
        new_survivors = sorted_algos[:n_keep]
        eliminated = sorted_algos[n_keep:]

        return new_survivors, eliminated
