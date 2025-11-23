# Wrappers module for py3plex
# Provides high-level interfaces and integrations

# R interoperability - import main functions for easy access
try:
    from py3plex.wrappers.r_interop import (
        export_adjacency,
        export_edgelist,
        export_graph_data,
        export_nodelist,
        get_layer_names,
        get_network_stats,
        to_igraph_for_r,
        to_r_igraph,
    )

    __all__ = [
        "to_igraph_for_r",
        "to_r_igraph",
        "export_edgelist",
        "export_nodelist",
        "export_graph_data",
        "export_adjacency",
        "get_layer_names",
        "get_network_stats",
    ]
except ImportError:
    # R interop dependencies not available
    __all__ = []
