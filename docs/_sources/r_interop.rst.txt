R Interoperability Guide
=========================

This guide shows how to use py3plex from R via the **reticulate** package, enabling R users (especially those familiar with igraph or MLnet) to leverage py3plex's multilayer network capabilities.

.. contents:: Table of Contents
   :local:
   :depth: 2

Why Use py3plex from R?
------------------------

py3plex provides specialized multilayer network analysis that complements R's igraph package:

* **Native multilayer support** - Layer-aware algorithms and statistics
* **Specialized visualizations** - Diagonal projection for large multilayer networks
* **Seamless conversion** - Export to R igraph format for further analysis
* **Rich ecosystem** - Combine py3plex multilayer capabilities with R's statistical tools

Prerequisites
-------------

Install required packages:

.. code-block:: R

    # In R
    install.packages("reticulate")
    install.packages("igraph")

.. code-block:: bash

    # In terminal/shell
    pip install git+https://github.com/SkBlaz/py3plex.git
    pip install python-igraph

Quick Start: Simple Use Case with Centrality
---------------------------------------------

This example demonstrates creating a multilayer social network, converting it to igraph, and computing centrality measures in R.

Complete R Workflow
~~~~~~~~~~~~~~~~~~~

.. code-block:: R

    library(reticulate)
    library(igraph)
    
    # Import py3plex modules
    py3plex <- import("py3plex")
    r_interop <- import("py3plex.wrappers.r_interop")
    
    # Create a multilayer social network
    # Two layers: Facebook and Twitter
    net <- py3plex$multi_layer_network()
    
    # Add nodes
    net$add_nodes(list(
      list(source='Alice', type='facebook'),
      list(source='Bob', type='facebook'),
      list(source='Charlie', type='facebook'),
      list(source='Alice', type='twitter'),
      list(source='Bob', type='twitter'),
      list(source='Diana', type='twitter')
    ))
    
    # Add edges (connections within each platform)
    net$add_edges(list(
      list(source='Alice', target='Bob', 
           source_type='facebook', target_type='facebook', weight=0.8),
      list(source='Bob', target='Charlie', 
           source_type='facebook', target_type='facebook', weight=0.6),
      list(source='Alice', target='Bob', 
           source_type='twitter', target_type='twitter', weight=0.9),
      list(source='Bob', target='Diana', 
           source_type='twitter', target_type='twitter', weight=0.7)
    ))
    
    # Convert to igraph for R analysis (union mode merges all layers)
    g <- r_interop$to_igraph_for_r(net, mode='union')
    
    # Now use R's igraph functions for centrality analysis
    print("=== Network Statistics ===")
    print(paste("Vertices:", vcount(g)))
    print(paste("Edges:", ecount(g)))
    
    # Compute centrality measures
    print("\n=== Centrality Measures ===")
    
    # Degree centrality
    deg <- degree(g)
    print("\nDegree centrality:")
    print(sort(deg, decreasing=TRUE))
    
    # Betweenness centrality
    between <- betweenness(g)
    print("\nBetweenness centrality:")
    print(sort(between, decreasing=TRUE))
    
    # Closeness centrality
    close <- closeness(g)
    print("\nCloseness centrality:")
    print(sort(close, decreasing=TRUE))
    
    # PageRank
    pr <- page_rank(g)$vector
    print("\nPageRank:")
    print(sort(pr, decreasing=TRUE))
    
    # Visualize the network
    plot(g, 
         vertex.size=deg*5,           # Size by degree
         vertex.label=V(g)$name,
         edge.width=E(g)$weight*2,    # Width by weight
         main="Multilayer Social Network")

Expected Output
~~~~~~~~~~~~~~~

.. code-block:: text

    === Network Statistics ===
    [1] "Vertices: 6"
    [1] "Edges: 4"
    
    === Centrality Measures ===
    
    Degree centrality:
    ('Bob', 'facebook')     2
    ('Alice', 'facebook')   1
    ('Charlie', 'facebook') 1
    ('Bob', 'twitter')      2
    ('Alice', 'twitter')    1
    ('Diana', 'twitter')    1
    
    Betweenness centrality:
    ('Bob', 'facebook')     2.0
    ('Bob', 'twitter')      2.0
    ('Alice', 'facebook')   0.0
    ...

This demonstrates how py3plex enables you to:

1. Create complex multilayer networks in Python
2. Export them to R igraph format
3. Use all R igraph centrality functions
4. Visualize and analyze with R's rich statistical tools

Core Functions
--------------

to_igraph_for_r()
~~~~~~~~~~~~~~~~~

Convert py3plex network to igraph format optimized for R.

