"""Execution engine for AutoCommunity meta-algorithm.

This module implements the core execution logic:
1. Run candidate algorithms
2. Evaluate on multiple metrics
3. Compute null model Z-scores
4. Apply Pareto selection
5. Build consensus if needed
6. Quantify uncertainty
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Callable
import time
import warnings

import numpy as np
import pandas as pd

from py3plex.exceptions import AlgorithmError
from py3plex.algorithms.community_detection.autocommunity import (
    AutoCommunityResult,
    CommunityStats,
)
from py3plex.uncertainty.partition import CommunityDistribution


def execute_autocommunity(
    network: Any,
    candidate_algorithms: List[str],
    metric_names: List[str],
    uq_config: Optional[Dict[str, Any]],
    null_config: Optional[Dict[str, Any]],
    use_pareto: bool,
    seed: int,
    custom_metrics: List[Callable],
    custom_candidates: List[Dict[str, Any]],
    metric_directions: Optional[Dict[str, str]] = None,
) -> AutoCommunityResult:
    """Execute AutoCommunity meta-algorithm.
    
    Args:
        network: Multilayer network
        candidate_algorithms: List of algorithm names
        metric_names: List of metric names
        uq_config: UQ configuration (or None)
        null_config: Null model configuration (or None)
        use_pareto: Whether to use Pareto selection
        seed: Random seed
        custom_metrics: Custom metric functions
        custom_candidates: Custom candidate specifications
    
    Returns:
        AutoCommunityResult
    """
    # Phase 1: Compute graph regime features
    regime_features = _compute_graph_regime(network)
    
    # Phase 2: Run all candidate algorithms
    algorithm_results = _run_candidate_algorithms(
        network=network,
        candidates=candidate_algorithms,
        seed=seed,
        uq_config=uq_config,
    )
    
    if not algorithm_results:
        raise AlgorithmError(
            "No algorithms produced valid partitions",
            suggestions=["Check network connectivity", "Try different algorithms"]
        )
    
    # Phase 3: Evaluate all algorithms on all metrics
    evaluation_matrix = _evaluate_algorithms(
        network=network,
        algorithm_results=algorithm_results,
        metric_names=metric_names,
        custom_metrics=custom_metrics,
    )
    
    # Phase 4: Null model calibration (if enabled)
    null_results = None
    if null_config:
        null_results = _compute_null_model_scores(
            network=network,
            algorithm_results=algorithm_results,
            evaluation_matrix=evaluation_matrix,
            null_config=null_config,
            seed=seed,
        )
        
        # Filter algorithms with weak null separation
        algorithm_results = _filter_by_null_scores(
            algorithm_results,
            null_results,
            threshold=1.5  # Minimum Z-score
        )
        
        if not algorithm_results:
            warnings.warn(
                "All algorithms filtered by null model test. "
                "Using original results.",
                stacklevel=2
            )
            # Restore original results
            algorithm_results = _run_candidate_algorithms(
                network=network,
                candidates=candidate_algorithms,
                seed=seed,
                uq_config=uq_config,
            )
    
    # Phase 5: Pareto selection
    if use_pareto:
        if metric_directions is None:
            metric_directions = {}
            for metric in custom_metrics:
                name = getattr(metric, "name", None)
                direction = getattr(metric, "direction", None)
                if name and direction in {"min", "max"}:
                    metric_directions[name] = direction

        pareto_front, selected_id = _pareto_selection(
            evaluation_matrix=evaluation_matrix,
            algorithm_results=algorithm_results,
            metric_directions=metric_directions,
        )
    else:
        # Fallback: single-metric selection (backward compatibility)
        pareto_front = [list(algorithm_results.keys())[0]]
        selected_id = pareto_front[0]
    
    # Phase 6: Consensus if multiple non-dominated
    if len(pareto_front) > 1:
        consensus_partition, community_stats = _build_consensus(
            network=network,
            pareto_front=pareto_front,
            algorithm_results=algorithm_results,
        )
        selected_id = "consensus"
    else:
        # Single winner
        selected_id = pareto_front[0]
        winner_result = algorithm_results[selected_id]
        consensus_partition = winner_result['partition']
        
        # Build stats from UQ data if available
        if winner_result.get('uq_data'):
            community_stats = _build_stats_from_uq(
                partition=consensus_partition,
                uq_data=winner_result['uq_data'],
            )
        else:
            community_stats = _build_stats_from_partition(
                partition=consensus_partition,
            )
    
    # Phase 7: Package results
    result = AutoCommunityResult(
        algorithms_tested=list(algorithm_results.keys()),
        pareto_front=pareto_front,
        selected=selected_id,
        consensus_partition=consensus_partition,
        community_stats=community_stats,
        evaluation_matrix=evaluation_matrix,
        diagnostics={
            algo_id: {
                'runtime_ms': result['runtime_ms'],
                'n_communities': len(set(result['partition'].values())),
            }
            for algo_id, result in algorithm_results.items()
        },
        provenance={
            'seed': seed,
            'uq_enabled': uq_config is not None,
            'null_enabled': null_config is not None,
            'pareto_enabled': use_pareto,
            'n_candidates': len(candidate_algorithms),
            'n_metrics': len(metric_names),
        },
        null_model_results=null_results,
        graph_regime=regime_features,
    )
    
    return result


def _compute_graph_regime(network: Any) -> Dict[str, float]:
    """Compute graph regime diagnostic features.
    
    Args:
        network: Multilayer network
    
    Returns:
        Dictionary with regime features
    """
    features = {}
    
    try:
        # Degree heterogeneity (coefficient of variation)
        degrees = []
        for node in network.get_nodes():
            degree = network.core_network.degree(node)
            degrees.append(degree)
        
        if degrees:
            mean_deg = np.mean(degrees)
            std_deg = np.std(degrees)
            features['degree_heterogeneity'] = std_deg / mean_deg if mean_deg > 0 else 0.0
            features['mean_degree'] = float(mean_deg)
            features['max_degree'] = float(np.max(degrees))
        
        # Layer density variance
        # Extract layer names directly from nodes without computing layout
        layers = list({node[1] for node in network.get_nodes()})
        if len(layers) > 1:
            densities = []
            for layer in layers:
                layer_edges = [
                    e for e in network.core_network.edges()
                    if e[2].get('layer') == layer
                ]
                layer_nodes = [
                    n for n in network.get_nodes()
                    if n[1] == layer
                ]
                
                n_nodes = len(layer_nodes)
                n_edges = len(layer_edges)
                
                if n_nodes > 1:
                    max_edges = n_nodes * (n_nodes - 1) / 2
                    density = n_edges / max_edges if max_edges > 0 else 0.0
                    densities.append(density)
            
            if densities:
                features['layer_density_variance'] = float(np.var(densities))
                features['mean_density'] = float(np.mean(densities))
        
        # Inter-layer coupling strength
        # (Ratio of inter-layer edges to total edges)
        inter_layer_edges = 0
        total_edges = 0
        
        for edge in network.core_network.edges(data=True):
            source = edge[0]
            target = edge[1]
            
            # Handle both tuple (node, layer) and regular node formats
            if isinstance(source, tuple) and len(source) >= 2:
                source_layer = source[1]
            else:
                source_layer = None
            
            if isinstance(target, tuple) and len(target) >= 2:
                target_layer = target[1]
            else:
                target_layer = None
            
            total_edges += 1
            if source_layer and target_layer and source_layer != target_layer:
                inter_layer_edges += 1
        
        if total_edges > 0:
            features['coupling_strength'] = inter_layer_edges / total_edges
        else:
            features['coupling_strength'] = 0.0
        
    except Exception as e:
        warnings.warn(f"Failed to compute some regime features: {e}", stacklevel=2)
    
    return features


def _run_candidate_algorithms(
    network: Any,
    candidates: List[str],
    seed: int,
    uq_config: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Run all candidate algorithms and collect results.
    
    Args:
        network: Multilayer network
        candidates: List of algorithm names
        seed: Random seed
        uq_config: UQ configuration (or None)
    
    Returns:
        Dictionary mapping algorithm_id -> result dict
    """
    from py3plex.algorithms.community_detection import (
        multilayer_louvain,
        leiden_multilayer,
        multilayer_leiden_uq,
    )
    
    results = {}
    
    for algo_name in candidates:
        algo_id = f"{algo_name}:default"
        
        try:
            start_time = time.time()
            
            # Run algorithm
            if algo_name == "louvain":
                if uq_config:
                    # Run with UQ
                    from py3plex.algorithms.community_detection import multilayer_louvain_distribution
                    dist = multilayer_louvain_distribution(
                        network,
                        n_runs=uq_config.get('n_samples', 50),
                        seed=seed,
                    )
                    partition = dist.consensus_partition()
                    # Convert array to dict
                    partition_dict = {
                        node: int(partition[i])
                        for i, node in enumerate(dist.nodes)
                    }
                    uq_data = dist
                else:
                    partition_dict, _ = multilayer_louvain(
                        network,
                        random_state=seed,
                    )
                    uq_data = None
            
            elif algo_name == "leiden":
                if uq_config:
                    # Run with UQ
                    uq_result = multilayer_leiden_uq(
                        network,
                        n_runs=uq_config.get('n_samples', 50),
                        seed=seed,
                    )
                    partition_dict = uq_result.consensus
                    uq_data = uq_result
                else:
                    leiden_result = leiden_multilayer(
                        network,
                        seed=seed,
                    )
                    partition_dict = leiden_result.communities  # Use 'communities', not 'partition'
                    uq_data = None

            elif algo_name in ("sbm", "standard_sbm", "dc_sbm", "degree_corrected_sbm"):
                # Use runner for SBM algorithms
                from py3plex.algorithms.community_detection.runner import run_community_algorithm
                from py3plex.algorithms.community_detection.budget import BudgetSpec

                # Configure budget
                budget = BudgetSpec(
                    max_iter=100,
                    n_restarts=3,
                    uq_samples=uq_config.get('n_samples', None) if uq_config else None
                )

                # Map algorithm name
                algo_id_runner = "dc_sbm" if algo_name in ("dc_sbm", "degree_corrected_sbm") else "sbm"

                # Run via runner
                result = run_community_algorithm(
                    algorithm_id=algo_id_runner,
                    network=network,
                    budget=budget,
                    seed=seed,
                    K_range=[2, 3, 4, 5, 6]  # Conservative K range for AutoCommunity
                )

                partition_dict = result.partition
                runtime_ms = result.runtime_ms
                uq_data = None  # UQ data already aggregated in meta

                # Store in results with metadata
                results[algo_id] = {
                    'algorithm': algo_name,
                    'partition': partition_dict,
                    'runtime_ms': runtime_ms,
                    'uq_data': uq_data,
                    'meta': result.meta,  # Include SBM-specific metadata
                }
                continue  # Skip the standard result packaging below

            elif algo_name == "infomap":
                # Run infomap
                from py3plex.algorithms.community_detection.community_wrapper import infomap_communities
                # Note: UQ not yet supported for infomap
                if uq_config:
                    warnings.warn(
                        "UQ not yet implemented for infomap, running without UQ",
                        stacklevel=2
                    )
                try:
                    partition_dict = infomap_communities(
                        network,
                        multiplex=True,
                        verbose=False,
                        seed=seed,
                    )
                    uq_data = None
                except Exception as e:
                    # If infomap fails (e.g., binary not found), skip gracefully
                    warnings.warn(f"Infomap failed: {e}. Skipping this algorithm.", stacklevel=2)
                    continue

            else:
                warnings.warn(f"Algorithm '{algo_name}' not implemented yet", stacklevel=2)
                continue
            
            runtime_ms = (time.time() - start_time) * 1000
            
            results[algo_id] = {
                'algorithm': algo_name,
                'partition': partition_dict,
                'runtime_ms': runtime_ms,
                'uq_data': uq_data,
            }
        
        except Exception as e:
            warnings.warn(f"Algorithm '{algo_name}' failed: {e}", stacklevel=2)
            continue
    
    return results


