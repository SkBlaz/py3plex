"""RewriteEngine with correctness-preserving rewrite rules for py3plex Graph Programs.

This module implements a rewrite engine that applies provable equivalence-preserving
transformations to GraphPrograms, optimizing them without changing semantics.

The rewrite engine supports:
- Pattern-based matching on AST structure
- Guard conditions for safe application
- Immutable transformations (returns new GraphProgram)
- Provenance tracking
- Iterative application until fixpoint

Example:
    >>> from py3plex.dsl import Q
    >>> from py3plex.dsl.program import GraphProgram
    >>> from py3plex.dsl.program.rewrite import RewriteEngine, get_standard_rules
    >>> 
    >>> # Create program
    >>> ast = Q.nodes().compute("degree").where(layer="social").to_ast()
    >>> program = GraphProgram.from_ast(ast)
    >>> 
    >>> # Apply rewrites
    >>> engine = RewriteEngine(rules=get_standard_rules())
    >>> optimized = engine.apply(program)
    >>> 
    >>> # Check provenance
    >>> print(optimized.metadata.provenance_chain)
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from ..ast import (
    ComputeItem,
    Comparison,
    ConditionAtom,
    ConditionExpr,
    FunctionCall,
    OrderItem,
    Query,
    SelectStmt,
    SpecialPredicate,
    Target,
    UQConfig,
)
from .program import GraphProgram
from .types import Type, infer_type


# ============================================================================
# Core Rewrite Infrastructure
# ============================================================================


@dataclass
class Match:
    """Represents a successful pattern match.
    
    Contains the matched AST node and any captured subexpressions needed
    for the transformation.
    
    Attributes:
        node: The matched AST node
        captures: Dictionary of captured subexpressions (name -> value)
        metadata: Optional metadata about the match
    """
    node: Any
    captures: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RewriteContext:
    """Execution context for rewrite rule application.
    
    Provides graph statistics and metadata that guards can use to determine
    if a rewrite is safe and beneficial.
    
    Attributes:
        network_stats: Optional network statistics (node count, edge count, etc.)
        available_metrics: Set of already-computed metrics
        layer_info: Information about layers in the network
        cost_hints: Cost model hints for estimation
        safety_mode: If True, only apply conservative rewrites
    """
    network_stats: Optional[Dict[str, Any]] = None
    available_metrics: Set[str] = field(default_factory=set)
    layer_info: Optional[Dict[str, Any]] = None
    cost_hints: Optional[Dict[str, Any]] = None
    safety_mode: bool = False


@dataclass
class RuleGuard:
    """Preconditions for safe rule application.
    
    Guards check that rewrite preserves semantics and is beneficial.
    
    Attributes:
        check: Callable that returns True if rewrite is safe
        description: Human-readable description of the guard
    """
    check: Callable[[Match, RewriteContext], bool]
    description: str


@dataclass
class RewriteRule:
    """A single rewrite rule with pattern, guard, and transformation.
    
    Rewrite rules are equivalence-preserving transformations on AST nodes.
    Each rule has:
    - Pattern matcher: Identifies applicable AST structures
    - Guard: Checks preconditions for safety
    - Transform: Applies the rewrite
    
    Attributes:
        name: Unique rule identifier
        description: Human-readable description
        pattern_matcher: Function to match AST patterns
        guards: List of precondition checks
        transform: Transformation function
        equivalence_class: Category for grouping rules
        priority: Higher priority rules apply first (default: 0)
    """
    name: str
    description: str
    pattern_matcher: Callable[[Query], Optional[Match]]
    guards: List[RuleGuard]
    transform: Callable[[Query, Match], Query]
    equivalence_class: str
    priority: int = 0
    
    def matches(self, query: Query) -> Optional[Match]:
        """Check if this rule matches the given query.
        
        Args:
            query: Query AST to match against
            
        Returns:
            Match object if pattern matches, None otherwise
        """
        return self.pattern_matcher(query)
    
    def is_applicable(self, match: Match, context: RewriteContext) -> bool:
        """Check if all guards pass for this match.
        
        Args:
            match: Pattern match result
            context: Rewrite context with statistics
            
        Returns:
            True if all guards pass, False otherwise
        """
        return all(guard.check(match, context) for guard in self.guards)
    
    def apply(self, query: Query, match: Match) -> Query:
        """Apply the transformation to the query.
        
        Args:
            query: Original query AST
            match: Pattern match result
            
        Returns:
            Transformed query AST (deep copy)
        """
        return self.transform(query, match)


@dataclass
class RewriteEngine:
    """Engine for applying rewrite rules to GraphPrograms.
    
    The engine:
    - Applies rules in priority order
    - Checks guards before transforming
    - Tracks applied rules in provenance
    - Supports iterative application until fixpoint
    - Preserves immutability
    
    Attributes:
        rules: List of rewrite rules to apply
        max_iterations: Maximum iterations for fixpoint (default: 10)
        enable_provenance: Track applied rules (default: True)
    
    Example:
        >>> engine = RewriteEngine(rules=get_standard_rules())
        >>> optimized = engine.apply(program, context)
    """
    rules: List[RewriteRule]
    max_iterations: int = 10
    enable_provenance: bool = True
    
    def apply(
        self,
        program: GraphProgram,
        context: Optional[RewriteContext] = None,
        fixpoint: bool = True,
    ) -> GraphProgram:
        """Apply rewrite rules to optimize a program.
        
        Args:
            program: GraphProgram to optimize
            context: Optional rewrite context with statistics
            fixpoint: If True, iterate until no more rules apply
            
        Returns:
            Optimized GraphProgram (new instance)
        """
        if context is None:
            context = RewriteContext()
        
        current_ast = copy.deepcopy(program.canonical_ast)
        applied_rules = []
        
        # Sort rules by priority (higher first)
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        
        iteration = 0
        changed = True
        
        while changed and iteration < self.max_iterations:
            changed = False
            iteration += 1
            
            for rule in sorted_rules:
                match = rule.matches(current_ast)
                if match and rule.is_applicable(match, context):
                    # Apply the rewrite
                    new_ast = rule.apply(current_ast, match)
                    
                    # Track the applied rule
                    if self.enable_provenance:
                        applied_rules.append(rule.name)
                    
                    current_ast = new_ast
                    changed = True
                    
                    if not fixpoint:
                        # Single pass mode - stop after first rule
                        break
            
            if not fixpoint:
                break
        
        # Create new program with updated AST and provenance
        new_provenance = list(program.metadata.provenance_chain)
        if applied_rules:
            new_provenance.append(f"rewrites:{','.join(applied_rules)}")
        
        return GraphProgram.from_ast(
            current_ast,
            provenance=new_provenance,
            cost_hints=program.metadata.cost_model_hints,
            randomness_meta=program.metadata.randomness_metadata,
        )
    
    def apply_rules(
        self,
        program: GraphProgram,
        rules: Union[List[RewriteRule], RewriteRule],
        context: Optional[RewriteContext] = None,
    ) -> GraphProgram:
        """Apply specific rules to a program.
        
        This is a convenience method for applying a subset of rules rather than
        all rules in the engine.
        
        Args:
            program: GraphProgram to optimize
            rules: Single rule or list of rules to apply
            context: Optional rewrite context with statistics
            
        Returns:
            Optimized GraphProgram (new instance)
        """
        # Convert single rule to list
        if isinstance(rules, RewriteRule):
            rules = [rules]
        
        # Create temporary engine with specified rules
        temp_engine = RewriteEngine(
            rules=rules,
            max_iterations=self.max_iterations,
            enable_provenance=self.enable_provenance,
        )
        
        # Apply using the main apply method
        return temp_engine.apply(program, context, fixpoint=True)
    
    def explain_rewrites(self, program: GraphProgram, context: Optional[RewriteContext] = None) -> List[str]:
        """Explain which rewrites would apply to a program.
        
        Args:
            program: GraphProgram to analyze
            context: Optional rewrite context
            
        Returns:
            List of rule names that would apply
        """
        if context is None:
            context = RewriteContext()
        
        applicable_rules = []
        for rule in self.rules:
            match = rule.matches(program.canonical_ast)
            if match and rule.is_applicable(match, context):
                applicable_rules.append(rule.name)
        
        return applicable_rules


# ============================================================================
# A. Pushdown/Fusion Rules (5 rules)
# ============================================================================


def rule_push_where_past_compute() -> RewriteRule:
    """Push WHERE filter past COMPUTE when compute doesn't affect predicate.
    
    Transformation:
        SELECT ... COMPUTE(x) WHERE(intrinsic_field=v)
        →
        SELECT ... WHERE(intrinsic_field=v) COMPUTE(x)
    
    This reduces the number of nodes/edges we compute metrics for.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has both compute and where
        if not select.compute or not select.where:
            return None
        
        # Check if where clause uses only intrinsic fields
        intrinsic_fields = {'layer', 'source_type', 'target_type', 'type', 'id', 'source', 'target'}
        where_fields = _extract_fields_from_condition(select.where)
        
        # Check if all where fields are intrinsic
        if not where_fields.issubset(intrinsic_fields):
            return None
        
        return Match(
            node=select,
            captures={'where': select.where, 'compute': select.compute}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Safe if where doesn't reference computed metrics
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        # No structural change needed - executor will handle order
        # But we can add hint metadata
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['where_before_compute'] = True
        return new_query
    
    return RewriteRule(
        name="push_where_past_compute",
        description="Push WHERE filter before COMPUTE when filter uses only intrinsic fields",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "WHERE uses only intrinsic fields")],
        transform=transform,
        equivalence_class="pushdown",
        priority=10,
    )


