"""Main Optimizer class and convenience function for the py3plex optimizer.

The :class:`Optimizer` ties together the logical plan builder, rule engine,
cost model, and physical plan builder.  The public ``optimize_query``
convenience function runs the full pipeline and returns an
*(optimized_ast_equivalent, optimizer_metadata)* pair that the DSL executor
can consume.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from .cost_model import CostEstimate, CostModel, NetworkStats
from .physical_plan import PhysicalPlan, PhysicalPlanBuilder
from .plan_nodes import LogicalOp
from .rules import RuleEngine

logger = logging.getLogger(__name__)


class Optimizer:
    """Cost-based query optimizer.

    Parameters
    ----------
    cost_model:
        :class:`CostModel` instance used to estimate plan costs.  A default
        instance is created automatically when *None*.
    enable_rule_based:
        Apply rule-based rewrites (default: ``True``).
    enable_cost_based:
        Use cost estimates to choose between alternative plans (default:
        ``True``).
    max_iter:
        Maximum number of rule-engine fixpoint iterations (default: ``10``).
    backend:
        Graph backend name forwarded to the physical planner (default:
        ``"networkx"``).
    """

    def __init__(
        self,
        cost_model: Optional[CostModel] = None,
        enable_rule_based: bool = True,
        enable_cost_based: bool = True,
        max_iter: int = 10,
        backend: str = "networkx",
    ) -> None:
        self.cost_model = cost_model or CostModel()
        self.enable_rule_based = enable_rule_based
        self.enable_cost_based = enable_cost_based
        self.max_iter = max_iter
        self.backend = backend
        self._rule_engine = RuleEngine(max_iter=max_iter)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def optimize(
        self,
        logical_plan: LogicalOp,
        stats: Optional[NetworkStats] = None,
    ) -> Tuple[PhysicalPlan, Dict[str, Any]]:
        """Optimize *logical_plan* and return a :class:`PhysicalPlan` plus
        optimizer metadata suitable for provenance.

        Parameters
        ----------
        logical_plan:
            Root of the logical operator tree built by
            :class:`~py3plex.optimizer.logical_plan.LogicalPlanBuilder`.
        stats:
            Optional :class:`NetworkStats`.  When *None* a default stats
            object is used (all-zero; disables cost-based rules).

        Returns
        -------
        physical_plan:
            Executable :class:`PhysicalPlan`.
        metadata:
            Dictionary suitable for ``result.meta["optimizer"]``.
        """
        if stats is None:
            stats = NetworkStats()

        t_start = time.monotonic()

        # --- 1. estimate initial cost ----------------------------------------
        initial_estimate: CostEstimate = self.cost_model.estimate(logical_plan, stats)
        initial_cost = initial_estimate.total_cost

        # --- 2. rule-based rewrites -------------------------------------------
        applied_rules: List[str] = []
        if self.enable_rule_based:
            logical_plan, applied_rules = self._rule_engine.run(logical_plan)

        # --- 3. estimate final cost after rewrites ----------------------------
        final_estimate: CostEstimate = self.cost_model.estimate(logical_plan, stats)
        final_cost = final_estimate.total_cost

        # --- 4. build physical plan -------------------------------------------
        planner = PhysicalPlanBuilder(backend=self.backend)
        physical_plan = planner.build(logical_plan, stats)

        t_end = time.monotonic()

        metadata: Dict[str, Any] = {
            "enabled": True,
            "rules_applied": applied_rules,
            "cost_before": round(initial_cost, 4),
            "cost_after": round(final_cost, 4),
            "plan_hash": physical_plan.plan_hash,
            "estimated_rows": final_estimate.estimated_rows,
            "backend": self.backend,
            "optimizer_time_ms": round((t_end - t_start) * 1000, 3),
        }

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Optimizer: %d rule(s) applied, cost %.2f → %.2f, plan_hash=%s",
                len(applied_rules),
                initial_cost,
                final_cost,
                physical_plan.plan_hash,
            )

        return physical_plan, metadata


# ---------------------------------------------------------------------------
# Convenience one-shot function
# ---------------------------------------------------------------------------


def optimize_query(
    ast: Any,
    network: Any = None,
    params: Optional[Dict[str, Any]] = None,
    backend: str = "networkx",
    enable_rule_based: bool = True,
    enable_cost_based: bool = True,
    max_iter: int = 10,
) -> Tuple[PhysicalPlan, Dict[str, Any]]:
    """One-shot helper: build logical plan → optimise → return physical plan.

    Parameters
    ----------
    ast:
        Compiled DSL AST (typically a ``SelectStmt`` dataclass).
    network:
        Optional multilayer network used to extract :class:`NetworkStats`.
    params:
        Optional parameter bindings (forwarded to the logical plan builder).
    backend:
        Graph backend name.
    enable_rule_based, enable_cost_based, max_iter:
        Forwarded to :class:`Optimizer`.

    Returns
    -------
    (physical_plan, metadata)
    """
    from .logical_plan import LogicalPlanBuilder

    # Build logical plan from AST
    builder = LogicalPlanBuilder()
    logical_plan = builder.build(ast, params=params or {})

    # Extract network stats if a network was provided
    stats: Optional[NetworkStats] = None
    if network is not None:
        stats = NetworkStats.from_network(network)

    optimizer = Optimizer(
        enable_rule_based=enable_rule_based,
        enable_cost_based=enable_cost_based,
        max_iter=max_iter,
        backend=backend,
    )
    return optimizer.optimize(logical_plan, stats)