def _evaluate_algorithms(
    network: Any,
    algorithm_results: Dict[str, Dict[str, Any]],
    metric_names: List[str],
    custom_metrics: List[Callable],
) -> pd.DataFrame:
    """Evaluate all algorithms on all metrics.
    
    Args:
        network: Multilayer network
        algorithm_results: Algorithm results
        metric_names: List of metric names
        custom_metrics: Custom metric functions
    
    Returns:
        DataFrame with rows=algorithms, columns=metrics
    """
    from py3plex.algorithms.community_detection import multilayer_modularity
    from py3plex.algorithms.community_detection.multilayer_quality_metrics import (
        replica_consistency,
        layer_entropy,
    )
    
    import inspect

    custom_metric_map = {}
    for metric in custom_metrics:
        name = getattr(metric, "name", None)
        func = getattr(metric, "callable", None)
        if name and func:
            custom_metric_map[name] = func
        elif callable(metric):
            custom_metric_map[metric.__name__] = metric

    rows = []
    
    for algo_id, result in algorithm_results.items():
        partition = result['partition']
        
        row = {'algorithm_id': algo_id}
        
        for metric_name in metric_names:
            try:
                if metric_name == "modularity":
                    value = multilayer_modularity(
                        network=network,
                        communities=partition,
                    )
                
                elif metric_name == "stability":
                    # Use UQ data if available
                    if result.get('uq_data'):
                        # Compute stability from co-assignment matrix
                        if hasattr(result['uq_data'], 'node_confidence'):
                            confidence = result['uq_data'].node_confidence()
                            value = float(np.mean(confidence))
                        else:
                            value = 0.5  # Neutral value
                    else:
                        value = 0.5  # Neutral value without UQ
                
                elif metric_name == "coverage":
                    # Fraction of nodes in non-singleton communities
                    comm_sizes = {}
                    for node, comm in partition.items():
                        comm_sizes[comm] = comm_sizes.get(comm, 0) + 1
                    
                    non_singleton = sum(
                        1 for node, comm in partition.items()
                        if comm_sizes[comm] > 1
                    )
                    value = non_singleton / len(partition) if partition else 0.0
                
                elif metric_name == "entropy":
                    # Assignment entropy (lower is better)
                    if result.get('uq_data'):
                        if hasattr(result['uq_data'], 'node_entropy'):
                            entropy = result['uq_data'].node_entropy()
                            value = float(np.mean(entropy))
                        else:
                            value = 0.0
                    else:
                        value = 0.0
                
                elif metric_name == "mdl":
                    # Description length (if available)
                    # Placeholder for now
                    value = 0.0
                
                elif metric_name == "replica_consistency":
                    # Multilayer coherence metric
                    value = replica_consistency(partition, network)

                elif metric_name == "layer_entropy":
                    # Multilayer degeneracy guardrail
                    value = layer_entropy(partition, network)

                else:
                    custom_func = custom_metric_map.get(metric_name)
                    if custom_func is None:
                        warnings.warn(
                            f"Metric '{metric_name}' not implemented",
                            stacklevel=2,
                        )
                        value = 0.0
                    else:
                        context = {
                            "algorithm_id": algo_id,
                            "algorithm": result.get("algorithm"),
                            "runtime_ms": result.get("runtime_ms"),
                            "uq": result.get("uq_data"),
                        }
                        values = {
                            "partition": partition,
                            "communities": partition,
                            "community_assignments": partition,
                            "net": network,
                            "network": network,
                            "context": context,
                            "contestant_metadata": context,
                            "meta": context,
                            "metadata": context,
                        }

                        try:
                            sig = inspect.signature(custom_func)
                            params = sig.parameters
                        except (TypeError, ValueError):
                            params = {}

                        if params:
                            kwargs = {
                                name: values[name]
                                for name in params
                                if name in values
                            }
                            if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
                                kwargs.setdefault("partition", partition)
                                kwargs.setdefault("network", network)
                                kwargs.setdefault("context", context)
                            if kwargs:
                                value = custom_func(**kwargs)
                            else:
                                arity = len(params)
                                if arity >= 3:
                                    value = custom_func(partition, network, context)
                                elif arity == 2:
                                    value = custom_func(partition, network)
                                elif arity == 1:
                                    value = custom_func(partition)
                                else:
                                    value = custom_func()
                        else:
                            value = custom_func(partition, network, context)
                
                row[metric_name] = value
            
            except Exception as e:
                warnings.warn(f"Failed to compute {metric_name} for {algo_id}: {e}", stacklevel=2)
                row[metric_name] = np.nan
        
        rows.append(row)
    
    return pd.DataFrame(rows)