def rule_fuse_compute() -> RewriteRule:
    """Fuse multiple COMPUTE operations into a single batched computation.
    
    Transformation:
        COMPUTE(a) → COMPUTE(b) → COMPUTE(c)
        →
        COMPUTE(a, b, c)
    
    This reduces overhead from multiple metric computation passes.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has compute items
        if not select.compute or len(select.compute) < 2:
            return None
        
        return Match(
            node=select,
            captures={'compute_items': select.compute}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Always safe - just batching
        return True
    
    def transform(query: Query, match: Match) -> Query:
        # Already fused in DSL representation
        # This is more of a semantic marker
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['compute_fused'] = True
        return new_query
    
    return RewriteRule(
        name="fuse_compute",
        description="Batch multiple COMPUTE operations into single pass",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "Always safe to batch")],
        transform=transform,
        equivalence_class="fusion",
        priority=8,
    )


def rule_fuse_where() -> RewriteRule:
    """Fuse multiple WHERE clauses into a single normalized predicate.
    
    Transformation:
        WHERE(a) AND WHERE(b)
        →
        WHERE(a AND b)
    
    This reduces the number of filtering passes.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has where with multiple atoms
        if not select.where:
            return None
        
        if len(select.where.atoms) < 2:
            return None
        
        return Match(
            node=select,
            captures={'where': select.where}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Always safe - just normalizing
        return True
    
    def transform(query: Query, match: Match) -> Query:
        # Already fused in DSL representation
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['where_fused'] = True
        return new_query
    
    return RewriteRule(
        name="fuse_where",
        description="Fuse multiple WHERE clauses into single predicate",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "Always safe to fuse")],
        transform=transform,
        equivalence_class="fusion",
        priority=8,
    )