.. code-block:: R

    # Union mode: Merge all layers (recommended for most use cases)
    g <- r_interop$to_igraph_for_r(net, mode='union')
    
    # Multiplex mode: Preserve layer structure
    g <- r_interop$to_igraph_for_r(net, mode='multiplex')
    
    # Extract specific layer only
    g_facebook <- r_interop$to_igraph_for_r(net, layer='facebook')

**Parameters:**

* ``mode`` - How to handle layers: ``'union'`` (merge), ``'multiplex'`` (preserve), ``'intersection'`` (common edges)
* ``layer`` - Extract specific layer (overrides mode)

export_edgelist()
~~~~~~~~~~~~~~~~~

Export edges as R data frame compatible structure.

.. code-block:: R

    # Get edge list
    edges <- r_interop$export_edgelist(net, include_attributes=TRUE)
    
    # Convert to R data frame
    edges_df <- do.call(rbind, lapply(edges, function(e) {
      data.frame(
        src = e$src,
        dst = e$dst,
        src_layer = e$src_layer,
        dst_layer = e$dst_layer,
        weight = ifelse(is.null(e$weight), 1.0, e$weight),
        stringsAsFactors = FALSE
      )
    }))
    
    # Analyze with R
    print(head(edges_df))
    print(summary(edges_df$weight))

export_nodelist()
~~~~~~~~~~~~~~~~~

Export nodes as R data frame compatible structure.

.. code-block:: R

    # Get node list
    nodes <- r_interop$export_nodelist(net, include_attributes=TRUE)
    
    # Convert to R data frame
    nodes_df <- do.call(rbind, lapply(nodes, function(n) {
      as.data.frame(n, stringsAsFactors = FALSE)
    }))
    
    print(head(nodes_df))

export_adjacency()
~~~~~~~~~~~~~~~~~~

Export adjacency matrix for matrix operations in R.

.. code-block:: R

    # Get adjacency matrix
    adj_list <- r_interop$export_adjacency(net, mode='union')
    
    # Convert to R matrix
    n <- length(adj_list)
    adj_matrix <- matrix(unlist(adj_list), nrow=n, byrow=TRUE)
    
    # Matrix operations
    eigenvalues <- eigen(adj_matrix)$values
    print(paste("Largest eigenvalue:", max(Re(eigenvalues))))

get_network_stats()
~~~~~~~~~~~~~~~~~~~

Get comprehensive network statistics.

.. code-block:: R

    # Get statistics
    stats <- r_interop$get_network_stats(net)
    
    print(paste("Nodes:", stats$num_nodes))
    print(paste("Edges:", stats$num_edges))
    print(paste("Layers:", stats$num_layers))
    print(paste("Directed:", stats$directed))

Advanced Examples
-----------------

Example 1: Layer-by-Layer Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Analyze each layer separately:

.. code-block:: R

    library(reticulate)
    library(igraph)
    
    py3plex <- import("py3plex")
    r_interop <- import("py3plex.wrappers.r_interop")
    
    # Create multilayer network (code from Quick Start)
    net <- py3plex$multi_layer_network()
    # ... add nodes and edges ...
    
    # Get layer names
    layers <- r_interop$get_layer_names(net)
    
    # Analyze each layer
    for (layer in layers) {
      cat(sprintf("\n=== Layer: %s ===\n", layer))
      
      # Extract layer-specific graph
      g_layer <- r_interop$to_igraph_for_r(net, layer=layer)
      
      # Compute centrality for this layer
      deg <- degree(g_layer)
      cat(sprintf("Average degree: %.2f\n", mean(deg)))
      
      # Community detection
      comm <- cluster_louvain(g_layer)
      cat(sprintf("Communities: %d\n", length(comm)))
    }

Example 2: Combining with R Statistical Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use R's statistical tools on network data:

.. code-block:: R

    library(reticulate)
    library(igraph)
    
    py3plex <- import("py3plex")
    r_interop <- import("py3plex.wrappers.r_interop")
    
    # Create network
    net <- py3plex$multi_layer_network()
    # ... build network ...
    
    # Export to igraph
    g <- r_interop$to_igraph_for_r(net, mode='union')
    
    # Compute multiple centrality measures
    deg <- degree(g)
    between <- betweenness(g)
    close <- closeness(g)
    
    # Create data frame for analysis
    centrality_df <- data.frame(
      node = V(g)$name,
      degree = deg,
      betweenness = between,
      closeness = close
    )
    
    # Statistical analysis
    print("=== Centrality Correlations ===")
    print(cor(centrality_df[, c("degree", "betweenness", "closeness")]))
    
    # Regression analysis
    model <- lm(betweenness ~ degree + closeness, data=centrality_df)
    print(summary(model))
    
    # Visualization
    library(ggplot2)
    ggplot(centrality_df, aes(x=degree, y=betweenness)) +
      geom_point() +
      geom_smooth(method="lm") +
      labs(title="Degree vs Betweenness Centrality",
           x="Degree", y="Betweenness")