def _compute_null_model_scores(
    network: Any,
    algorithm_results: Dict[str, Dict[str, Any]],
    evaluation_matrix: pd.DataFrame,
    null_config: Dict[str, Any],
    seed: int,
) -> Dict[str, Any]:
    """Compute null model Z-scores for each algorithm.
    
    Args:
        network: Multilayer network
        algorithm_results: Algorithm results
        evaluation_matrix: Evaluation matrix
        null_config: Null model configuration
        seed: Random seed
    
    Returns:
        Dictionary with null model results
    """
    from py3plex.nullmodels import generate_null_model
    
    try:
        # Generate null models
        null_result = generate_null_model(
            network,
            model=null_config['type'],
            samples=null_config['samples'],
            seed=seed,
        )
        
        # For each algorithm, compute Z-scores
        z_scores = {}
        null_distributions = {}
        
        for algo_id, result in algorithm_results.items():
            algo_name = result['algorithm']
            
            # Run algorithm on null models
            null_metrics = []
            
            for null_network in null_result.samples[:10]:  # Sample subset for speed
                try:
                    # Run same algorithm on null
                    if algo_name == "louvain":
                        from py3plex.algorithms.community_detection import multilayer_louvain
                        null_partition, _ = multilayer_louvain(
                            null_network,
                            random_state=seed,
                        )
                    elif algo_name == "leiden":
                        from py3plex.algorithms.community_detection import leiden_multilayer
                        null_leiden = leiden_multilayer(
                            null_network,
                            seed=seed,
                        )
                        null_partition = null_leiden.partition
                    elif algo_name == "infomap":
                        from py3plex.algorithms.community_detection.community_wrapper import infomap_communities
                        try:
                            null_partition = infomap_communities(
                                null_network,
                                multiplex=True,
                                verbose=False,
                                seed=seed,
                            )
                        except Exception:
                            # Skip if infomap fails on null model
                            continue
                    else:
                        continue
                    
                    # Compute modularity on null
                    from py3plex.algorithms.community_detection import multilayer_modularity
                    null_mod = multilayer_modularity(
                        network=null_network,
                        communities=null_partition,
                    )
                    null_metrics.append(null_mod)
                
                except Exception:
                    continue
            
            if null_metrics:
                # Compute Z-score
                observed_mod = evaluation_matrix[
                    evaluation_matrix['algorithm_id'] == algo_id
                ]['modularity'].values[0]
                
                null_mean = np.mean(null_metrics)
                null_std = np.std(null_metrics)
                
                if null_std > 0:
                    z_score = (observed_mod - null_mean) / null_std
                else:
                    z_score = 0.0
                
                z_scores[algo_id] = float(z_score)
                null_distributions[algo_id] = null_metrics
        
        return {
            'z_scores': z_scores,
            'null_distributions': null_distributions,
            'null_config': null_config,
        }
    
    except Exception as e:
        warnings.warn(f"Null model computation failed: {e}", stacklevel=2)
        return {}