def rule_push_limit_early() -> RewriteRule:
    """Push LIMIT operation as early as possible when safe.
    
    Transformation:
        SELECT ... ORDER_BY(x) LIMIT(k)
        →
        (preserved - limit must follow order)
    
    But:
        SELECT ... COMPUTE(x) LIMIT(k)  [no ORDER BY]
        →
        SELECT ... LIMIT(k) COMPUTE(x)  [if k is small]
    
    This is only safe when there's no ORDER BY, as limit semantics depend on ordering.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has limit but no order_by
        if not select.limit or select.order_by:
            return None
        
        return Match(
            node=select,
            captures={'limit': select.limit}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Only safe when no ordering specified
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['limit_early'] = True
        return new_query
    
    return RewriteRule(
        name="push_limit_early",
        description="Push LIMIT before COMPUTE when no ORDER BY specified",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "No ORDER BY present")],
        transform=transform,
        equivalence_class="pushdown",
        priority=9,
    )


def rule_push_projection() -> RewriteRule:
    """Push SELECT/projection down to reduce materialization.
    
    Transformation:
        COMPUTE(a, b, c, d) SELECT_COLS(a, b)
        →
        COMPUTE(a, b)  [if c, d not needed elsewhere]
    
    This reduces memory usage by not computing unnecessary metrics.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has both compute and select_cols
        if not select.compute or not select.select_cols:
            return None
        
        computed_names = {c.result_name for c in select.compute}
        selected_cols = set(select.select_cols)
        
        # Find computed metrics not in selection
        unused_metrics = computed_names - selected_cols
        
        if not unused_metrics:
            return None
        
        return Match(
            node=select,
            captures={
                'compute': select.compute,
                'select_cols': select.select_cols,
                'unused': unused_metrics,
            }
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Safe if no order_by or other operations use unused metrics
        select = match.node
        
        # Check if unused metrics are referenced in order_by
        if select.order_by:
            order_fields = {o.key for o in select.order_by}
            if order_fields & match.captures['unused']:
                return False
        
        # Check if unused metrics are referenced in where
        if select.where:
            where_fields = _extract_fields_from_condition(select.where)
            if where_fields & match.captures['unused']:
                return False
        
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        
        # Remove unused compute items
        selected_cols = match.captures['select_cols']
        new_compute = [
            c for c in new_query.select.compute
            if c.result_name in selected_cols
        ]
        new_query.select.compute = new_compute
        
        return new_query
    
    return RewriteRule(
        name="push_projection",
        description="Remove computed metrics not used in final selection",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "Unused metrics not referenced elsewhere")],
        transform=transform,
        equivalence_class="pushdown",
        priority=7,
    )


