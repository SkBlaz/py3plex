"""Diagnostic builders for common error patterns.

This module provides convenience functions for creating Diagnostic objects
for common error scenarios throughout py3plex.
"""

from typing import List, Optional, Any, Dict
from .core import (
    Diagnostic,
    DiagnosticSeverity,
    DiagnosticContext,
    FixSuggestion,
)
from .codes import ERROR_CODES
from .utils import did_you_mean, fuzzy_match


def unknown_field_error(
    field: str,
    known_fields: List[str],
    target_type: str = "node",
    builder_method: Optional[str] = None,
    query_fragment: Optional[str] = None,
) -> Diagnostic:
    """Create diagnostic for unknown field.
    
    Args:
        field: Unknown field name
        known_fields: List of valid field names
        target_type: Target type (node, edge, etc.)
        builder_method: Builder method where error occurred
        query_fragment: Query fragment with the error
    
    Returns:
        Diagnostic with DSL_SEM_001 code
    """
    suggestion = did_you_mean(field, known_fields)
    
    fixes = []
    if suggestion:
        fixes.append(FixSuggestion(
            description=f"Did you mean '{suggestion}'?",
            replacement=suggestion,
            example=f"Q.{target_type}s().where({suggestion}__gt=3)"
        ))
    
    # Add suggestion to compute the field
    fixes.append(FixSuggestion(
        description=f"Compute the field before using it",
        replacement=f".compute('{field}')",
        example=f"Q.{target_type}s().compute('{field}').where({field}__gt=3)"
    ))
    
    context = DiagnosticContext(
        builder_method=builder_method,
        query_fragment=query_fragment,
        additional={"target_type": target_type}
    )
    
    error_code = ERROR_CODES["DSL_SEM_001"]
    
    return Diagnostic(
        severity=DiagnosticSeverity.ERROR,
        code=error_code.code,
        message=f"Unknown field '{field}' for {target_type} target",
        context=context,
        cause=error_code.typical_cause,
        fixes=fixes,
        related=[
            f"Q.{target_type}s().compute()",
            "Available fields: " + ", ".join(sorted(known_fields)[:10]),
        ]
    )


def unknown_measure_error(
    measure: str,
    known_measures: List[str],
    builder_method: Optional[str] = "compute",
) -> Diagnostic:
    """Create diagnostic for unknown measure.
    
    Args:
        measure: Unknown measure name
        known_measures: List of valid measure names
        builder_method: Builder method where error occurred
    
    Returns:
        Diagnostic with DSL_SEM_001 code
    """
    suggestion = did_you_mean(measure, known_measures)
    
    fixes = []
    if suggestion:
        fixes.append(FixSuggestion(
            description=f"Did you mean '{suggestion}'?",
            replacement=suggestion,
            example=f".compute('{suggestion}')"
        ))
    
    context = DiagnosticContext(
        builder_method=builder_method,
        query_fragment=f".compute('{measure}')"
    )
    
    return Diagnostic(
        severity=DiagnosticSeverity.ERROR,
        code="DSL_SEM_001",
        message=f"Unknown measure '{measure}'",
        context=context,
        cause="The measure name is not recognized or contains a typo",
        fixes=fixes,
        related=[
            "Q.nodes().compute()",
            "Available measures: " + ", ".join(sorted(known_measures)[:10]),
        ]
    )


def unknown_layer_error(
    layer: str,
    known_layers: List[str],
    builder_method: Optional[str] = "from_layers",
) -> Diagnostic:
    """Create diagnostic for unknown layer.
    
    Args:
        layer: Unknown layer name
        known_layers: List of valid layer names
        builder_method: Builder method where error occurred
    
    Returns:
        Diagnostic with DSL_SEM_005 code
    """
    suggestion = did_you_mean(layer, known_layers)
    
    fixes = []
    if suggestion:
        fixes.append(FixSuggestion(
            description=f"Did you mean '{suggestion}'?",
            replacement=suggestion,
            example=f"L['{suggestion}']"
        ))
    
    # Add suggestion to use all layers
    if "*" not in known_layers:
        fixes.append(FixSuggestion(
            description="Use all layers",
            replacement="L['*']",
            example="Q.nodes().from_layers(L['*'])"
        ))
    
    context = DiagnosticContext(
        builder_method=builder_method,
        query_fragment=f"L['{layer}']"
    )
    
    error_code = ERROR_CODES["DSL_SEM_005"]
    
    return Diagnostic(
        severity=DiagnosticSeverity.ERROR,
        code=error_code.code,
        message=f"Unknown layer '{layer}'",
        context=context,
        cause=error_code.typical_cause,
        fixes=fixes,
        related=[
            "network.list_layers()",
            "Available layers: " + ", ".join(sorted(known_layers)),
        ]
    )