def _filter_by_null_scores(
    algorithm_results: Dict[str, Dict[str, Any]],
    null_results: Dict[str, Any],
    threshold: float,
) -> Dict[str, Dict[str, Any]]:
    """Filter algorithms by null model Z-scores.
    
    Args:
        algorithm_results: Algorithm results
        null_results: Null model results
        threshold: Minimum Z-score threshold
    
    Returns:
        Filtered algorithm results
    """
    if not null_results or 'z_scores' not in null_results:
        return algorithm_results
    
    z_scores = null_results['z_scores']
    
    filtered = {
        algo_id: result
        for algo_id, result in algorithm_results.items()
        if z_scores.get(algo_id, 0.0) >= threshold
    }
    
    return filtered if filtered else algorithm_results


def _pareto_selection(
    evaluation_matrix: pd.DataFrame,
    algorithm_results: Dict[str, Dict[str, Any]],
    metric_directions: Optional[Dict[str, str]] = None,
) -> Tuple[List[str], str]:
    """Apply Pareto dominance to select non-dominated algorithms.
    
    Args:
        evaluation_matrix: DataFrame with metrics
        algorithm_results: Algorithm results
    
    Returns:
        Tuple of (pareto_front, selected_id)
    """
    # Define metric directions (max or min)
    base_directions = {
        'modularity': 'max',
        'stability': 'max',
        'coverage': 'max',
        'entropy': 'min',  # Lower is better
        'mdl': 'min',  # Lower is better
        'replica_consistency': 'max',  # Higher is better (multilayer coherence)
        'layer_entropy': 'max',  # Higher is better (degeneracy guardrail)
    }
    direction_map = dict(base_directions)
    if metric_directions:
        direction_map.update(metric_directions)
    
    # Extract metric columns
    metric_cols = [col for col in evaluation_matrix.columns if col != 'algorithm_id']
    
    # Compute Pareto dominance
    pareto_front = []
    
    for i, row_i in evaluation_matrix.iterrows():
        algo_i = row_i['algorithm_id']
        dominated = False
        
        for j, row_j in evaluation_matrix.iterrows():
            if i == j:
                continue
            
            algo_j = row_j['algorithm_id']
            
            # Check if j dominates i
            dominates = True
            strictly_better = False
            
            for metric in metric_cols:
                val_i = row_i[metric]
                val_j = row_j[metric]
                
                # Skip NaN
                if np.isnan(val_i) or np.isnan(val_j):
                    continue
                
                direction = direction_map.get(metric, 'max')
                
                if direction == 'max':
                    if val_j < val_i:
                        dominates = False
                        break
                    elif val_j > val_i:
                        strictly_better = True
                else:  # min
                    if val_j > val_i:
                        dominates = False
                        break
                    elif val_j < val_i:
                        strictly_better = True
            
            if dominates and strictly_better:
                dominated = True
                break
        
        if not dominated:
            pareto_front.append(algo_i)
    
    # Select from Pareto front
    if len(pareto_front) == 1:
        selected = pareto_front[0]
    else:
        # If multiple, select by modularity (as tiebreaker) when available,
        # otherwise use a mean rank across available metrics.
        pareto_rows = evaluation_matrix[
            evaluation_matrix['algorithm_id'].isin(pareto_front)
        ]
        if 'modularity' in pareto_rows.columns:
            selected = pareto_rows.sort_values('modularity', ascending=False).iloc[0][
                'algorithm_id'
            ]
        else:
            ranks = []
            for metric in metric_cols:
                if metric not in pareto_rows.columns:
                    continue
                direction = direction_map.get(metric, 'max')
                if direction == 'min':
                    rank = pareto_rows[metric].rank(ascending=True, method='average')
                else:
                    rank = pareto_rows[metric].rank(ascending=False, method='average')
                ranks.append(rank)

            if ranks:
                mean_rank = sum(ranks) / len(ranks)
                selected = pareto_rows.loc[mean_rank.idxmin(), 'algorithm_id']
            else:
                selected = pareto_rows.iloc[0]['algorithm_id']
    
    return pareto_front, selected