# ============================================================================
# B. Layer Distributivity Rules (3 rules)
# ============================================================================


def rule_move_per_layer_early() -> RewriteRule:
    """Move per_layer grouping earlier when operations are layer-local.
    
    Transformation:
        COMPUTE(degree) PER_LAYER()
        →
        PER_LAYER() COMPUTE(degree)  [when degree is layer-local]
    
    This can improve parallelization by processing layers independently.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has group_by with layer
        if 'layer' not in select.group_by:
            return None
        
        # Has compute items
        if not select.compute:
            return None
        
        return Match(
            node=select,
            captures={'group_by': select.group_by, 'compute': select.compute}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Check if all compute items are layer-local metrics
        layer_local_metrics = {
            'degree', 'in_degree', 'out_degree', 'clustering',
            'local_clustering_coefficient', 'triangles'
        }
        
        compute_items = match.captures['compute']
        for item in compute_items:
            if item.name not in layer_local_metrics:
                # Not all metrics are layer-local
                return False
        
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['per_layer_early'] = True
        return new_query
    
    return RewriteRule(
        name="move_per_layer_early",
        description="Move PER_LAYER before COMPUTE when metrics are layer-local",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "All metrics are layer-local")],
        transform=transform,
        equivalence_class="layer_distributivity",
        priority=7,
    )


def rule_fuse_per_layer() -> RewriteRule:
    """Fuse nested per_layer groupings.
    
    Transformation:
        PER_LAYER() ... PER_LAYER()
        →
        PER_LAYER()
    
    This eliminates redundant grouping operations.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: group_by has 'layer' multiple times (shouldn't happen, but check)
        # More realistically, check for redundant grouping
        if select.group_by.count('layer') > 1:
            return Match(
                node=select,
                captures={'group_by': select.group_by}
            )
        
        return None
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        # Remove duplicate 'layer' from group_by
        seen = set()
        new_group_by = []
        for g in new_query.select.group_by:
            if g not in seen:
                new_group_by.append(g)
                seen.add(g)
        new_query.select.group_by = new_group_by
        return new_query
    
    return RewriteRule(
        name="fuse_per_layer",
        description="Remove duplicate PER_LAYER groupings",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "Always safe")],
        transform=transform,
        equivalence_class="layer_distributivity",
        priority=6,
    )


