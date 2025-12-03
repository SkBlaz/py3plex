Chapter 1: Your First Five Minutes
===================================

*In which we create a multilayer network from scratch, visualize it, and discover what makes multilayer analysis different from single-layer approaches.*

----

Every journey into multilayer network analysis begins with a simple question: *What happens when relationships aren't all the same?*

Traditional network analysis treats every connection equally—a friend is a friend, a colleague is a colleague, and the tool you use doesn't care which is which. But real-world systems are messier. The same people might be connected in fundamentally different ways: as friends *and* as colleagues, as family members *and* as business partners, as collaborators on one project *and* competitors on another.

py3plex exists because these distinctions matter. This quickstart will show you how, in just five minutes.

The Scenario
------------

Imagine you have data about a small group of people and their relationships across two contexts: **friends** (personal relationships) and **colleagues** (professional relationships). You want to understand:

* Who is well-connected in each context?
* Who appears in both contexts (and might bridge personal and professional networks)?
* Are the friendship and colleague networks similarly structured?

This is a classic multilayer network analysis scenario. Let's solve it with py3plex.

Installation
------------

Install py3plex from GitHub:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

If you prefer Docker, see :doc:`installation` for container-based setup.

Hello World: Your First Multilayer Network
-------------------------------------------

Create a simple multilayer network with just a few lines of code:

.. code-block:: python

    from py3plex.core import multinet

    # Create a new multilayer network
    network = multinet.multi_layer_network()

    # Add edges (nodes are created automatically)
    # Format: [source_node, source_layer, target_node, target_layer, weight]
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
        ['Bob', 'colleagues', 'Dave', 'colleagues', 1]
    ], input_type="list")

    # Display basic statistics
    network.basic_stats()

**Output:**

.. code-block:: text

    Number of nodes: 6
    Number of edges: 4
    Number of unique nodes (as node-layer tuples): 6
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer 'friends': 3 nodes
      Layer 'colleagues': 3 nodes

**What just happened?** We created a multilayer network with 2 layers. Notice that ``basic_stats()`` reports both **6 nodes** (counting each person in each layer separately) and **4 unique node IDs** (counting each person once regardless of how many layers they appear in). This distinction is fundamental: Alice appears in both layers, but Alice-in-friends and Alice-in-colleagues are different **node-layer pairs**.

**Sanity check:** The "Nodes per layer" section confirms that each layer has 3 nodes. If you see layers with 0 or 1 nodes, you likely have a data loading issue. If the unique node count seems wrong, check your layer naming for consistency.

Visualize Your Network
----------------------

Create a simple visualization:

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Simple visualization
    draw_multilayer_default([network], display=True)

This creates a visual plot showing your multilayer network with nodes colored by layer.

**What you should see:** Nodes from the "friends" layer will be one color, nodes from the "colleagues" layer another. Edges connect nodes within and across layers. This immediate visual feedback helps you verify that your data was loaded correctly—if layers are missing or edges seem wrong, you'll often spot it in the visualization before you spot it in statistics.

Basic Analysis
--------------

Compute some basic network statistics:

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # How dense is each layer?
    friends_density = mls.layer_density(network, 'friends')
    colleagues_density = mls.layer_density(network, 'colleagues')
    
    print(f"Friends layer density: {friends_density:.3f}")
    print(f"Colleagues layer density: {colleagues_density:.3f}")
    
    # How active is Bob across layers?
    bob_activity = mls.node_activity(network, 'Bob')
    print(f"Bob's activity: {bob_activity:.3f}")

**Output:**

.. code-block:: text

    Friends layer density: 0.667
    Colleagues layer density: 0.667
    Bob's activity: 1.000

**Interpreting the results:**

* **Density 0.667** means 2 out of 3 possible edges exist in each layer (with 3 nodes, a complete graph has 3 edges; we have 2). This is a fairly dense small network—real-world networks are typically much sparser (density < 0.1).

* **Bob's activity 1.000** means Bob appears in 100% of layers (both of them). He's a "bridge" person who connects both contexts. Compare this to Carol (activity 0.5, only in friends) or Dave (activity 0.5, only in colleagues). High-activity nodes are often interesting for understanding cross-layer dynamics.

Query with DSL (SQL-like)
--------------------------

Use SQL-like queries for intuitive network analysis:

.. code-block:: python

    from py3plex.dsl import execute_query
    
    # Find nodes with high degree
    result = execute_query(network, 'SELECT nodes WHERE degree > 1')
    print(f"Found {result['count']} high-degree nodes")
    
    # Get nodes in a specific layer
    result = execute_query(network, 'SELECT nodes WHERE layer="friends"')
    print(f"Friends layer has {result['count']} nodes")
    
    # Compute centrality
    result = execute_query(network, 
        'SELECT nodes WHERE layer="friends" COMPUTE betweenness_centrality')

**What this gives you:** The DSL is particularly useful when you're exploring data interactively. Instead of chaining Python method calls, you can express queries in a readable, declarative style. The ``COMPUTE`` clause adds computed metrics to the result, making it easy to filter and analyze in one step.
    
See :doc:`../user_guide/dsl` for comprehensive DSL documentation.

What You Learned
----------------

Let's pause and take stock. In five minutes, you've learned the core mental model that distinguishes py3plex from traditional network tools:

1. **Node-layer pairs are fundamental.** In a multilayer network, a node like "Bob" isn't just a single entity—it's represented as ``('Bob', 'friends')`` and ``('Bob', 'colleagues')`` separately. This allows the same person to have different attributes and connections in different contexts. This representation isn't a limitation; it's what makes multilayer analysis possible.

2. **Layers preserve context.** Each layer represents a different type of relationship or interaction mode. Unlike tools that flatten everything into one graph, py3plex keeps layers distinct throughout your analysis. When you compute statistics or detect communities, the layer structure is always available.

3. **py3plex extends NetworkX.** Under the hood, py3plex uses NetworkX graphs. This means you can use any NetworkX algorithm on your multilayer network—computing PageRank, finding shortest paths, or any of hundreds of other algorithms—while py3plex adds multilayer-specific capabilities on top.

4. **Multilayer statistics reveal hidden patterns.** Metrics like node activity (who appears in multiple contexts?), layer density (how connected is each context?), and edge overlap (do the same relationships appear in both contexts?) help you understand how layers relate to each other. These insights are invisible to single-layer tools.

What's Next?
------------

Congratulations! You've created your first multilayer network and taken the first steps toward understanding its structure.

In :doc:`tutorial_10min`, we'll expand on these foundations with a more comprehensive walkthrough: loading real data from files, computing centrality measures, detecting communities that span layers, generating random walks for embeddings, and creating publication-ready visualizations.

**Ready to continue?** Move on to :doc:`tutorial_10min` for the full 10-minute tutorial.

**Need to install first?** See :doc:`installation` for complete setup instructions including optional dependencies.

**Something not working?** Check :doc:`common_issues` for solutions to common problems.

**Prefer to explore?** Browse the ``examples/`` directory for 50+ working examples covering every major feature.

----

*Next chapter: :doc:`tutorial_10min` — where we build complete analysis pipelines from loading to visualization.*
