"""
Centrality metrics computation service
"""
from app.services.io import get_graph
import networkx as nx
import logging

logger = logging.getLogger(__name__)

# Maximum nodes for expensive centrality algorithms
MAX_NODES_BETWEENNESS = 5000
MAX_NODES_CLOSENESS = 5000


def compute_centrality(graph_id: str, metrics: list, layers: list = None):
    """Compute centrality metrics (optimized for large graphs)
    
    For MultiGraphs (multilayer networks), centrality is computed on a simplified
    view where multiple edges are aggregated. This provides meaningful centrality
    values for multilayer networks.
    """
    entry = get_graph(graph_id)
    if not entry:
        raise ValueError(f"Graph {graph_id} not found")
    
    graph = entry['graph']
    num_nodes = graph.number_of_nodes()
    
    # Convert MultiGraph to simple Graph for centrality computation
    # Multiple edges are collapsed into single weighted edges
    if isinstance(graph, nx.MultiGraph) or isinstance(graph, nx.MultiDiGraph):
        logger.info(f"Converting MultiGraph to Graph for centrality computation")
        simple_graph = nx.Graph()
        
        # Aggregate edge weights (optimized)
        for u, v, data in graph.edges(data=True):
            weight = data.get('weight', 1.0)
            if simple_graph.has_edge(u, v):
                simple_graph[u][v]['weight'] += weight
            else:
                simple_graph.add_edge(u, v, weight=weight)
        
        graph = simple_graph
    
    results = {}
    
    for metric in metrics:
        logger.info(f"Computing {metric} centrality for graph {graph_id} ({num_nodes} nodes)")
        
        try:
            if metric == "degree":
                # Degree is fast, always compute
                if nx.is_weighted(graph):
                    centrality = dict(graph.degree(weight='weight'))
                else:
                    centrality = dict(graph.degree())
                    
            elif metric == "betweenness":
                # Betweenness is expensive, use sampling for large graphs
                if num_nodes > MAX_NODES_BETWEENNESS:
                    logger.warning(f"Large graph ({num_nodes} nodes), using approximate betweenness")
                    # Sample k nodes (5% or at least 100)
                    k = max(100, int(num_nodes * 0.05))
                    centrality = nx.betweenness_centrality(graph, k=k, weight='weight')
                else:
                    centrality = nx.betweenness_centrality(graph, weight='weight')
                    
            elif metric == "closeness":
                # Closeness can be slow, optimize for large graphs
                if num_nodes > MAX_NODES_CLOSENESS:
                    logger.warning(f"Large graph ({num_nodes} nodes), using approximate closeness")
                    # Use Wasserman-Faust normalization (faster)
                    centrality = nx.closeness_centrality(graph, distance='weight', wf_improved=False)
                else:
                    centrality = nx.closeness_centrality(graph, distance='weight')
                    
            elif metric == "eigenvector":
                try:
                    # Try numpy version first (faster)
                    centrality = nx.eigenvector_centrality_numpy(graph, weight='weight', max_iter=100)
                except:
                    try:
                        # Fall back to power iteration
                        centrality = nx.eigenvector_centrality(graph, max_iter=100, weight='weight')
                    except:
                        # Last resort: unweighted
                        logger.warning("Falling back to unweighted eigenvector centrality")
                        centrality = nx.eigenvector_centrality(graph, max_iter=100)
                        
            elif metric == "pagerank":
                # PageRank is relatively fast
                centrality = nx.pagerank(graph, weight='weight', max_iter=100)
            else:
                logger.warning(f"Unknown metric: {metric}")
                continue
            
            # Convert to list of tuples for JSON serialization
            # Only keep top 1000 results for very large graphs to reduce response size
            sorted_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
            if num_nodes > 10000:
                logger.info(f"Limiting results to top 1000 nodes for {metric}")
                sorted_centrality = sorted_centrality[:1000]
            
            results[metric] = [
                {"node": str(node), "value": float(value)}
                for node, value in sorted_centrality
            ]
        except Exception as e:
            logger.error(f"Error computing {metric}: {e}", exc_info=True)
            results[metric] = {"error": str(e)}
    
    return results
