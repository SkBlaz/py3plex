#!/usr/bin/env python3
"""
Meta Flow Report - Comprehensive Multilayer Network Analysis

This module provides a unified interface for conducting multiple network analyses
at once, including centralities, communities, and statistics. It enables users
to easily perform comprehensive multilayer network analysis with a single function call.

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Dict, List, Optional
import warnings


class MetaFlowReport:
    """
    Class for generating comprehensive multilayer network analysis reports.

    This class provides a unified interface for running multiple analyses at once:
    - Centrality measures (degree, eigenvector, betweenness, etc.)
    - Community detection algorithms (Louvain, Leiden, etc.)
    - Network statistics (density, clustering, modularity, etc.)

    Example:
        >>> from py3plex.core import multinet
        >>> from py3plex.algorithms.meta_flow_report import MetaFlowReport
        >>>
        >>> network = multinet.multi_layer_network(directed=False)
        >>> network.add_edges([
        ...     ['A', 'L1', 'B', 'L1', 1],
        ...     ['B', 'L1', 'C', 'L1', 1],
        ... ], input_type='list')
        >>>
        >>> report = MetaFlowReport(network)
        >>> results = report.run_all_analyses()
        >>> report.print_summary(results)
    """

    def __init__(self, network: Any):
        """
        Initialize the meta flow report generator.

        Args:
            network: py3plex multi_layer_network object
        """
        self.network = network
        self._results: Dict[str, Any] = {}

    def compute_centralities(
        self,
        include_path_based: bool = False,
        include_advanced: bool = False,
        wf_improved: bool = True
    ) -> Dict[str, Any]:
        """
        Compute multiple centrality measures at once.

        By default, computes fast centrality measures:
        - Degree-based: layer_degree, layer_strength, supra_degree, supra_strength,
          overlapping_degree, overlapping_strength, participation_coefficient
        - Eigenvector-based: multiplex_eigenvector, eigenvector_versatility,
          katz_bonacich, pagerank

        Args:
            include_path_based: If True, also compute path-based measures (betweenness,
                               closeness). These are computationally expensive O(n^3).
                               Default: False (skipped).
            include_advanced: If True, also compute advanced measures (HITS,
                             current-flow, communicability, k-core). These are
                             computationally expensive. Default: False (skipped).
            wf_improved: For closeness centrality, use Wasserman-Faust improved
                        scaling (affects disconnected graphs). Default: True.

        Returns:
            Dictionary containing all computed centrality measures with keys
            corresponding to measure names.

        Note:
            Path-based and advanced measures are EXPENSIVE for large networks.
            The function will emit a note about which centralities were computed.
        """
        try:
            from py3plex.algorithms.multilayer_algorithms.centrality import (
                compute_all_centralities
            )

            import logging
            logger = logging.getLogger(__name__)

            centralities = compute_all_centralities(
                self.network,
                include_path_based=include_path_based,
                include_advanced=include_advanced,
                wf_improved=wf_improved
            )

            # Log information about which centralities were computed
            centrality_types = ["degree-based", "eigenvector-based"]
            if include_path_based:
                centrality_types.append("path-based")
            if include_advanced:
                centrality_types.append("advanced")

            logger.info(f"Computed centralities: {', '.join(centrality_types)}")
            if not include_path_based:
                logger.info("Note: Path-based measures (betweenness, closeness) were skipped. "
                           "Set include_path_based=True to compute them.")
            if not include_advanced:
                logger.info("Note: Advanced measures (HITS, communicability, k-core) were skipped. "
                           "Set include_advanced=True to compute them.")

            return centralities
        except ImportError as e:
            warnings.warn(f"Could not compute centralities: {e}", stacklevel=2)
            return {}

    def detect_communities(
        self,
        methods: Optional[List[str]] = None,
        gamma: float = 1.0,
        omega: float = 1.0
    ) -> Dict[str, Any]:
        """
        Run multiple community detection algorithms at once.

        Args:
            methods: List of methods to use. Options: ['louvain', 'leiden']
                    If None, runs all available methods.
            gamma: Resolution parameter for modularity optimization
            omega: Inter-layer coupling strength

        Returns:
            Dictionary mapping method names to community assignments
        """
        if methods is None:
            methods = ['louvain', 'leiden']

        results = {}

        for method in methods:
            try:
                if method == 'louvain':
                    from py3plex.algorithms.community_detection.multilayer_modularity import (
                        louvain_multilayer
                    )
                    communities = louvain_multilayer(
                        self.network,
                        gamma=gamma,
                        omega=omega
                    )
                    results['louvain'] = communities

                elif method == 'leiden':
                    from py3plex.algorithms.community_detection.leiden_multilayer import (
                        leiden_multilayer
                    )
                    leiden_result = leiden_multilayer(
                        self.network,
                        gamma=gamma,
                        omega=omega
                    )
                    results['leiden'] = {
                        'communities': leiden_result.communities,
                        'modularity': leiden_result.modularity
                    }

            except ImportError as e:
                warnings.warn(f"Could not run {method} community detection: {e}", stacklevel=2)
            except Exception as e:
                warnings.warn(f"Error running {method}: {e}", stacklevel=2)

        return results

    def compute_statistics(
        self,
        include_advanced: bool = False
    ) -> Dict[str, Any]:
        """
        Compute multiple network statistics at once.

        Args:
            include_advanced: Include computationally expensive statistics

        Returns:
            Dictionary containing computed statistics
        """
        stats = {}

        try:
            from py3plex.algorithms.statistics import multilayer_statistics as mls

            # Get layers
            layers = list({nl[1] for nl in self.network.get_nodes()})

            # Basic statistics for each layer
            stats['layer_densities'] = {}
            for layer in layers:
                try:
                    density = mls.layer_density(self.network, layer)
                    stats['layer_densities'][layer] = density
                except Exception as e:
                    warnings.warn(f"Could not compute density for layer {layer}: {e}", stacklevel=2)

            # Node activities
            try:
                nodes = list({nl[0] for nl in self.network.get_nodes()})
                stats['node_activities'] = {}
                for node in nodes[:10]:  # Limit to first 10 nodes for performance
                    activity = mls.node_activity(self.network, node)
                    stats['node_activities'][node] = activity
            except Exception as e:
                warnings.warn(f"Could not compute node activities: {e}", stacklevel=2)

            # Inter-layer coupling (for first pair of layers)
            if len(layers) >= 2:
                try:
                    coupling = mls.inter_layer_coupling_strength(
                        self.network, layers[0], layers[1]
                    )
                    stats['inter_layer_coupling'] = {
                        f"{layers[0]}-{layers[1]}": coupling
                    }
                except Exception as e:
                    warnings.warn(f"Could not compute inter-layer coupling: {e}", stacklevel=2)

            # Edge overlap (for first pair of layers)
            if len(layers) >= 2:
                try:
                    overlap = mls.edge_overlap(self.network, layers[0], layers[1])
                    stats['edge_overlap'] = {
                        f"{layers[0]}-{layers[1]}": overlap
                    }
                except Exception as e:
                    warnings.warn(f"Could not compute edge overlap: {e}", stacklevel=2)

            # Advanced statistics
            if include_advanced:
                try:
                    versatility = mls.versatility_centrality(
                        self.network, centrality_type='degree'
                    )
                    stats['versatility_centrality'] = versatility
                except Exception as e:
                    warnings.warn(f"Could not compute versatility centrality: {e}", stacklevel=2)

                try:
                    clustering = mls.multilayer_clustering_coefficient(self.network)
                    stats['multilayer_clustering'] = clustering
                except Exception as e:
                    warnings.warn(f"Could not compute clustering: {e}", stacklevel=2)

        except ImportError as e:
            warnings.warn(f"Could not compute statistics: {e}", stacklevel=2)

        return stats

    def run_all_analyses(
        self,
        include_centralities: bool = True,
        include_communities: bool = True,
        include_statistics: bool = True,
        include_path_based: bool = False,
        include_advanced: bool = False,
        wf_improved: bool = True,
        community_methods: Optional[List[str]] = None,
        gamma: float = 1.0,
        omega: float = 1.0
    ) -> Dict[str, Any]:
        """
        Run all analyses at once - the main meta flow report function.

        This is the primary interface for comprehensive multilayer network analysis.
        It runs multiple centrality measures, community detection algorithms, and
        network statistics in a single call.

        Args:
            include_centralities: Whether to compute centrality measures
            include_communities: Whether to run community detection
            include_statistics: Whether to compute network statistics
            include_path_based: Include path-based centralities (computationally expensive)
            include_advanced: Include advanced measures (computationally expensive)
            wf_improved: For closeness centrality, use Wasserman-Faust improved scaling
            community_methods: List of community detection methods to use
            gamma: Resolution parameter for community detection
            omega: Inter-layer coupling strength

        Returns:
            Dictionary containing all analysis results with keys:
                - 'centralities': Centrality measures
                - 'communities': Community detection results
                - 'statistics': Network statistics
        """
        results = {}

        if include_centralities:
            print("Computing centrality measures...")
            results['centralities'] = self.compute_centralities(
                include_path_based=include_path_based,
                include_advanced=include_advanced,
                wf_improved=wf_improved
            )

        if include_communities:
            print("Running community detection...")
            results['communities'] = self.detect_communities(
                methods=community_methods,
                gamma=gamma,
                omega=omega
            )

        if include_statistics:
            print("Computing network statistics...")
            results['statistics'] = self.compute_statistics(
                include_advanced=include_advanced
            )

        self._results = results
        return results

    def print_summary(
        self,
        results: Optional[Dict[str, Any]] = None,
        top_n: int = 5
    ) -> None:
        """
        Print a human-readable summary of analysis results.

        Args:
            results: Analysis results dictionary (uses stored results if None)
            top_n: Number of top nodes to show for each measure
        """
        if results is None:
            results = self._results

        if not results:
            print("No analysis results available. Run run_all_analyses() first.")
            return

        print("=" * 80)
        print("META FLOW REPORT - Multilayer Network Analysis Summary")
        print("=" * 80)

        # Centralities
        if 'centralities' in results and results['centralities']:
            print("\n" + "=" * 80)
            print("CENTRALITY MEASURES")
            print("=" * 80)

            for measure_name, centrality_dict in results['centralities'].items():
                if isinstance(centrality_dict, dict) and centrality_dict:
                    print(f"\n{measure_name.replace('_', ' ').title()}:")

                    # Sort and show top N
                    sorted_items = sorted(
                        centrality_dict.items(),
                        key=lambda x: float(x[1]) if isinstance(x[1], (int, float)) else 0,
                        reverse=True
                    )[:top_n]

                    for node, value in sorted_items:
                        if isinstance(value, (int, float)):
                            print(f"  {str(node):30} {value:.6f}")

        # Communities
        if 'communities' in results and results['communities']:
            print("\n" + "=" * 80)
            print("COMMUNITY DETECTION")
            print("=" * 80)

            for method_name, comm_data in results['communities'].items():
                print(f"\n{method_name.title()} Communities:")

                if isinstance(comm_data, dict):
                    if 'communities' in comm_data:
                        communities = comm_data['communities']
                        # Count nodes per community
                        comm_counts: Dict[int, int] = {}
                        for comm_id in communities.values():
                            comm_counts[comm_id] = comm_counts.get(comm_id, 0) + 1

                        print(f"  Number of communities: {len(comm_counts)}")
                        print(f"  Community sizes: {dict(sorted(comm_counts.items()))}")

                        if 'modularity' in comm_data:
                            print(f"  Modularity: {comm_data['modularity']:.4f}")
                    else:
                        # Direct community assignment
                        comm_counts = {}
                        for comm_id in comm_data.values():
                            comm_counts[comm_id] = comm_counts.get(comm_id, 0) + 1

                        print(f"  Number of communities: {len(comm_counts)}")
                        print(f"  Community sizes: {dict(sorted(comm_counts.items()))}")

        # Statistics
        if 'statistics' in results and results['statistics']:
            print("\n" + "=" * 80)
            print("NETWORK STATISTICS")
            print("=" * 80)

            stats = results['statistics']

            if 'layer_densities' in stats:
                print("\nLayer Densities:")
                for layer, density in stats['layer_densities'].items():
                    print(f"  {layer}: {density:.4f}")

            if 'inter_layer_coupling' in stats:
                print("\nInter-layer Coupling:")
                for pair, coupling in stats['inter_layer_coupling'].items():
                    print(f"  {pair}: {coupling:.4f}")

            if 'edge_overlap' in stats:
                print("\nEdge Overlap:")
                for pair, overlap in stats['edge_overlap'].items():
                    print(f"  {pair}: {overlap:.4f}")

            if 'node_activities' in stats:
                print("\nNode Activities (sample):")
                for node, activity in list(stats['node_activities'].items())[:top_n]:
                    print(f"  {node}: {activity:.4f}")

            if 'versatility_centrality' in stats:
                print("\nVersatility Centrality (top nodes):")
                sorted_versatility = sorted(
                    stats['versatility_centrality'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:top_n]
                for node, value in sorted_versatility:
                    print(f"  {node}: {value:.4f}")

        print("\n" + "=" * 80)
        print("END OF REPORT")
        print("=" * 80)

    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export analysis results as a dictionary for further processing.

        Returns:
            Dictionary containing all analysis results
        """
        return self._results.copy()

    def get_top_nodes(
        self,
        measure: str,
        n: int = 10,
        category: str = 'centralities'
    ) -> List[tuple]:
        """
        Get top N nodes by a specific measure.

        Args:
            measure: Name of the measure (e.g., 'overlapping_degree')
            n: Number of top nodes to return
            category: Category of measure ('centralities', 'statistics')

        Returns:
            List of (node, value) tuples sorted by value
        """
        if not self._results or category not in self._results:
            return []

        if measure not in self._results[category]:
            return []

        data = self._results[category][measure]
        if not isinstance(data, dict):
            return []

        sorted_items = sorted(
            data.items(),
            key=lambda x: float(x[1]) if isinstance(x[1], (int, float)) else 0,
            reverse=True
        )

        return sorted_items[:n]


