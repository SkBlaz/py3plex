"""Claim language parser for counterexample generation.

This module parses claim strings in the MVP format:
    degree__ge(k) -> pagerank__rank_gt(r)

And compiles them into callable predicates for antecedent and consequent checks.
"""

import hashlib
import re
from typing import Any, Callable, Dict, Optional, Tuple

from py3plex.exceptions import ParsingError


class ClaimParseError(ParsingError):
    """Exception raised when claim parsing fails.

    Error code: PX105
    """

    default_code = "PX105"


# Supported comparison operators
COMPARATORS = {
    "gt": ">",
    "ge": ">=",
    "gte": ">=",
    "lt": "<",
    "le": "<=",
    "lte": "<=",
    "eq": "==",
    "ne": "!=",
}


def parse_claim(
    claim_str: str, params: Optional[Dict[str, Any]] = None
) -> Tuple[str, Callable, Callable]:
    """Parse a claim string into antecedent and consequent predicates.

    MVP format: metric1__comparator(param) -> metric2__comparator(param)
    Example: degree__ge(k) -> pagerank__rank_gt(r)

    Args:
        claim_str: Claim string in MVP format
        params: Parameter bindings (e.g., {"k": 10, "r": 50})

    Returns:
        Tuple of (normalized_claim, antecedent_fn, consequent_fn)

    Raises:
        ClaimParseError: If claim string is malformed
    """
    if params is None:
        params = {}

    # Split on ->
    if "->" not in claim_str:
        raise ClaimParseError(
            f"Claim must contain '->': {claim_str}",
            suggestions=["Use format: antecedent -> consequent"],
        )

    parts = claim_str.split("->")
    if len(parts) != 2:
        raise ClaimParseError(
            f"Claim must have exactly one '->': {claim_str}",
            suggestions=["Use format: antecedent -> consequent"],
        )

    antecedent_str = parts[0].strip()
    consequent_str = parts[1].strip()

    # Parse antecedent and consequent
    try:
        antecedent_fn = _parse_predicate(antecedent_str, params, is_antecedent=True)
        consequent_fn = _parse_predicate(consequent_str, params, is_antecedent=False)
    except Exception as e:
        raise ClaimParseError(
            f"Failed to parse claim: {str(e)}",
            context={"claim": claim_str},
        )

    # Normalize claim string
    normalized = f"{antecedent_str} -> {consequent_str}"

    return normalized, antecedent_fn, consequent_fn


def _parse_predicate(
    pred_str: str, params: Dict[str, Any], is_antecedent: bool
) -> Callable:
    """Parse a single predicate (antecedent or consequent).

    Formats:
        - degree__ge(k) - value comparison on cheap metric
        - pagerank__gt(x) - value comparison on computed metric
        - pagerank__rank_gt(r) - rank comparison on computed metric

    Args:
        pred_str: Predicate string
        params: Parameter bindings
        is_antecedent: Whether this is the antecedent (affects metric availability)

    Returns:
        Callable that checks the predicate

    Raises:
        ClaimParseError: If predicate is malformed
    """
    # Match pattern: metric__comparator(param) or metric__rank_comparator(param)
    pattern = r"(\w+)__(rank_)?(\w+)\((\w+)\)"
    match = re.match(pattern, pred_str)

    if not match:
        raise ClaimParseError(
            f"Invalid predicate format: {pred_str}",
            suggestions=[
                "Use format: metric__comparator(param) or metric__rank_comparator(param)"
            ],
        )

    metric = match.group(1)
    is_rank = match.group(2) is not None
    comparator_key = match.group(3)
    param_name = match.group(4)

    # Get parameter value
    if param_name not in params:
        raise ClaimParseError(
            f"Parameter '{param_name}' not provided",
            context={"predicate": pred_str, "available_params": list(params.keys())},
        )

    param_value = params[param_name]

    # Get comparison operator
    if comparator_key not in COMPARATORS:
        raise ClaimParseError(
            f"Unknown comparator: {comparator_key}",
            suggestions=[f"Available: {', '.join(COMPARATORS.keys())}"],
        )

    op_str = COMPARATORS[comparator_key]

    # Build predicate function
    if is_antecedent:
        # Antecedent: simple value check
        def antecedent_pred(node_data: Dict[str, Any]) -> bool:
            if metric not in node_data:
                return False
            value = node_data[metric]
            return _compare(value, op_str, param_value)

        return antecedent_pred
    else:
        # Consequent: value or rank check
        if is_rank:
            # Rank-based check: metric__rank_gt(r)
            def consequent_rank_pred(
                node_data: Dict[str, Any], metrics: Dict[str, Any]
            ) -> bool:
                if metric not in node_data:
                    return False
                # Expect metrics to contain rank information
                rank_key = f"{metric}_rank"
                if rank_key not in node_data:
                    return False
                rank = node_data[rank_key]
                return _compare(rank, op_str, param_value)

            return consequent_rank_pred
        else:
            # Value-based check: metric__gt(x)
            def consequent_value_pred(
                node_data: Dict[str, Any], metrics: Dict[str, Any]
            ) -> bool:
                if metric not in node_data:
                    return False
                value = node_data[metric]
                return _compare(value, op_str, param_value)

            return consequent_value_pred


def _compare(left: Any, op: str, right: Any) -> bool:
    """Compare two values using the given operator.

    Args:
        left: Left-hand side value
        op: Comparison operator (">", ">=", "<", "<=", "==", "!=")
        right: Right-hand side value

    Returns:
        Result of comparison
    """
    if op == ">":
        return left > right
    elif op == ">=":
        return left >= right
    elif op == "<":
        return left < right
    elif op == "<=":
        return left <= right
    elif op == "==":
        return left == right
    elif op == "!=":
        return left != right
    else:
        raise ValueError(f"Unknown operator: {op}")


def compute_claim_hash(normalized_claim: str, params: Dict[str, Any]) -> str:
    """Compute stable hash of claim + parameters.

    Args:
        normalized_claim: Normalized claim string
        params: Parameter bindings

    Returns:
        SHA256 hex digest
    """
    # Sort params for stable hash
    sorted_params = sorted(params.items())
    hash_input = f"{normalized_claim}|{sorted_params}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def parse_and_compile_claim(claim_str: str, params: Dict[str, Any]) -> "Claim":
    """Parse claim string and return Claim object.

    Args:
        claim_str: Claim string in MVP format
        params: Parameter bindings

    Returns:
        Claim object with compiled predicates

    Raises:
        ClaimParseError: If parsing fails
    """
    from .types import Claim

    normalized, antecedent_fn, consequent_fn = parse_claim(claim_str, params)
    claim_hash = compute_claim_hash(normalized, params)

    return Claim(
        claim_str=normalized,
        claim_hash=claim_hash,
        antecedent=antecedent_fn,
        consequent=consequent_fn,
        params=params,
        description=normalized,
    )