def empty_result_warning(
    filter_condition: Optional[str] = None,
    num_nodes: int = 0,
) -> Diagnostic:
    """Create diagnostic for empty result after filtering.
    
    Args:
        filter_condition: Filter condition that produced empty result
        num_nodes: Number of nodes before filtering
    
    Returns:
        Diagnostic with RES_001 code
    """
    fixes = []
    
    if filter_condition:
        fixes.append(FixSuggestion(
            description="Relax the filter condition",
            example="Try using a less restrictive threshold"
        ))
    
    fixes.append(FixSuggestion(
        description="Check data distribution",
        example="result.to_pandas().describe()"
    ))
    
    context = DiagnosticContext(
        query_fragment=filter_condition
    )
    
    error_code = ERROR_CODES["RES_001"]
    
    return Diagnostic(
        severity=DiagnosticSeverity.WARNING,
        code=error_code.code,
        message=f"Query produced no results (started with {num_nodes} nodes)",
        context=context,
        cause=error_code.typical_cause,
        fixes=fixes,
        related=[]
    )


def high_variance_warning(
    measure: str,
    variance: float,
    n_samples: int,
) -> Diagnostic:
    """Create diagnostic for high variance in UQ results.
    
    Args:
        measure: Measure name with high variance
        variance: Variance value
        n_samples: Number of samples used
    
    Returns:
        Diagnostic with RES_002 code
    """
    fixes = [
        FixSuggestion(
            description="Increase number of samples",
            replacement=f"n_samples={n_samples * 2}",
            example=f".uq(method='bootstrap', n_samples={n_samples * 2})"
        ),
        FixSuggestion(
            description="Try different resampling strategy",
            example=".uq(method='perturbation', n_samples=100)"
        ),
    ]
    
    error_code = ERROR_CODES["RES_002"]
    
    return Diagnostic(
        severity=DiagnosticSeverity.WARNING,
        code=error_code.code,
        message=f"High variance detected for measure '{measure}' (variance={variance:.3f})",
        context=None,
        cause=error_code.typical_cause,
        fixes=fixes,
        related=["Q.nodes().uq()"]
    )


def unknown_algorithm_error(
    algorithm: str,
    known_algorithms: List[str],
    operation: str = "operation",
) -> Diagnostic:
    """Create diagnostic for unknown algorithm.
    
    Args:
        algorithm: Unknown algorithm name
        known_algorithms: List of valid algorithm names
        operation: Operation description (e.g., "community detection")
    
    Returns:
        Diagnostic with ALG_001 code
    """
    suggestion = did_you_mean(algorithm, known_algorithms)
    
    fixes = []
    if suggestion:
        fixes.append(FixSuggestion(
            description=f"Did you mean '{suggestion}'?",
            replacement=suggestion,
        ))
    
    error_code = ERROR_CODES["ALG_001"]
    
    return Diagnostic(
        severity=DiagnosticSeverity.ERROR,
        code=error_code.code,
        message=f"Unknown algorithm '{algorithm}' for {operation}",
        context=None,
        cause=error_code.typical_cause,
        fixes=fixes,
        related=[
            "Available algorithms: " + ", ".join(sorted(known_algorithms)[:10]),
        ]
    )


def randomness_without_seed_warning(
    operation: str,
) -> Diagnostic:
    """Create diagnostic for randomness without seed.
    
    Args:
        operation: Operation that uses randomness
    
    Returns:
        Diagnostic with EXEC_004 code
    """
    fixes = [
        FixSuggestion(
            description="Add a seed for reproducibility",
            replacement="seed=42",
            example=f"{operation}(..., seed=42)"
        ),
    ]
    
    error_code = ERROR_CODES["EXEC_004"]
    
    return Diagnostic(
        severity=DiagnosticSeverity.WARNING,
        code=error_code.code,
        message=f"Stochastic operation '{operation}' used without seed",
        context=None,
        cause=error_code.typical_cause,
        fixes=fixes,
        related=[]
    )
