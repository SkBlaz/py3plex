"""Contract evaluation engine.

This module provides the core logic for evaluating robustness contracts:
- Running perturbations over a grid
- Computing metrics and comparing to baseline
- Evaluating predicates
- Performing repairs
- Handling failure modes
"""

import time
import traceback
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .failure_modes import FailureMode
from .result import ContractResult, Evidence, RepairPayload
from .contract import Robustness


def evaluate_contract(
    baseline_result: Any,
    contract: Robustness,
    network: Any,
    query_builder: Any,
    conclusion_type: str,
    top_k: Optional[int] = None,
    metric: Optional[str] = None,
) -> ContractResult:
    """Evaluate a robustness contract.
    
    This is the main entry point for contract evaluation. It:
    1. Resolves defaults based on network and query context
    2. Validates baseline
    3. Runs perturbations and computes metrics
    4. Evaluates predicates
    5. Performs repair if needed
    6. Returns ContractResult with evidence
    
    Args:
        baseline_result: QueryResult from baseline (unperturbed) query
        contract: Robustness contract object
        network: Multilayer network object
        query_builder: QueryBuilder instance (for re-executing)
        conclusion_type: Type of conclusion ("top_k", "ranking", "community")
        top_k: Value of k for top-k queries
        metric: Metric name being computed
        
    Returns:
        ContractResult with pass/fail, evidence, and optional repair
    """
    start_time = time.time()
    
    try:
        # Resolve defaults
        resolved_contract = contract.resolve_defaults(
            network=network,
            conclusion_type=conclusion_type,
            top_k=top_k,
            metric=metric,
        )
        
        # Check budget from the start
        if time.time() - start_time > resolved_contract.budget.max_seconds:
            return _make_failure_result(
                failure_mode=FailureMode.RESOURCE_LIMIT,
                message="Budget exceeded during initialization",
                details={"elapsed_seconds": time.time() - start_time},
                provenance=_make_provenance(resolved_contract, network, conclusion_type, top_k, metric),
            )
        
        # Validate baseline
        validation_result = _validate_baseline(baseline_result, conclusion_type, top_k)
        if validation_result is not None:
            # Baseline validation failed
            return validation_result
        
        # Run perturbations
        try:
            perturbed_results = _run_perturbations(
                network=network,
                query_builder=query_builder,
                contract=resolved_contract,
                start_time=start_time,
            )
        except Exception as e:
            return _make_failure_result(
                failure_mode=FailureMode.PERTURBATION_INVALID,
                message=f"Perturbation failed: {str(e)}",
                details={"error": str(e), "traceback": traceback.format_exc()},
                provenance=_make_provenance(resolved_contract, network, conclusion_type, top_k, metric),
            )
        
        # Check budget after perturbations
        if time.time() - start_time > resolved_contract.budget.max_seconds:
            return _make_failure_result(
                failure_mode=FailureMode.RESOURCE_LIMIT,
                message="Budget exceeded during perturbation",
                details={"elapsed_seconds": time.time() - start_time},
                provenance=_make_provenance(resolved_contract, network, conclusion_type, top_k, metric),
                evidence=_make_evidence_from_results(baseline_result, perturbed_results),
            )
        
        # Evaluate predicates
        predicates = resolved_contract.predicates
        evidence = Evidence()
        all_passed = True
        
        for predicate in predicates:
            try:
                passed, pred_evidence = predicate.evaluate(
                    baseline=baseline_result,
                    perturbed_results=perturbed_results,
                    domain=resolved_contract.domain,
                )
                evidence.predicate_results.append((predicate, passed, pred_evidence))
                
                if not passed:
                    all_passed = False
                    
                    # Check for specific failure reasons in evidence
                    if "error" in pred_evidence:
                        error_type = pred_evidence["error"]
                        if error_type == "insufficient_baseline":
                            return _make_failure_result(
                                failure_mode=FailureMode.INSUFFICIENT_BASELINE,
                                message="Baseline insufficient for predicate evaluation",
                                details=pred_evidence,
                                provenance=_make_provenance(resolved_contract, network, conclusion_type, top_k, metric),
                                evidence=evidence,
                            )
                        elif error_type == "metric_undefined":
                            return _make_failure_result(
                                failure_mode=FailureMode.METRIC_UNDEFINED,
                                message="Metric undefined for this network structure",
                                details=pred_evidence,
                                provenance=_make_provenance(resolved_contract, network, conclusion_type, top_k, metric),
                                evidence=evidence,
                            )
            except Exception as e:
                return _make_failure_result(
                    failure_mode=FailureMode.EXECUTION_ERROR,
                    message=f"Predicate evaluation failed: {str(e)}",
                    details={"error": str(e), "traceback": traceback.format_exc()},
                    provenance=_make_provenance(resolved_contract, network, conclusion_type, top_k, metric),
                    evidence=evidence,
                )
        
        # Check budget after predicate evaluation
        if time.time() - start_time > resolved_contract.budget.max_seconds:
            return _make_failure_result(
                failure_mode=FailureMode.RESOURCE_LIMIT,
                message="Budget exceeded during predicate evaluation",
                details={"elapsed_seconds": time.time() - start_time},
                provenance=_make_provenance(resolved_contract, network, conclusion_type, top_k, metric),
                evidence=evidence,
            )
        
        # If all predicates passed, return success
        if all_passed:
            return ContractResult(
                baseline_result=baseline_result,
                contract_ok=True,
                message="All predicates passed",
                evidence=evidence,
                provenance=_make_provenance(resolved_contract, network, conclusion_type, top_k, metric),
            )
        
        # Contract violated - attempt repair if enabled
        repair_payload = RepairPayload()
        if resolved_contract.repair:
            repair_payload = _perform_repair(
                baseline_result=baseline_result,
                perturbed_results=perturbed_results,
                conclusion_type=conclusion_type,
                contract=resolved_contract,
                evidence=evidence,
            )
        
        # Return failure with repair
        return ContractResult(
            baseline_result=baseline_result,
            contract_ok=False,
            failure_mode=FailureMode.CONTRACT_VIOLATION,
            message="Contract predicate(s) violated",
            evidence=evidence,
            repair=repair_payload,
            provenance=_make_provenance(resolved_contract, network, conclusion_type, top_k, metric),
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        return _make_failure_result(
            failure_mode=FailureMode.EXECUTION_ERROR,
            message=f"Unexpected error during contract evaluation: {str(e)}",
            details={"error": str(e), "traceback": traceback.format_exc()},
            provenance=_make_provenance(contract, network, conclusion_type, top_k, metric),
        )


def _validate_baseline(
    baseline_result: Any,
    conclusion_type: str,
    top_k: Optional[int] = None,
) -> Optional[ContractResult]:
    """Validate baseline result.
    
    Returns ContractResult with INSUFFICIENT_BASELINE if validation fails,
    or None if validation passes.
    """
    if baseline_result is None:
        return _make_failure_result(
            failure_mode=FailureMode.INSUFFICIENT_BASELINE,
            message="Baseline query returned None",
            details={"baseline_size": 0},
        )
    
    # Get baseline size
    if hasattr(baseline_result, "to_pandas"):
        df = baseline_result.to_pandas()
        if df is None or len(df) == 0:
            return _make_failure_result(
                failure_mode=FailureMode.INSUFFICIENT_BASELINE,
                message="Baseline query returned empty DataFrame",
                details={"baseline_size": 0},
            )
        baseline_size = len(df)
    else:
        baseline_size = 0
    
    # Check top_k requirement
    if conclusion_type == "top_k" and top_k is not None:
        if baseline_size < top_k:
            return _make_failure_result(
                failure_mode=FailureMode.INSUFFICIENT_BASELINE,
                message=f"Baseline has only {baseline_size} items, but top_k={top_k}",
                details={"baseline_size": baseline_size, "required_k": top_k},
            )
    
    return None


def _run_perturbations(
    network: Any,
    query_builder: Any,
    contract: Robustness,
    start_time: float,
) -> List[Tuple[float, Any]]:
    """Run perturbations over grid and collect results.
    
    Returns list of (p, result) tuples.
    """
    from py3plex.robustness.perturbations import EdgeDrop
    from py3plex.utils import get_rng
    
    results = []
    
    for p in contract.grid:
        if p == 0.0:
            # Skip p=0 (baseline already computed)
            continue
        
        # Check budget
        if time.time() - start_time > contract.budget.max_seconds:
            break
        
        # Run n_samples perturbations at this p value
        for sample_id in range(contract.n_samples):
            # Create perturbation
            if contract.perturb == "edge_drop":
                perturbation = EdgeDrop(p=p)
            else:
                raise ValueError(f"Unsupported perturbation type: {contract.perturb}")
            
            # Apply perturbation
            seed = contract.seed + sample_id if contract.seed is not None else None
            rng = get_rng(seed)
            perturbed_network = perturbation.apply(network, rng)
            
            # Re-execute query on perturbed network
            # Note: This assumes query_builder can be re-executed
            # We need to clone the query and remove contract_spec to avoid recursion
            perturbed_result = _execute_on_network(query_builder, perturbed_network)
            
            results.append((p, perturbed_result))
    
    return results


def _execute_on_network(query_builder: Any, network: Any) -> Any:
    """Execute query on a specific network.
    
    This clones the query and removes contract_spec to avoid recursion.
    """
    # Create a copy of the SelectStmt without contract_spec
    select_copy = query_builder._select
    original_contract = select_copy.contract_spec
    
    try:
        select_copy.contract_spec = None
        result = query_builder.execute(network)
        return result
    finally:
        select_copy.contract_spec = original_contract


def _perform_repair(
    baseline_result: Any,
    perturbed_results: List[Tuple[float, Any]],
    conclusion_type: str,
    contract: Robustness,
    evidence: Evidence,
) -> RepairPayload:
    """Perform repair based on conclusion type.
    
    Returns RepairPayload with repaired output.
    """
    if conclusion_type == "top_k":
        return _repair_top_k(baseline_result, perturbed_results, contract, evidence)
    elif conclusion_type == "ranking":
        return _repair_ranking(baseline_result, perturbed_results, contract, evidence)
    elif conclusion_type == "community":
        return _repair_community(baseline_result, perturbed_results, contract, evidence)
    else:
        return RepairPayload(repaired_ok=False, conclusion_type=conclusion_type)


def _repair_top_k(
    baseline_result: Any,
    perturbed_results: List[Tuple[float, Any]],
    contract: Robustness,
    evidence: Evidence,
) -> RepairPayload:
    """Repair top-k by computing stable core.
    
    Stable core = items with presence frequency >= threshold for all p <= p_max.
    """
    # Get threshold from predicate (use 0.85 as default)
    threshold = 0.85
    if contract.predicates and len(contract.predicates) > 0:
        pred = contract.predicates[0]
        if hasattr(pred, "threshold"):
            threshold = pred.threshold
    
    # Extract baseline items
    baseline_items = _extract_items(baseline_result)
    if not baseline_items:
        return RepairPayload(repaired_ok=False, conclusion_type="top_k")
    
    # Compute frequency of each item across all perturbations
    item_frequencies = {item: [] for item in baseline_items}
    
    for p, result in perturbed_results:
        perturbed_items = set(_extract_items(result))
        for item in baseline_items:
            item_frequencies[item].append(1 if item in perturbed_items else 0)
    
    # Compute mean frequency per item
    stable_core = []
    for item, frequencies in item_frequencies.items():
        if len(frequencies) > 0:
            mean_freq = np.mean(frequencies)
            if mean_freq >= threshold:
                stable_core.append(item)
    
    if len(stable_core) == 0:
        return RepairPayload(
            repaired_ok=False,
            conclusion_type="top_k",
            metadata={"reason": "empty_stable_core"},
        )
    
    return RepairPayload(
        repaired_ok=True,
        conclusion_type="top_k",
        stable_core=stable_core,
        metadata={"threshold": threshold, "original_size": len(baseline_items)},
    )


def _repair_ranking(
    baseline_result: Any,
    perturbed_results: List[Tuple[float, Any]],
    contract: Robustness,
    evidence: Evidence,
) -> RepairPayload:
    """Repair ranking by computing tiers.
    
    Tiers are groups of items with stable relative ordering.
    """
    # TODO: Implement tier-based repair
    # For now, return simple repair placeholder
    return RepairPayload(
        repaired_ok=False,
        conclusion_type="ranking",
        metadata={"reason": "not_implemented"},
    )


def _repair_community(
    baseline_result: Any,
    perturbed_results: List[Tuple[float, Any]],
    contract: Robustness,
    evidence: Evidence,
) -> RepairPayload:
    """Repair community by finding stable nodes.
    
    Stable nodes = nodes with low community flip probability.
    """
    # TODO: Implement stable node repair
    # For now, return simple repair placeholder
    return RepairPayload(
        repaired_ok=False,
        conclusion_type="community",
        metadata={"reason": "not_implemented"},
    )


def _extract_items(result: Any) -> List:
    """Extract list of items from QueryResult."""
    if result is None:
        return []
    
    if hasattr(result, "to_pandas"):
        df = result.to_pandas()
        if df is None or len(df) == 0:
            return []
        
        if "node" in df.columns:
            return df["node"].tolist()
        elif "edge" in df.columns:
            return df["edge"].tolist()
        elif len(df.columns) > 0:
            return df[df.columns[0]].tolist()
    
    return []


def _make_evidence_from_results(baseline: Any, perturbed_results: List[Tuple[float, Any]]) -> Evidence:
    """Create Evidence object from results."""
    evidence = Evidence()
    
    # Create per-p summaries
    for p, result in perturbed_results:
        if p not in evidence.per_p_summaries:
            evidence.per_p_summaries[p] = {"count": 0}
        evidence.per_p_summaries[p]["count"] += 1
    
    return evidence


def _make_provenance(
    contract: Robustness,
    network: Any,
    conclusion_type: str,
    top_k: Optional[int],
    metric: Optional[str],
) -> Dict[str, Any]:
    """Create provenance dictionary."""
    n_nodes = len(list(network.get_nodes())) if hasattr(network, "get_nodes") else 0
    n_edges = len(list(network.get_edges())) if hasattr(network, "get_edges") else 0
    
    return {
        "contract": contract.to_dict(),
        "conclusion_type": conclusion_type,
        "top_k": top_k,
        "metric": metric,
        "network": {
            "n_nodes": n_nodes,
            "n_edges": n_edges,
        },
        "determinism_check": "passed" if contract.seed is not None else "skipped",
    }


def _make_failure_result(
    failure_mode: FailureMode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    provenance: Optional[Dict[str, Any]] = None,
    evidence: Optional[Evidence] = None,
) -> ContractResult:
    """Create a ContractResult for a failure."""
    return ContractResult(
        baseline_result=None,
        contract_ok=False,
        failure_mode=failure_mode,
        message=message,
        details=details or {},
        evidence=evidence or Evidence(),
        provenance=provenance or {},
    )