Example 3: Time Series of Multilayer Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Analyze temporal evolution:

.. code-block:: R

    library(reticulate)
    library(igraph)
    
    py3plex <- import("py3plex")
    r_interop <- import("py3plex.wrappers.r_interop")
    
    # Create networks for different time points
    time_points <- c("2020", "2021", "2022")
    networks <- list()
    
    for (t in time_points) {
      # Load or create network for this time point
      net <- py3plex$multi_layer_network()
      # ... load data for time t ...
      
      # Convert and store
      networks[[t]] <- r_interop$to_igraph_for_r(net, mode='union')
    }
    
    # Compare network evolution
    metrics <- data.frame(
      time = time_points,
      nodes = sapply(networks, vcount),
      edges = sapply(networks, ecount),
      density = sapply(networks, graph.density),
      clustering = sapply(networks, transitivity)
    )
    
    print(metrics)
    
    # Plot evolution
    library(ggplot2)
    ggplot(metrics, aes(x=time, y=density, group=1)) +
      geom_line() +
      geom_point() +
      labs(title="Network Density Over Time")

Working with CSV Files
----------------------

Load multilayer network data from CSV:

.. code-block:: R

    library(reticulate)
    library(igraph)
    
    py3plex <- import("py3plex")
    r_interop <- import("py3plex.wrappers.r_interop")
    
    # Create network
    net <- py3plex$multi_layer_network()
    
    # Load from CSV file
    # CSV format: source,source_type,target,target_type,weight
    net$load_network("network_data.csv", 
                     input_type="multiedgelist", 
                     directed=FALSE)
    
    # Convert and analyze
    g <- r_interop$to_igraph_for_r(net, mode='union')
    
    # Get statistics
    stats <- r_interop$get_network_stats(net)
    print(stats)

Integration with MLnet
----------------------

For users familiar with MLnet (R package for multilayer networks):

.. code-block:: R

    library(reticulate)
    library(igraph)
    # library(multinet)  # If you have MLnet installed
    
    py3plex <- import("py3plex")
    r_interop <- import("py3plex.wrappers.r_interop")
    
    # Create py3plex network
    net <- py3plex$multi_layer_network()
    # ... build network ...
    
    # Export layer-by-layer for MLnet compatibility
    layers <- r_interop$get_layer_names(net)
    
    for (layer in layers) {
      # Get igraph for this layer
      g <- r_interop$to_igraph_for_r(net, layer=layer)
      
      # Save as GraphML (MLnet compatible)
      write_graph(g, sprintf("layer_%s.graphml", layer), format="graphml")
    }
    
    # Now you can import these layers into MLnet
    # Or continue using igraph functions directly

Troubleshooting
---------------

Python Module Not Found
~~~~~~~~~~~~~~~~~~~~~~~~

If you get ``ModuleNotFoundError: No module named 'py3plex'``:

.. code-block:: R

    library(reticulate)
    
    # Check which Python reticulate is using
    py_config()
    
    # Install py3plex in that Python
    py_install("git+https://github.com/SkBlaz/py3plex.git")

igraph Import Error
~~~~~~~~~~~~~~~~~~~

If ``to_igraph_for_r()`` fails with import error:

.. code-block:: bash

    # Install python-igraph
    pip install python-igraph

Conversion Issues
~~~~~~~~~~~~~~~~~

If conversion produces unexpected results:

.. code-block:: R

    # Check network statistics first
    stats <- r_interop$get_network_stats(net)
    print(stats)
    
    # Try different modes
    g_union <- r_interop$to_igraph_for_r(net, mode='union')
    g_multiplex <- r_interop$to_igraph_for_r(net, mode='multiplex')
    
    print(paste("Union:", vcount(g_union), "nodes"))
    print(paste("Multiplex:", vcount(g_multiplex), "nodes"))

Performance Tips
----------------

For Large Networks
~~~~~~~~~~~~~~~~~~

.. code-block:: R

    # Use union mode for faster processing
    g <- r_interop$to_igraph_for_r(net, mode='union')
    
    # For very large networks, export to file instead
    # Then use igraph's file reading functions

Memory Management
~~~~~~~~~~~~~~~~~

.. code-block:: R

    # Clear Python objects when done
    rm(net)
    gc()
    
    # Or restart Python session
    py_run_string("import gc; gc.collect()")

Next Steps
----------

- :doc:`networkx_interop` - NetworkX integration for Python workflows
- :doc:`basic_usage_analysis` - Network analysis methods
- :doc:`community_detection` - Community detection algorithms  
- :doc:`visualization_guide` - Visualization options

For Python examples with R code snippets, see `examples/r_interop_example.py <https://github.com/SkBlaz/py3plex/blob/main/examples/r_interop_example.py>`_ in the GitHub repository.