def _build_consensus(
    network: Any,
    pareto_front: List[str],
    algorithm_results: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[Tuple[Any, Any], int], CommunityStats]:
    """Build consensus partition from Pareto front algorithms.
    
    Args:
        network: Multilayer network
        pareto_front: List of non-dominated algorithm IDs
        algorithm_results: Algorithm results
    
    Returns:
        Tuple of (consensus_partition, community_stats)
    """
    # Collect partitions from Pareto front
    partitions = []
    nodes = None
    
    for algo_id in pareto_front:
        result = algorithm_results[algo_id]
        partition = result['partition']
        
        if nodes is None:
            nodes = list(partition.keys())
        
        # Convert to array
        partition_array = np.array([partition[node] for node in nodes])
        partitions.append(partition_array)
    
    # Build CommunityDistribution
    dist = CommunityDistribution(
        partitions=partitions,
        nodes=nodes,
        meta={'method': 'consensus', 'n_algorithms': len(pareto_front)},
    )
    
    # Get consensus partition
    consensus_array = dist.consensus_partition(method='medoid')
    
    # Convert back to dict
    consensus_dict = {
        node: int(consensus_array[i])
        for i, node in enumerate(nodes)
    }
    
    # Build stats
    stats = _build_stats_from_distribution(dist, consensus_array)
    
    return consensus_dict, stats