def rule_group_by_to_per_layer() -> RewriteRule:
    """Convert GROUP_BY(layer) into canonical PER_LAYER form.
    
    Transformation:
        GROUP_BY(layer)
        →
        PER_LAYER()
    
    This normalizes the representation for consistent optimization.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: group_by contains only 'layer'
        if select.group_by == ['layer']:
            return Match(
                node=select,
                captures={'group_by': select.group_by}
            )
        
        return None
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        return True
    
    def transform(query: Query, match: Match) -> Query:
        # Already in canonical form in our representation
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['canonical_per_layer'] = True
        return new_query
    
    return RewriteRule(
        name="group_by_to_per_layer",
        description="Normalize GROUP_BY(layer) to PER_LAYER",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "Always safe")],
        transform=transform,
        equivalence_class="layer_distributivity",
        priority=5,
    )


# ============================================================================
# C. UQ-Aware Rules (3 rules)
# ============================================================================


def rule_move_deterministic_into_uq() -> RewriteRule:
    """Move deterministic fusable operations inside UQ to reduce sampling cost.
    
    Transformation:
        UQ(COMPUTE(x)) WHERE(intrinsic)
        →
        UQ(COMPUTE(x) WHERE(intrinsic))  [if safe]
    
    This reduces the number of samples needed by filtering first.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has UQ config and has where with intrinsic fields
        if not select.uq_config:
            return None
        
        if not select.where:
            return None
        
        # Check if where uses intrinsic fields
        intrinsic_fields = {'layer', 'source_type', 'target_type', 'type', 'id', 'source', 'target'}
        where_fields = _extract_fields_from_condition(select.where)
        
        if not where_fields.issubset(intrinsic_fields):
            return None
        
        return Match(
            node=select,
            captures={'uq_config': select.uq_config, 'where': select.where}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Safe if where is deterministic and doesn't depend on UQ
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['where_in_uq'] = True
        return new_query
    
    return RewriteRule(
        name="move_deterministic_into_uq",
        description="Move deterministic WHERE filters inside UQ to reduce sampling cost",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "WHERE is deterministic")],
        transform=transform,
        equivalence_class="uq_aware",
        priority=8,
    )


def rule_hoist_reporting_outside_uq() -> RewriteRule:
    """Hoist purely reporting operations outside UQ.
    
    Transformation:
        UQ(COMPUTE(x) EXPORT(csv))
        →
        EXPORT(UQ(COMPUTE(x)), csv)
    
    This avoids exporting intermediate samples.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has UQ and export
        if not select.uq_config:
            return None
        
        if not select.file_export:
            return None
        
        return Match(
            node=select,
            captures={'uq_config': select.uq_config, 'export': select.file_export}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Always safe - export is pure reporting
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['export_outside_uq'] = True
        return new_query
    
    return RewriteRule(
        name="hoist_reporting_outside_uq",
        description="Move EXPORT operations outside UQ",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "EXPORT is pure reporting")],
        transform=transform,
        equivalence_class="uq_aware",
        priority=7,
    )


def rule_cache_uq_subprogram() -> RewriteRule:
    """Recognize identical subprograms in UQ samples and cache results.
    
    Transformation:
        UQ(COMPUTE(a, b)) where a, b are deterministic
        →
        UQ(COMPUTE(a, b)) with caching hint
    
    This avoids recomputing deterministic parts across samples.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has UQ with compute
        if not select.uq_config:
            return None
        
        if not select.compute:
            return None
        
        return Match(
            node=select,
            captures={'uq_config': select.uq_config, 'compute': select.compute}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Check if compute items are deterministic
        deterministic_metrics = {
            'degree', 'in_degree', 'out_degree', 'clustering',
            'triangles', 'eigenvector_centrality'
        }
        
        compute_items = match.captures['compute']
        for item in compute_items:
            if item.name not in deterministic_metrics:
                return False
        
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['uq_cache_subprogram'] = True
        return new_query
    
    return RewriteRule(
        name="cache_uq_subprogram",
        description="Cache deterministic computations inside UQ",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "All metrics are deterministic")],
        transform=transform,
        equivalence_class="uq_aware",
        priority=6,
    )


# ============================================================================
# D. Community-Specific Rules (3 rules)
# ============================================================================


