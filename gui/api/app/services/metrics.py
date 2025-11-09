"""
Centrality metrics computation service
"""
from app.services.io import get_graph
import networkx as nx
import logging

logger = logging.getLogger(__name__)


def compute_centrality(graph_id: str, metrics: list, layers: list = None):
    """Compute centrality metrics"""
    entry = get_graph(graph_id)
    if not entry:
        raise ValueError(f"Graph {graph_id} not found")
    
    graph = entry['graph']
    results = {}
    
    for metric in metrics:
        logger.info(f"Computing {metric} centrality for graph {graph_id}")
        
        try:
            if metric == "degree":
                centrality = dict(graph.degree())
            elif metric == "betweenness":
                centrality = nx.betweenness_centrality(graph)
            elif metric == "closeness":
                centrality = nx.closeness_centrality(graph)
            elif metric == "eigenvector":
                try:
                    centrality = nx.eigenvector_centrality(graph, max_iter=100)
                except:
                    centrality = nx.eigenvector_centrality_numpy(graph)
            elif metric == "pagerank":
                centrality = nx.pagerank(graph)
            else:
                continue
            
            # Convert to list of tuples for JSON serialization
            results[metric] = [
                {"node": str(node), "value": float(value)}
                for node, value in sorted(centrality.items(), key=lambda x: x[1], reverse=True)
            ]
        except Exception as e:
            logger.error(f"Error computing {metric}: {e}")
            results[metric] = {"error": str(e)}
    
    return results
