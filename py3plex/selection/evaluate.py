"""Contestant evaluation for AutoCommunity."""

import hashlib
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from .result import ContestantResult
from .community_registry import CandidateSpec
from .metric_registry import MetricRegistry, MetricSpec

logger = logging.getLogger(__name__)


def evaluate_contestant(
    network: Any,
    candidate: CandidateSpec,
    metrics: List[MetricSpec],
    master_seed: int = 0,
    uq: bool = False,
    uq_config: Optional[Dict[str, Any]] = None,
    time_budget_s: Optional[float] = None,
) -> ContestantResult:
    """Evaluate a single contestant (algorithm + params).
    
    Args:
        network: Multilayer network
        candidate: CandidateSpec for this contestant
        metrics: List of MetricSpec to compute
        master_seed: Master random seed
        uq: Whether to use UQ
        uq_config: UQ configuration (if uq=True)
        time_budget_s: Time budget in seconds (optional)
    
    Returns:
        ContestantResult with partition and computed metrics
    """
    # Derive deterministic seed for this contestant
    contestant_seed = _derive_contestant_seed(master_seed, candidate.contestant_id)
    
    # Prepare algorithm parameters
    algo_params = candidate.params.copy()
    
    # Add seed parameter if algorithm supports it
    if candidate.seed_param_name:
        algo_params[candidate.seed_param_name] = contestant_seed
    else:
        logger.debug(f"Algorithm {candidate.name} does not support seeding")
    
    # Add network parameter
    algo_params["network"] = network
    
    # Run algorithm
    start_time = time.time()
    
    try:
        if uq:
            partition, uq_result = _run_algorithm_with_uq(
                candidate=candidate,
                algo_params=algo_params,
                uq_config=uq_config or {},
            )
            uq_meta = {"uq_result": uq_result}
        else:
            partition = _run_algorithm(
                candidate=candidate,
                algo_params=algo_params,
            )
            uq_result = None
            uq_meta = None
        
        runtime_ms = (time.time() - start_time) * 1000
        
        # Compute metrics
        metric_values = _compute_metrics(
            partition=partition,
            network=network,
            metrics=metrics,
            runtime_ms=runtime_ms,
            uq_result=uq_result,
        )
        
        # Create result
        result = ContestantResult(
            contestant_id=candidate.contestant_id,
            algo_name=candidate.name,
            params=candidate.params,
            partition=partition,
            metrics=metric_values,
            runtime_ms=runtime_ms,
            seed_used=contestant_seed,
            uq_meta=uq_meta,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to evaluate {candidate.contestant_id}: {e}")
        
        # Return failed result
        return ContestantResult(
            contestant_id=candidate.contestant_id,
            algo_name=candidate.name,
            params=candidate.params,
            partition={},
            metrics={},
            runtime_ms=0.0,
            seed_used=contestant_seed,
            errors=[str(e)],
        )


def _derive_contestant_seed(master_seed: int, contestant_id: str) -> int:
    """Derive deterministic seed for a contestant.
    
    Args:
        master_seed: Master random seed
        contestant_id: Contestant ID
    
    Returns:
        Derived seed as integer
    """
    # Hash the contestant ID with master seed
    hash_input = f"{master_seed}:{contestant_id}".encode("utf-8")
    hash_digest = hashlib.sha256(hash_input).digest()
    
    # Convert to integer mod 2^32
    seed = int.from_bytes(hash_digest[:4], byteorder="big") % (2**32)
    return seed


def _run_algorithm(
    candidate: CandidateSpec,
    algo_params: Dict[str, Any],
) -> Dict[Any, int]:
    """Run algorithm without UQ.
    
    Args:
        candidate: CandidateSpec
        algo_params: Algorithm parameters
    
    Returns:
        Partition dict
    """
    result = candidate.callable(**algo_params)
    
    # Handle different return types
    if isinstance(result, tuple):
        # Could be (partition, score) or (model, selection_info)
        first_elem = result[0]
        
        # Check if first element is an SBM model or other object with to_partition_vector
        if hasattr(first_elem, 'to_partition_vector') and callable(getattr(first_elem, 'to_partition_vector')):
            # SBM model with selection info
            partition = first_elem.to_partition_vector()
        elif isinstance(first_elem, dict):
            # Standard (partition, score) tuple
            partition = first_elem
        else:
            raise ValueError(f"Unexpected tuple element type: {type(first_elem)}")
    elif isinstance(result, dict):
        partition = result
    elif hasattr(result, 'to_partition_vector') and callable(getattr(result, 'to_partition_vector')):
        # Direct SBM model return
        partition = result.to_partition_vector()
    elif hasattr(result, 'consensus_partition'):
        # UQResult or similar object with consensus_partition attribute
        consensus = getattr(result, 'consensus_partition')
        if callable(consensus):
            # CommunityDistribution with consensus_partition() method
            partition_array = consensus()
            # Convert array to dict - need to get nodes from result
            if hasattr(result, 'nodes'):
                nodes = result.nodes
                partition = {node: int(partition_array[i]) for i, node in enumerate(nodes)}
            else:
                raise ValueError(f"Result has consensus_partition() method but no nodes attribute: {type(result)}")
        elif isinstance(consensus, dict):
            # UQResult with consensus_partition dict attribute
            partition = consensus
        else:
            raise ValueError(f"Unexpected consensus_partition type: {type(consensus)}")
    elif hasattr(result, 'consensus'):
        # Check for consensus attribute (might be alternative naming)
        consensus = getattr(result, 'consensus')
        if isinstance(consensus, dict):
            partition = consensus
        else:
            raise ValueError(f"Unexpected consensus type: {type(consensus)}")
    else:
        raise ValueError(f"Unexpected result type: {type(result)}")
    
    return partition


def _run_algorithm_with_uq(
    candidate: CandidateSpec,
    algo_params: Dict[str, Any],
    uq_config: Dict[str, Any],
) -> Tuple[Dict[Any, int], Any]:
    """Run algorithm with UQ.
    
    Args:
        candidate: CandidateSpec
        algo_params: Algorithm parameters
        uq_config: UQ configuration
    
    Returns:
        Tuple of (consensus_partition, uq_result)
    """
    # Import UQ execution
    from py3plex.dsl.community_uq import execute_community_with_uq
    
    # Extract algorithm parameters
    net = algo_params.pop("network")
    method = candidate.name
    
    # UQ parameters
    uq_method = uq_config.get("method", "seed")
    n_samples = uq_config.get("n_samples", 10)
    seed = uq_config.get("seed", 0)
    
    # Run with UQ
    consensus_partition, partition_uq = execute_community_with_uq(
        network=net,
        method=method,
        uq_method=uq_method,
        n_samples=n_samples,
        seed=seed,
        **algo_params
    )
    
    return consensus_partition, partition_uq


def _compute_metrics(
    partition: Dict[Any, int],
    network: Any,
    metrics: List[MetricSpec],
    runtime_ms: float,
    uq_result: Optional[Any] = None,
) -> Dict[str, Any]:
    """Compute metrics for a partition.
    
    Args:
        partition: Partition dict
        network: Network
        metrics: List of MetricSpec
        runtime_ms: Runtime in milliseconds
        uq_result: Optional UQ result
    
    Returns:
        Dict of metric name -> value
    """
    metric_values = {}
    
    # Build context
    context = {
        "runtime_ms": runtime_ms,
        "uq": uq_result,
    }
    
    for metric_spec in metrics:
        try:
            # Skip UQ metrics if no UQ result
            if metric_spec.requires_uq and uq_result is None:
                continue
            
            # Compute metric
            value = metric_spec.callable(partition, network, context)
            metric_values[metric_spec.name] = value
        
        except Exception as e:
            logger.debug(f"Failed to compute {metric_spec.name}: {e}")
            # Mark as NA
            metric_values[metric_spec.name] = float("nan")
    
    return metric_values