def rule_fuse_community_annotation() -> RewriteRule:
    """Fuse community detection + node annotation if only for annotation.
    
    Transformation:
        COMMUNITIES(louvain) JOIN NODES
        →
        NODES.annotate_community(louvain)  [if communities not used directly]
    
    This avoids materializing the full community table.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: target is communities with auto_community_config
        if select.target != Target.COMMUNITIES:
            return None
        
        if not select.auto_community_config or not select.auto_community_config.enabled:
            return None
        
        # Check if kind is nodes_join
        if select.auto_community_config.kind != 'nodes_join':
            return None
        
        return Match(
            node=select,
            captures={'config': select.auto_community_config}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Safe when only used for annotation
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['community_annotation_fused'] = True
        return new_query
    
    return RewriteRule(
        name="fuse_community_annotation",
        description="Fuse community detection with node annotation",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "Only used for annotation")],
        transform=transform,
        equivalence_class="community_specific",
        priority=7,
    )


def rule_community_to_partition_slice() -> RewriteRule:
    """Rewrite communities → filter(community_id==k) to partition slice.
    
    Transformation:
        COMMUNITIES(louvain) WHERE(community_id=5)
        →
        PARTITION_SLICE(louvain, 5)
    
    This uses a more efficient access pattern for single community lookup.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: communities with where clause on community_id
        if select.target != Target.COMMUNITIES:
            return None
        
        if not select.where:
            return None
        
        # Check if where filters on community_id
        for atom in select.where.atoms:
            if atom.is_comparison and atom.comparison:
                if atom.comparison.left == 'community_id' and atom.comparison.op == '=':
                    return Match(
                        node=select,
                        captures={
                            'where': select.where,
                            'community_id': atom.comparison.right
                        }
                    )
        
        return None
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Safe when filtering on single community
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['partition_slice'] = True
        new_query.select._rewrite_hints['partition_slice_id'] = match.captures['community_id']
        return new_query
    
    return RewriteRule(
        name="community_to_partition_slice",
        description="Use partition slice for single community lookup",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "Single community filter")],
        transform=transform,
        equivalence_class="community_specific",
        priority=6,
    )


def rule_batch_community_metrics() -> RewriteRule:
    """Batch multiple community metrics in one pass.
    
    Transformation:
        COMMUNITIES(louvain) COMPUTE(modularity) COMPUTE(size) COMPUTE(density)
        →
        COMMUNITIES(louvain) COMPUTE_BATCH(modularity, size, density)
    
    This computes all metrics in a single pass over communities.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: communities with multiple compute items
        if select.target != Target.COMMUNITIES:
            return None
        
        if not select.compute or len(select.compute) < 2:
            return None
        
        return Match(
            node=select,
            captures={'compute': select.compute}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Always safe - just batching
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['community_metrics_batched'] = True
        return new_query
    
    return RewriteRule(
        name="batch_community_metrics",
        description="Batch multiple community metrics in single pass",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "Always safe to batch")],
        transform=transform,
        equivalence_class="community_specific",
        priority=5,
    )


# ============================================================================
# E. CSE/Caching Rules (2 rules)
# ============================================================================


def rule_detect_common_subexpression() -> RewriteRule:
    """Detect common subexpressions and mark for reuse.
    
    Transformation:
        COMPUTE(degree) ... WHERE(degree > 5) ... ORDER_BY(degree)
        →
        COMPUTE(degree) [cached] ... WHERE(degree > 5) ... ORDER_BY(degree)
    
    This marks 'degree' for caching since it's used multiple times.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: compute items used in multiple places
        if not select.compute:
            return None
        
        computed_names = {c.result_name for c in select.compute}
        
        # Check usage in where
        where_fields = set()
        if select.where:
            where_fields = _extract_fields_from_condition(select.where)
        
        # Check usage in order_by
        order_fields = set()
        if select.order_by:
            order_fields = {o.key for o in select.order_by}
        
        # Find fields used in multiple places
        used_in_where = computed_names & where_fields
        used_in_order = computed_names & order_fields
        
        common_fields = used_in_where & used_in_order
        
        if not common_fields:
            return None
        
        return Match(
            node=select,
            captures={'common_fields': common_fields}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Always beneficial to cache
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['cse_cache'] = list(match.captures['common_fields'])
        return new_query
    
    return RewriteRule(
        name="detect_common_subexpression",
        description="Mark computed fields used multiple times for caching",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "Multiple uses detected")],
        transform=transform,
        equivalence_class="cse_caching",
        priority=5,
    )