def _build_stats_from_distribution(
    dist: CommunityDistribution,
    consensus: np.ndarray,
) -> CommunityStats:
    """Build CommunityStats from CommunityDistribution.
    
    Args:
        dist: Community distribution
        consensus: Consensus partition array
    
    Returns:
        CommunityStats
    """
    # Compute statistics
    confidence = dist.node_confidence(consensus)
    entropy = dist.node_entropy()
    margin = dist.node_margin(consensus)
    
    # Convert to dict
    confidence_dict = {
        dist.nodes[i]: float(confidence[i])
        for i in range(len(dist.nodes))
    }
    entropy_dict = {
        dist.nodes[i]: float(entropy[i])
        for i in range(len(dist.nodes))
    }
    margin_dict = {
        dist.nodes[i]: float(margin[i])
        for i in range(len(dist.nodes))
    }
    
    # Compute community sizes
    comm_sizes = {}
    for i, comm in enumerate(consensus):
        comm_sizes[comm] = comm_sizes.get(comm, 0) + 1
    
    community_sizes = list(comm_sizes.values())
    n_communities = len(community_sizes)
    
    # Compute coverage
    non_singleton = sum(1 for size in community_sizes if size > 1)
    coverage = non_singleton / len(consensus) if len(consensus) > 0 else 0.0
    
    # Identify orphan nodes
    orphan_nodes = [
        dist.nodes[i]
        for i, comm in enumerate(consensus)
        if comm_sizes[comm] == 1
    ]
    
    # Compute stability
    stability = float(np.mean(confidence))
    
    return CommunityStats(
        n_communities=n_communities,
        community_sizes=community_sizes,
        node_confidence=confidence_dict,
        node_entropy=entropy_dict,
        node_margin=margin_dict,
        coverage=coverage,
        orphan_nodes=orphan_nodes,
        stability_score=stability,
    )


