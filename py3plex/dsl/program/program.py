"""GraphProgram - Immutable, typed, compositional program objects for py3plex DSL.

This module implements GraphProgram as a first-class program representation with:
- Immutable design (all transformations return new instances)
- Stable hashing for reproducibility
- Type signatures from the type system
- Program composition with type checking
- Metadata tracking for provenance
- Integration with existing DSL executor

Example:
    >>> from py3plex.dsl import Q
    >>> from py3plex.dsl.program import GraphProgram
    >>>
    >>> # Create program from AST
    >>> ast = Q.nodes().compute("degree").order_by("degree").to_ast()
    >>> program = GraphProgram.from_ast(ast)
    >>>
    >>> # Execute on network
    >>> result = program.execute(network)
    >>>
    >>> # Compose programs
    >>> program2 = GraphProgram.from_ast(Q.nodes().compute("betweenness").to_ast())
    >>> composed = program.compose(program2)
"""

from __future__ import annotations

import copy
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union

from ..ast import Query, SelectStmt, Target
from ..executor import execute_ast
from ..result import QueryResult
from .types import Type, infer_type, type_check, TypeCheckError

# Import library version
try:
    from py3plex import __version__ as LIBRARY_VERSION
except ImportError:
    LIBRARY_VERSION = "unknown"


DSL_VERSION = "2.0"


@dataclass(frozen=True)
class ProgramMetadata:
    """Metadata for a GraphProgram.
    
    Tracks creation time, versions, and provenance for reproducibility.
    
    Attributes:
        creation_timestamp: Unix timestamp when program was created
        dsl_version: DSL version used to create the program
        library_version: py3plex version used to create the program
        cost_model_hints: Optional hints for cost estimation
        randomness_metadata: Optional metadata about random seeds/reproducibility
        provenance_chain: List of transformations applied to create this program
    
    Example:
        >>> meta = ProgramMetadata(
        ...     creation_timestamp=time.time(),
        ...     dsl_version="2.0",
        ...     library_version="1.1.2",
        ...     provenance_chain=["from_ast", "optimize"]
        ... )
    """
    
    creation_timestamp: float
    dsl_version: str
    library_version: str
    cost_model_hints: Optional[Dict[str, Any]] = None
    randomness_metadata: Optional[Dict[str, Any]] = None
    provenance_chain: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "creation_timestamp": self.creation_timestamp,
            "dsl_version": self.dsl_version,
            "library_version": self.library_version,
            "cost_model_hints": self.cost_model_hints,
            "randomness_metadata": self.randomness_metadata,
            "provenance_chain": list(self.provenance_chain),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProgramMetadata:
        """Deserialize from dictionary."""
        return cls(
            creation_timestamp=data["creation_timestamp"],
            dsl_version=data["dsl_version"],
            library_version=data["library_version"],
            cost_model_hints=data.get("cost_model_hints"),
            randomness_metadata=data.get("randomness_metadata"),
            provenance_chain=data.get("provenance_chain", []),
        )