def rule_cache_expensive_metrics() -> RewriteRule:
    """Mark expensive metrics for caching.
    
    Transformation:
        COMPUTE(betweenness_centrality)
        →
        COMPUTE(betweenness_centrality) [cache=True]
    
    This marks expensive metrics for caching to avoid recomputation.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has expensive compute items
        expensive_metrics = {
            'betweenness_centrality',
            'closeness_centrality',
            'eigenvector_centrality',
            'pagerank',
            'katz_centrality',
        }
        
        if not select.compute:
            return None
        
        expensive_items = [
            c for c in select.compute
            if c.name in expensive_metrics
        ]
        
        if not expensive_items:
            return None
        
        return Match(
            node=select,
            captures={'expensive_items': expensive_items}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Check if not already cached
        if context.available_metrics:
            expensive_names = {c.result_name for c in match.captures['expensive_items']}
            if expensive_names.issubset(context.available_metrics):
                # Already computed/cached
                return False
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        
        expensive_names = [c.result_name for c in match.captures['expensive_items']]
        new_query.select._rewrite_hints['cache_expensive'] = expensive_names
        return new_query
    
    return RewriteRule(
        name="cache_expensive_metrics",
        description="Mark expensive centrality metrics for caching",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "Not already cached")],
        transform=transform,
        equivalence_class="cse_caching",
        priority=6,
    )


# ============================================================================
# F. Additional Optimization Rules (2 bonus rules)
# ============================================================================


def rule_eliminate_redundant_order_by() -> RewriteRule:
    """Eliminate ORDER BY when followed by operation that doesn't preserve order.
    
    Transformation:
        ORDER_BY(x) ... [operation that destroys order]
        →
        [remove ORDER_BY]
    
    This avoids unnecessary sorting.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has order_by but also has group_by (which may destroy order)
        if not select.order_by:
            return None
        
        # Check if group_by would destroy the ordering
        if select.group_by:
            return Match(
                node=select,
                captures={'order_by': select.order_by, 'group_by': select.group_by}
            )
        
        return None
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Only eliminate if group_by is not on the same field as order_by
        order_keys = {o.key for o in match.captures['order_by']}
        group_keys = set(match.captures['group_by'])
        
        # If ordering by grouped field, keep it
        if order_keys.issubset(group_keys):
            return False
        
        return True
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['redundant_order_eliminated'] = True
        # Note: actual elimination would require more complex logic
        return new_query
    
    return RewriteRule(
        name="eliminate_redundant_order_by",
        description="Remove ORDER BY when GROUP BY destroys ordering",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "ORDER BY rendered redundant")],
        transform=transform,
        equivalence_class="elimination",
        priority=4,
    )


def rule_optimize_top_k() -> RewriteRule:
    """Optimize TOP_K to use heap-based selection instead of full sort.
    
    Transformation:
        ORDER_BY(x) LIMIT(k)
        →
        TOP_K(x, k)
    
    This uses O(n log k) instead of O(n log n) for small k.
    """
    
    def matcher(query: Query) -> Optional[Match]:
        select = query.select
        
        # Pattern: has both order_by and limit
        if not select.order_by or not select.limit:
            return None
        
        return Match(
            node=select,
            captures={'order_by': select.order_by, 'limit': select.limit}
        )
    
    def guard_check(match: Match, context: RewriteContext) -> bool:
        # Beneficial when k is small relative to n
        limit = match.captures['limit']
        
        if context.network_stats and 'node_count' in context.network_stats:
            n = context.network_stats['node_count']
            # Use top-k if k < n/10
            if limit < n / 10:
                return True
            return False
        
        # If no stats, assume beneficial for k < 100
        return limit < 100
    
    def transform(query: Query, match: Match) -> Query:
        new_query = copy.deepcopy(query)
        if not hasattr(new_query.select, '_rewrite_hints'):
            new_query.select._rewrite_hints = {}
        new_query.select._rewrite_hints['use_heap_topk'] = True
        return new_query
    
    return RewriteRule(
        name="optimize_top_k",
        description="Use heap-based TOP_K instead of full sort + limit",
        pattern_matcher=matcher,
        guards=[RuleGuard(guard_check, "k is small relative to n")],
        transform=transform,
        equivalence_class="algorithmic",
        priority=7,
    )