def _build_stats_from_uq(
    partition: Dict[Tuple[Any, Any], int],
    uq_data: Any,
) -> CommunityStats:
    """Build CommunityStats from UQ data.
    
    Args:
        partition: Consensus partition
        uq_data: UQ data (CommunityDistribution or UQResult)
    
    Returns:
        CommunityStats
    """
    # Extract stats from UQ data
    if hasattr(uq_data, 'node_confidence'):
        # CommunityDistribution
        nodes = list(partition.keys())
        consensus_array = np.array([partition[node] for node in nodes])
        
        confidence = uq_data.node_confidence(consensus_array)
        entropy = uq_data.node_entropy()
        margin = uq_data.node_margin(consensus_array)
        
        confidence_dict = {
            nodes[i]: float(confidence[i])
            for i in range(len(nodes))
        }
        entropy_dict = {
            nodes[i]: float(entropy[i])
            for i in range(len(nodes))
        }
        margin_dict = {
            nodes[i]: float(margin[i])
            for i in range(len(nodes))
        }
        
        stability = float(np.mean(confidence))
    
    elif hasattr(uq_data, 'confidence'):
        # UQResult
        confidence_dict = {k: float(v) for k, v in uq_data.confidence.items()}
        entropy_dict = None
        margin_dict = None
        stability = float(np.mean(list(uq_data.confidence.values())))
    
    else:
        # Fallback
        confidence_dict = None
        entropy_dict = None
        margin_dict = None
        stability = None
    
    # Compute community sizes
    comm_sizes = {}
    for node, comm in partition.items():
        comm_sizes[comm] = comm_sizes.get(comm, 0) + 1
    
    community_sizes = list(comm_sizes.values())
    n_communities = len(community_sizes)
    
    # Compute coverage
    non_singleton = sum(
        1 for node, comm in partition.items()
        if comm_sizes[comm] > 1
    )
    coverage = non_singleton / len(partition) if partition else 0.0
    
    # Identify orphan nodes
    orphan_nodes = [
        node for node, comm in partition.items()
        if comm_sizes[comm] == 1
    ]
    
    return CommunityStats(
        n_communities=n_communities,
        community_sizes=community_sizes,
        node_confidence=confidence_dict,
        node_entropy=entropy_dict,
        node_margin=margin_dict,
        coverage=coverage,
        orphan_nodes=orphan_nodes,
        stability_score=stability,
    )


def _build_stats_from_partition(
    partition: Dict[Tuple[Any, Any], int],
) -> CommunityStats:
    """Build CommunityStats from partition only (no UQ).
    
    Args:
        partition: Partition dict
    
    Returns:
        CommunityStats
    """
    # Compute community sizes
    comm_sizes = {}
    for node, comm in partition.items():
        comm_sizes[comm] = comm_sizes.get(comm, 0) + 1
    
    community_sizes = list(comm_sizes.values())
    n_communities = len(community_sizes)
    
    # Compute coverage
    non_singleton = sum(
        1 for node, comm in partition.items()
        if comm_sizes[comm] > 1
    )
    coverage = non_singleton / len(partition) if partition else 0.0
    
    # Identify orphan nodes
    orphan_nodes = [
        node for node, comm in partition.items()
        if comm_sizes[comm] == 1
    ]
    
    return CommunityStats(
        n_communities=n_communities,
        community_sizes=community_sizes,
        coverage=coverage,
        orphan_nodes=orphan_nodes,
    )


