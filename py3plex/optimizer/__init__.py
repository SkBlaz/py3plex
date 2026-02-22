"""Cost-based optimizer layer for py3plex DSL v2.

This package provides a logical/physical query optimizer that sits between
AST compilation and execution:

    Builder/DSL → AST → LogicalPlanBuilder → Optimizer → PhysicalPlan → Executor → QueryResult

Public API
----------
- ``optimize_query(ast, network, params)`` – one-shot optimize + return
  (optimized_ast, optimizer_metadata)
- ``NetworkStats`` – network statistics for cost estimation
- ``CostEstimate`` – result of cost estimation
- ``Optimizer`` – main optimizer class
"""

from .cost_model import CostEstimate, CostModel, NetworkStats
from .logical_plan import LogicalPlanBuilder
from .optimizer import Optimizer, optimize_query
from .physical_plan import PhysicalPlan, PhysicalPlanBuilder
from .plan_nodes import (
    LogicalAggregate,
    LogicalCompute,
    LogicalCoverage,
    LogicalFilter,
    LogicalGroupByLayer,
    LogicalGroupByLayerPair,
    LogicalLayerFilter,
    LogicalLimit,
    LogicalNullModel,
    LogicalOp,
    LogicalOrderBy,
    LogicalProject,
    LogicalScanEdges,
    LogicalScanNodes,
    LogicalUQ,
    PhysicalAggregateHash,
    PhysicalAggregateSort,
    PhysicalCoverage,
    PhysicalEdgeScanNX,
    PhysicalFilterPython,
    PhysicalFilterVectorized,
    PhysicalLayerPushdown,
    PhysicalLimitEarly,
    PhysicalNodeScanNX,
    PhysicalOp,
    PhysicalTopKHeap,
)
from .rules import BUILTIN_RULES, OptimizationRule

__all__ = [
    # plan nodes
    "LogicalOp",
    "LogicalScanNodes",
    "LogicalScanEdges",
    "LogicalFilter",
    "LogicalLayerFilter",
    "LogicalCompute",
    "LogicalAggregate",
    "LogicalGroupByLayer",
    "LogicalGroupByLayerPair",
    "LogicalCoverage",
    "LogicalOrderBy",
    "LogicalLimit",
    "LogicalUQ",
    "LogicalNullModel",
    "LogicalProject",
    "PhysicalOp",
    "PhysicalNodeScanNX",
    "PhysicalEdgeScanNX",
    "PhysicalFilterPython",
    "PhysicalFilterVectorized",
    "PhysicalLayerPushdown",
    "PhysicalAggregateHash",
    "PhysicalAggregateSort",
    "PhysicalCoverage",
    "PhysicalTopKHeap",
    "PhysicalLimitEarly",
    # cost model
    "NetworkStats",
    "CostEstimate",
    "CostModel",
    # builders
    "LogicalPlanBuilder",
    "PhysicalPlan",
    "PhysicalPlanBuilder",
    # optimizer
    "Optimizer",
    "optimize_query",
    # rules
    "OptimizationRule",
    "BUILTIN_RULES",
]