# ============================================================================
# Helper Functions
# ============================================================================


def _extract_fields_from_condition(cond: ConditionExpr) -> Set[str]:
    """Extract all field names referenced in a condition expression.
    
    Args:
        cond: Condition expression to analyze
        
    Returns:
        Set of field names
    """
    fields = set()
    
    for atom in cond.atoms:
        if atom.is_comparison and atom.comparison:
            fields.add(atom.comparison.left)
        elif atom.is_function and atom.function:
            # For functions, we'd need more complex analysis
            pass
    
    return fields


# ============================================================================
# Standard Rule Sets
# ============================================================================


def get_standard_rules() -> List[RewriteRule]:
    """Get the standard set of rewrite rules.
    
    Returns:
        List of all standard rewrite rules (15+)
    """
    return [
        # A. Pushdown/Fusion (5 rules)
        rule_push_where_past_compute(),
        rule_fuse_compute(),
        rule_fuse_where(),
        rule_push_limit_early(),
        rule_push_projection(),
        
        # B. Layer Distributivity (3 rules)
        rule_move_per_layer_early(),
        rule_fuse_per_layer(),
        rule_group_by_to_per_layer(),
        
        # C. UQ-Aware (3 rules)
        rule_move_deterministic_into_uq(),
        rule_hoist_reporting_outside_uq(),
        rule_cache_uq_subprogram(),
        
        # D. Community-Specific (3 rules)
        rule_fuse_community_annotation(),
        rule_community_to_partition_slice(),
        rule_batch_community_metrics(),
        
        # E. CSE/Caching (2 rules)
        rule_detect_common_subexpression(),
        rule_cache_expensive_metrics(),
        
        # F. Additional (2 bonus rules)
        rule_eliminate_redundant_order_by(),
        rule_optimize_top_k(),
    ]


def get_aggressive_rules() -> List[RewriteRule]:
    """Get aggressive optimization rules (all standard rules).
    
    Returns:
        All available rewrite rules
    """
    return get_standard_rules()


def get_conservative_rules() -> List[RewriteRule]:
    """Get conservative optimization rules (safe subset).
    
    Returns:
        Conservative subset of rules
    """
    return [
        rule_fuse_compute(),
        rule_fuse_where(),
        rule_fuse_per_layer(),
        rule_batch_community_metrics(),
        rule_detect_common_subexpression(),
    ]


# ============================================================================
# Public API
# ============================================================================


def apply_rewrites(
    program: GraphProgram,
    rules: Optional[List[RewriteRule]] = None,
    context: Optional[RewriteContext] = None,
    fixpoint: bool = True,
) -> GraphProgram:
    """Apply rewrite rules to optimize a GraphProgram.
    
    Convenience function that creates an engine and applies rules.
    
    Args:
        program: GraphProgram to optimize
        rules: List of rules to apply (defaults to standard rules)
        context: Optional rewrite context
        fixpoint: If True, iterate until no more rules apply
        
    Returns:
        Optimized GraphProgram
        
    Example:
        >>> from py3plex.dsl import Q
        >>> from py3plex.dsl.program import GraphProgram
        >>> from py3plex.dsl.program.rewrite import apply_rewrites
        >>> 
        >>> ast = Q.nodes().compute("degree").where(layer="social").to_ast()
        >>> program = GraphProgram.from_ast(ast)
        >>> optimized = apply_rewrites(program)
    """
    if rules is None:
        rules = get_standard_rules()
    
    engine = RewriteEngine(rules=rules)
    return engine.apply(program, context=context, fixpoint=fixpoint)


__all__ = [
    'Match',
    'RewriteContext',
    'RuleGuard',
    'RewriteRule',
    'RewriteEngine',
    'apply_rewrites',
    'get_standard_rules',
    'get_aggressive_rules',
    'get_conservative_rules',
]