def execute_autocommunity_sh(
    network: Any,
    candidate_algorithms: List[str],
    metric_names: List[str],
    uq_config: Optional[Dict[str, Any]],
    seed: int,
    racer_config: Optional[Dict[str, Any]],
) -> AutoCommunityResult:
    """Execute AutoCommunity with Successive Halving strategy.
    
    Args:
        network: Multilayer network
        candidate_algorithms: List of algorithm names
        metric_names: List of metric names
        uq_config: UQ configuration (or None)
        seed: Random seed
        racer_config: Racer configuration (or None)
    
    Returns:
        AutoCommunityResult with racing history
    """
    from datetime import datetime, timezone
    from py3plex.algorithms.community_detection.successive_halving import (
        SuccessiveHalvingRacer,
        SuccessiveHalvingConfig,
    )
    from py3plex.algorithms.community_detection.budget import BudgetSpec
    
    # Build racer config
    racer_config = racer_config or {}
    
    # Extract budget0 if provided
    budget0_dict = racer_config.pop("budget0", None)
    if budget0_dict is not None:
        if isinstance(budget0_dict, dict):
            budget0 = BudgetSpec.from_dict(budget0_dict)
        elif isinstance(budget0_dict, BudgetSpec):
            budget0 = budget0_dict
        else:
            budget0 = None
    else:
        # Default budget
        budget0 = BudgetSpec(
            max_iter=5,
            n_restarts=1,
            resolution_trials=3,
            uq_samples=uq_config.get('n_samples', 10) if uq_config else 10,
        )
    
    # Build config
    config = SuccessiveHalvingConfig(
        budget0=budget0,
        **racer_config
    )
    
    # Create racer
    racer = SuccessiveHalvingRacer(config, seed=seed)
    
    # Run race
    history = racer.race(
        network=network,
        algorithm_ids=candidate_algorithms,
        metric_names=metric_names,
        n_jobs=1,
    )
    
    # Extract winner partition
    winner_id = history.winner_algo_id
    
    # Re-run winner to get final partition (or extract from last round)
    if history.rounds:
        last_round = history.rounds[-1]
        
        # Find winner's metrics in last round
        winner_metrics_records = [
            r for r in last_round['metrics']
            if r['algo_id'] == winner_id
        ]
        
        if winner_metrics_records:
            winner_metrics = winner_metrics_records[0]
        else:
            winner_metrics = {}
    else:
        winner_metrics = {}
    
    # Re-run winner with full budget to get partition
    from py3plex.algorithms.community_detection.runner import run_community_algorithm
    
    final_budget = BudgetSpec(
        max_iter=50,
        n_restarts=5,
        resolution_trials=10,
        uq_samples=uq_config.get('n_samples', 50) if uq_config else 50,
    )
    
    final_result = run_community_algorithm(
        algorithm_id=winner_id,
        network=network,
        budget=final_budget,
        seed=seed,
    )
    
    consensus_partition = final_result.partition
    
    # Build stats from partition
    community_stats = _build_stats_from_partition(consensus_partition)
    
    # Build evaluation matrix from racing history
    eval_rows = []
    for round_rec in history.rounds:
        for metric_rec in round_rec['metrics']:
            eval_rows.append(metric_rec)
    
    if eval_rows:
        evaluation_matrix = pd.DataFrame(eval_rows)
    else:
        evaluation_matrix = pd.DataFrame()
    
    # Build provenance
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    
    # Get version dynamically
    try:
        import importlib.metadata
        py3plex_version = importlib.metadata.version('py3plex')
    except Exception:
        py3plex_version = '1.1.2'  # Fallback for development installs
    
    provenance = {
        'engine': 'autocommunity_successive_halving',
        'py3plex_version': py3plex_version,
        'timestamp_utc': timestamp_utc,
        'seed': seed,
        'strategy': 'successive_halving',
        'racer_config': config.__dict__,
        'n_candidates': len(candidate_algorithms),
        'n_metrics': len(metric_names),
        'n_rounds': len(history.rounds),
        'racing_history': history.to_dict(),
    }
    
    # Build diagnostics
    diagnostics = {
        'racing_status': history.status,
        'finalists': history.finalists,
        'total_runtime_ms': history.total_runtime_ms,
    }
    
    # Build result
    result = AutoCommunityResult(
        algorithms_tested=candidate_algorithms,
        pareto_front=[winner_id],  # For compatibility
        selected=winner_id,
        consensus_partition=consensus_partition,
        community_stats=community_stats,
        evaluation_matrix=evaluation_matrix,
        diagnostics=diagnostics,
        provenance=provenance,
        null_model_results=None,
        graph_regime=None,
    )
    
    return result
