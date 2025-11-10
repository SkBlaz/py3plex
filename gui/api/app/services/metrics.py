"""
Centrality metrics computation service
"""
from app.services.io import get_graph
import networkx as nx
import logging

logger = logging.getLogger(__name__)


def compute_centrality(graph_id: str, metrics: list, layers: list = None):
    """Compute centrality metrics
    
    For MultiGraphs (multilayer networks), centrality is computed on a simplified
    view where multiple edges are aggregated. This provides meaningful centrality
    values for multilayer networks.
    """
    entry = get_graph(graph_id)
    if not entry:
        raise ValueError(f"Graph {graph_id} not found")
    
    graph = entry['graph']
    
    # Convert MultiGraph to simple Graph for centrality computation
    # Multiple edges are collapsed into single weighted edges
    if isinstance(graph, nx.MultiGraph) or isinstance(graph, nx.MultiDiGraph):
        logger.info(f"Converting MultiGraph to Graph for centrality computation")
        simple_graph = nx.Graph()
        
        # Aggregate edge weights
        for u, v, data in graph.edges(data=True):
            weight = data.get('weight', 1.0)
            if simple_graph.has_edge(u, v):
                simple_graph[u][v]['weight'] += weight
            else:
                simple_graph.add_edge(u, v, weight=weight)
        
        graph = simple_graph
    
    results = {}
    
    for metric in metrics:
        logger.info(f"Computing {metric} centrality for graph {graph_id}")
        
        try:
            if metric == "degree":
                # For degree centrality, use weighted degree if weights present
                if nx.is_weighted(graph):
                    centrality = dict(graph.degree(weight='weight'))
                else:
                    centrality = dict(graph.degree())
            elif metric == "betweenness":
                centrality = nx.betweenness_centrality(graph, weight='weight')
            elif metric == "closeness":
                centrality = nx.closeness_centrality(graph, distance='weight')
            elif metric == "eigenvector":
                try:
                    centrality = nx.eigenvector_centrality(graph, max_iter=100, weight='weight')
                except:
                    try:
                        centrality = nx.eigenvector_centrality_numpy(graph, weight='weight')
                    except:
                        # Fall back to unweighted if that fails too
                        centrality = nx.eigenvector_centrality(graph, max_iter=100)
            elif metric == "pagerank":
                centrality = nx.pagerank(graph, weight='weight')
            else:
                continue
            
            # Convert to list of tuples for JSON serialization
            results[metric] = [
                {"node": str(node), "value": float(value)}
                for node, value in sorted(centrality.items(), key=lambda x: x[1], reverse=True)
            ]
        except Exception as e:
            logger.error(f"Error computing {metric}: {e}", exc_info=True)
            results[metric] = {"error": str(e)}
    
    return results