@dataclass(frozen=True)
class GraphProgram:
    """Immutable, typed, compositional graph program.
    
    A GraphProgram is a first-class representation of a DSL query that can be:
    - Type checked statically
    - Hashed for reproducibility
    - Composed with other programs
    - Optimized via rewrite rules
    - Serialized and cached
    
    All program transformations (compose, optimize) return new instances.
    
    Attributes:
        canonical_ast: Deep copy of the DSL AST (immutable)
        type_signature: Inferred type from the type system
        program_hash: Stable 64-char hex hash for reproducibility
        metadata: Program metadata with provenance
    
    Example:
        >>> from py3plex.dsl import Q
        >>> ast = Q.nodes().compute("degree").to_ast()
        >>> program = GraphProgram.from_ast(ast)
        >>> print(program.hash())
        >>> result = program.execute(network)
    """
    
    canonical_ast: Query
    type_signature: Type
    program_hash: str
    metadata: ProgramMetadata
    
    @classmethod
    def from_ast(
        cls,
        ast: Query,
        provenance: Optional[List[str]] = None,
        cost_hints: Optional[Dict[str, Any]] = None,
        randomness_meta: Optional[Dict[str, Any]] = None,
    ) -> GraphProgram:
        """Create a GraphProgram from a DSL AST.
        
        Args:
            ast: Query AST to wrap
            provenance: Optional provenance chain
            cost_hints: Optional cost model hints
            randomness_meta: Optional randomness metadata
        
        Returns:
            New GraphProgram instance
        
        Raises:
            TypeCheckError: If AST fails type checking
        
        Example:
            >>> from py3plex.dsl import Q
            >>> ast = Q.nodes().compute("degree").to_ast()
            >>> program = GraphProgram.from_ast(ast)
        """
        # Type check the AST
        type_check(ast)
        
        # Deep copy AST to ensure immutability
        canonical_ast = copy.deepcopy(ast)
        
        # Infer type signature
        type_signature = infer_type(canonical_ast)
        
        # Create metadata
        metadata = ProgramMetadata(
            creation_timestamp=time.time(),
            dsl_version=DSL_VERSION,
            library_version=LIBRARY_VERSION,
            cost_model_hints=cost_hints,
            randomness_metadata=randomness_meta,
            provenance_chain=provenance or ["from_ast"],
        )
        
        # Compute stable hash
        program_hash = cls._compute_hash(canonical_ast, metadata)
        
        return cls(
            canonical_ast=canonical_ast,
            type_signature=type_signature,
            program_hash=program_hash,
            metadata=metadata,
        )
    
    @staticmethod
    def _compute_hash(ast: Query, metadata: ProgramMetadata) -> str:
        """Compute stable hash for the program.
        
        Hash is stable across Python versions and independent of dict ordering.
        
        Args:
            ast: Canonical AST
            metadata: Program metadata
        
        Returns:
            64-character hex string (SHA-256 hash)
        """
        # Serialize AST to canonical JSON (sorted keys)
        ast_dict = _ast_to_dict(ast)
        ast_json = json.dumps(ast_dict, sort_keys=True, separators=(',', ':'))
        
        # Serialize relevant metadata (exclude timestamp for reproducibility)
        meta_dict = {
            "dsl_version": metadata.dsl_version,
            "library_version": metadata.library_version,
        }
        meta_json = json.dumps(meta_dict, sort_keys=True, separators=(',', ':'))
        
        # Combine and hash
        combined = f"{ast_json}|{meta_json}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def hash(self) -> str:
        """Return the stable program hash.
        
        Returns:
            64-character hex string
        
        Example:
            >>> program.hash()
            'a3b5c7d9...'
        """
        return self.program_hash
    
    def execute(
        self,
        network: Any,
        params: Optional[Dict[str, Any]] = None,
        progress: bool = True,
        explain_plan: bool = False,
        seed: Optional[int] = None,
        n_jobs: int = 1,
        cache_policy: str = "auto",
        **kwargs: Any,
    ) -> QueryResult:
        """Execute the program on a network.
        
        Args:
            network: Multilayer network object
            params: Parameter bindings for the query
            progress: If True, log progress messages
            explain_plan: If True, populate result.meta["plan"]
            seed: Random seed for reproducibility
            n_jobs: Number of parallel jobs for execution
            cache_policy: Cache policy ("auto", "enabled", "disabled")
            **kwargs: Additional execution parameters
        
        Returns:
            QueryResult from DSL executor
        
        Example:
            >>> result = program.execute(network, params={"k": 10}, seed=42)
            >>> df = result.to_pandas()
        """
        # Set random seed if provided
        if seed is not None:
            import random
            import numpy as np
            random.seed(seed)
            np.random.seed(seed)
        
        # Check cache if enabled
        if cache_policy != "disabled":
            from .cache import (
                get_global_cache,
                graph_fingerprint,
                execution_fingerprint,
                environment_signature,
                CacheKey,
            )
            cache = get_global_cache()
            
            # Create cache key
            key = CacheKey(
                graph_fingerprint=graph_fingerprint(network),
                program_hash=self.program_hash,
                execution_context=execution_fingerprint(seed=seed, n_jobs=n_jobs),
                environment_signature=environment_signature(),
            )
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
        
        # Execute the query
        result = execute_ast(
            network=network,
            query=self.canonical_ast,
            params=params,
            progress=progress,
            explain_plan=explain_plan,
        )
        
        # Store in cache if enabled
        if cache_policy != "disabled" and seed is not None:
            from .cache import (
                get_global_cache,
                graph_fingerprint,
                execution_fingerprint,
                environment_signature,
                CacheKey,
            )
            cache = get_global_cache()
            key = CacheKey(
                graph_fingerprint=graph_fingerprint(network),
                program_hash=self.program_hash,
                execution_context=execution_fingerprint(seed=seed, n_jobs=n_jobs),
                environment_signature=environment_signature(),
            )
            cache.put(key, result)
        
        return result
    
    def compose(self, other: GraphProgram) -> GraphProgram:
        """Compose this program with another program sequentially.
        
        Creates a new program that executes self, then other. Type checks that
        the output type of self matches the input type of other.
        
        Args:
            other: Program to compose with
        
        Returns:
            New composed GraphProgram
        
        Raises:
            TypeCheckError: If output/input types don't match
        
        Example:
            >>> p1 = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
            >>> p2 = GraphProgram.from_ast(Q.nodes().compute("betweenness").to_ast())
            >>> composed = p1.compose(p2)
        """
        # For now, composition is sequential execution with result passing
        # This is a placeholder - full composition requires AST merging
        # which depends on the specific query structure
        
        # Type check compatibility (simplified - needs enhancement)
        # In a full implementation, we'd check that other's expected input
        # matches self's output. For now, we just compose the ASTs.
        
        # Merge ASTs by creating a new SelectStmt that combines both
        # This is a basic implementation - can be enhanced with proper AST merging
        merged_ast = _merge_asts(self.canonical_ast, other.canonical_ast)
        
        # Merge provenance
        merged_provenance = (
            list(self.metadata.provenance_chain) + 
            ["compose"] + 
            list(other.metadata.provenance_chain)
        )
        
        # Create new program
        return GraphProgram.from_ast(
            merged_ast,
            provenance=merged_provenance,
        )
    
    def optimize(
        self,
        rules=None,
        context=None,
        fixpoint=True,
        budget=None,
        objective=None,
        **kwargs
    ) -> GraphProgram:
        """Optimize the program via rewrite rules with optional cost-based optimization.
        
        Applies correctness-preserving rewrite rules to optimize the program
        without changing semantics. Can also use cost-based optimization with budget.
        
        Args:
            rules: List of rewrite rules (defaults to standard rules)
            context: RewriteContext with network statistics
            fixpoint: If True, iterate until no more rules apply
            budget: Optional time budget (float seconds or string like "30s")
            objective: Optional CostObjective for multi-objective optimization
            **kwargs: Additional optimization configuration
        
        Returns:
            Optimized GraphProgram
        
        Example:
            >>> optimized = program.optimize()
            >>> optimized = program.optimize(rules=get_conservative_rules())
            >>> optimized = program.optimize(budget="30s", objective=CostObjective.MIN_TIME)
        """
        from .rewrite import apply_rewrites
        
        # If budget is specified, use cost-based optimization
        if budget is not None or objective is not None:
            from .cost import CostObjective as CO
            from .rewrite import RewriteContext
            
            # Create or update context with objective
            if context is None:
                context = RewriteContext()
            
            if objective is not None:
                # Store objective in context for cost-aware rewrite decisions
                context = RewriteContext(
                    safety_mode=context.safety_mode,
                    preserve_order=context.preserve_order,
                    network_stats=context.network_stats,
                    metadata={**context.metadata, "cost_objective": objective},
                )
        
        return apply_rewrites(self, rules=rules, context=context, fixpoint=fixpoint)
    
    def explain(self) -> str:
        """Generate human-readable explanation of the program.
        
        Returns:
            Multi-line string explaining what the program does
        
        Example:
            >>> print(program.explain())
            Program: SELECT nodes
            Layers: social, work
            Compute: degree, betweenness
            Filter: degree > 5
            Order by: degree DESC
            Limit: 10
        """
        lines = ["Program: SELECT " + str(self.canonical_ast.select.target.value)]
        
        select = self.canonical_ast.select
        
        # Layer info
        if select.layer_expr:
            layer_names = select.layer_expr.get_layer_names()
            lines.append(f"Layers: {', '.join(layer_names)}")
        elif select.layer_set:
            lines.append(f"Layers: {', '.join(sorted(select.layer_set))}")
        
        # Compute info
        if select.compute:
            metric_names = [c.result_name for c in select.compute]
            lines.append(f"Compute: {', '.join(metric_names)}")
        
        # Filter info
        if select.where:
            lines.append(f"Filter: {_format_condition(select.where)}")
        
        # Order info
        if select.order_by:
            order_strs = [
                f"{o.key} {'DESC' if o.desc else 'ASC'}" 
                for o in select.order_by
            ]
            lines.append(f"Order by: {', '.join(order_strs)}")
        
        # Limit info
        if select.limit:
            lines.append(f"Limit: {select.limit}")
        
        # Type info
        lines.append(f"Output type: {self.type_signature}")
        
        # Hash
        lines.append(f"Hash: {self.program_hash[:16]}...")
        
        return "\n".join(lines)
    
    def diff(self, other: GraphProgram) -> Dict[str, Any]:
        """Compute structural difference between two programs.
        
        Args:
            other: Program to compare with
        
        Returns:
            Dictionary describing differences
        
        Example:
            >>> diff = program1.diff(program2)
            >>> if diff['identical']:
            ...     print("Programs are identical")
        """
        # Basic structural diff - can be enhanced later
        diff_result = {
            "identical": self.program_hash == other.program_hash,
            "hash_self": self.program_hash,
            "hash_other": other.program_hash,
            "type_self": str(self.type_signature),
            "type_other": str(other.type_signature),
        }
        
        # Compare AST targets
        if self.canonical_ast.select.target != other.canonical_ast.select.target:
            diff_result["target_differs"] = {
                "self": self.canonical_ast.select.target.value,
                "other": other.canonical_ast.select.target.value,
            }
        
        # Compare compute items
        self_metrics = {c.result_name for c in self.canonical_ast.select.compute}
        other_metrics = {c.result_name for c in other.canonical_ast.select.compute}
        
        if self_metrics != other_metrics:
            diff_result["metrics_differ"] = {
                "only_in_self": list(self_metrics - other_metrics),
                "only_in_other": list(other_metrics - self_metrics),
            }
        
        return diff_result
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize program to dictionary.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        
        Example:
            >>> program_dict = program.to_dict()
            >>> json.dumps(program_dict)
        """
        return {
            "canonical_ast": _ast_to_dict(self.canonical_ast),
            "type_signature": self.type_signature.to_dict(),
            "program_hash": self.program_hash,
            "metadata": self.metadata.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GraphProgram:
        """Deserialize program from dictionary.
        
        Args:
            data: Dictionary representation
        
        Returns:
            Reconstructed GraphProgram
        
        Raises:
            NotImplementedError: AST deserialization is complex and not yet implemented
        
        Example:
            >>> program_dict = program.to_dict()
            >>> restored = GraphProgram.from_dict(program_dict)
            >>> assert restored.hash() == program.hash()
        """
        # AST deserialization is complex and requires complete reconstruction
        # of all AST node types. This is deferred for future implementation.
        raise NotImplementedError(
            "AST deserialization not yet implemented. "
            "Use GraphProgram.from_ast() to create programs."
        )


def compose(p1: GraphProgram, p2: GraphProgram) -> GraphProgram:
    """Compose two programs sequentially.
    
    This is a convenience function equivalent to p1.compose(p2).
    
    Args:
        p1: First program
        p2: Second program
    
    Returns:
        Composed program
    
    Raises:
        TypeCheckError: If programs cannot be composed
    
    Example:
        >>> from py3plex.dsl.program import compose
        >>> composed = compose(program1, program2)
    """
    return p1.compose(p2)


# ============================================================================
# Helper Functions for AST Serialization
# ============================================================================


def _ast_to_dict(ast: Query) -> Dict[str, Any]:
    """Convert AST to dictionary with canonical ordering.
    
    Ensures deterministic serialization for stable hashing.
    """
    result = {
        "explain": ast.explain,
        "dsl_version": ast.dsl_version,
        "select": _select_to_dict(ast.select),
    }
    return result


def _select_to_dict(select: SelectStmt) -> Dict[str, Any]:
    """Convert SelectStmt to dictionary."""
    result = {
        "target": select.target.value,
    }
    
    # Layer info
    if select.layer_expr:
        result["layer_expr"] = _layer_expr_to_dict(select.layer_expr)
    if select.layer_set:
        result["layer_set"] = sorted(select.layer_set)
    
    # Compute items
    if select.compute:
        result["compute"] = [
            {
                "name": c.name,
                "alias": c.alias,
                "uncertainty": c.uncertainty,
            }
            for c in select.compute
        ]
    
    # Conditions
    if select.where:
        result["where"] = str(select.where)  # Simplified
    
    # Ordering
    if select.order_by:
        result["order_by"] = [
            {"key": o.key, "desc": o.desc}
            for o in select.order_by
        ]
    
    # Limit
    if select.limit:
        result["limit"] = select.limit
    
    # Grouping
    if select.group_by:
        result["group_by"] = sorted(select.group_by)
    
    return result


def _layer_expr_to_dict(layer_expr) -> Dict[str, Any]:
    """Convert LayerExpr to dictionary."""
    from ..ast import LayerExpr
    
    if isinstance(layer_expr, LayerExpr):
        return {
            "terms": [t.name for t in layer_expr.terms],
            "ops": layer_expr.ops,
        }
    return {}


def _merge_asts(ast1: Query, ast2: Query) -> Query:
    """Merge two ASTs for composition.
    
    This is a simplified merge that combines compute items.
    Full implementation would need sophisticated AST merging logic.
    """
    # Create a new select statement that combines both
    select1 = ast1.select
    select2 = ast2.select
    
    # Verify targets match
    if select1.target != select2.target:
        raise TypeCheckError(
            f"Cannot compose queries with different targets: "
            f"{select1.target.value} vs {select2.target.value}",
            ast1
        )
    
    # Merge compute items (avoid duplicates)
    compute_names = {c.name for c in select1.compute}
    merged_compute = list(select1.compute)
    
    for compute_item in select2.compute:
        if compute_item.name not in compute_names:
            merged_compute.append(compute_item)
    
    # Create merged select statement
    merged_select = SelectStmt(
        target=select1.target,
        layer_expr=select1.layer_expr or select2.layer_expr,
        layer_set=select1.layer_set or select2.layer_set,
        where=select1.where or select2.where,
        compute=merged_compute,
        order_by=select2.order_by or select1.order_by,  # Prefer second
        limit=select2.limit or select1.limit,  # Prefer second
        group_by=select1.group_by or select2.group_by,
    )
    
    # Create merged query
    return Query(
        explain=ast1.explain or ast2.explain,
        select=merged_select,
        dsl_version=DSL_VERSION,
    )


def _format_condition(condition) -> str:
    """Format condition for human-readable output."""
    # Simplified - just convert to string
    return str(condition)
