"""
Community detection service
"""
from app.services.io import get_graph
import networkx as nx
import logging

logger = logging.getLogger(__name__)


def compute_community(graph_id: str, algorithm: str = "louvain", 
                      resolution: float = 1.0, seed: int = 42):
    """Compute community detection"""
    entry = get_graph(graph_id)
    if not entry:
        raise ValueError(f"Graph {graph_id} not found")
    
    graph = entry['graph']
    
    # Convert to undirected if needed
    if graph.is_directed():
        graph = graph.to_undirected()
    
    communities = {}
    
    try:
        if algorithm == "louvain":
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(graph, resolution=resolution, random_state=seed)
                communities = partition
            except ImportError:
                logger.warning("python-louvain not installed, using greedy modularity")
                algorithm = "greedy_modularity"
        
        if algorithm == "greedy_modularity":
            from networkx.algorithms import community as nx_community
            community_generator = nx_community.greedy_modularity_communities(graph)
            communities = {}
            for i, comm in enumerate(community_generator):
                for node in comm:
                    communities[node] = i
        
        elif algorithm == "label_propagation":
            from networkx.algorithms import community as nx_community
            community_generator = nx_community.label_propagation_communities(graph)
            communities = {}
            for i, comm in enumerate(community_generator):
                for node in comm:
                    communities[node] = i
        
        # Convert to result format
        result = {
            "algorithm": algorithm,
            "num_communities": len(set(communities.values())),
            "communities": [
                {"node": str(node), "community": int(comm)}
                for node, comm in communities.items()
            ]
        }
        
        logger.info(f"Found {result['num_communities']} communities using {algorithm}")
        return result
        
    except Exception as e:
        logger.error(f"Error computing communities: {e}", exc_info=True)
        raise