def run_meta_analysis(
    network: Any,
    include_centralities: bool = True,
    include_communities: bool = True,
    include_statistics: bool = True,
    include_path_based: bool = False,
    include_advanced: bool = False,
    wf_improved: bool = True,
    print_summary: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to run comprehensive multilayer network analysis.

    This is a high-level function that creates a MetaFlowReport instance,
    runs all requested analyses, and optionally prints a summary.

    Args:
        network: py3plex multi_layer_network object
        include_centralities: Whether to compute centrality measures. Default: True.
                             Always includes degree-based and eigenvector-based measures.
        include_communities: Whether to run community detection. Default: True.
        include_statistics: Whether to compute network statistics. Default: True.
        include_path_based: Include path-based centralities (betweenness, closeness).
                           COMPUTATIONALLY EXPENSIVE. Default: False (skipped).
        include_advanced: Include advanced measures (HITS, communicability, k-core).
                         COMPUTATIONALLY EXPENSIVE. Default: False (skipped).
        wf_improved: For closeness centrality, use Wasserman-Faust improved scaling.
                    Default: True.
        print_summary: Whether to print a summary of results. Default: True.
        **kwargs: Additional arguments passed to run_all_analyses

    Returns:
        Dictionary containing all analysis results with keys:
        - 'centralities': dict of centrality measures (if include_centralities=True)
        - 'communities': dict of community detection results (if include_communities=True)
        - 'statistics': dict of network statistics (if include_statistics=True)

    Example:
        >>> from py3plex.core import multinet
        >>> from py3plex.algorithms.meta_flow_report import run_meta_analysis
        >>>
        >>> network = multinet.multi_layer_network(directed=False)
        >>> network.add_edges([
        ...     ['A', 'L1', 'B', 'L1', 1],
        ...     ['B', 'L1', 'C', 'L1', 1],
        ... ], input_type='list')
        >>>
        >>> # Fast analysis (degree and eigenvector centralities only)
        >>> results = run_meta_analysis(network)
        >>>
        >>> # Full analysis (includes expensive path-based measures)
        >>> results_full = run_meta_analysis(network, include_path_based=True, include_advanced=True)

    Note:
        By default, only FAST centrality measures are computed. Path-based and
        advanced measures require explicit opt-in via include_path_based=True
        and include_advanced=True flags.
    """
    report = MetaFlowReport(network)

    # Pass wf_improved through to centrality computation
    kwargs['wf_improved'] = wf_improved

    results = report.run_all_analyses(
        include_centralities=include_centralities,
        include_communities=include_communities,
        include_statistics=include_statistics,
        include_path_based=include_path_based,
        include_advanced=include_advanced,
        **kwargs
    )

    if print_summary:
        report.print_summary(results)

    return results


# Public API
__all__ = [
    'MetaFlowReport',
    'run_meta_analysis',
]
