Case Study 1 — Social Multiplex Network
===================================================

.. admonition:: Case Study Template
   :class: note

   This case study provides a complete workflow template for social multiplex network 
   analysis. The structure and code patterns are production-ready and can be adapted 
   to your own datasets. Examples use representative synthetic data to demonstrate 
   the analysis pipeline.

.. admonition:: DSL in Case Studies
   :class: dsl-example

   This case study demonstrates DSL throughout the analysis workflow:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # 1. Quick exploratory analysis
       for platform in ["facebook", "twitter", "linkedin"]:
           stats = (
               Q.nodes()
                .from_layers(L[platform])
                .compute("degree", "clustering")
                .execute(network)
           )
           df = stats.to_pandas()
           print(f"{platform}: avg degree = {df['degree'].mean():.2f}")

       # 2. Find cross-platform influencers
       influencers = (
           Q.nodes()
            .from_layers(L["facebook"] + L["twitter"] + L["linkedin"])
            .where(degree__gt=50)
            .compute("betweenness_centrality")
            .order_by("-betweenness_centrality")
            .limit(20)
            .export_csv("influencers.csv")
            .execute(network)
       )

       # 3. Platform-specific analysis
       twitter_only = (
           Q.nodes()
            .from_layers(L["twitter"] - L["facebook"] - L["linkedin"])
            .compute("degree")
            .execute(network)
       )

   DSL enables rapid iteration in exploratory research!

Domain Context
--------------

Social media users often maintain multiple online identities across platforms (Facebook, Twitter, LinkedIn, Instagram). This creates a **social multiplex network** where:

* **Nodes** represent users
* **Layers** represent platforms
* **Intra-layer edges** are friendships/follows within a platform
* **Inter-layer edges** link the same user across platforms

**Research questions:**

1. How do user roles vary across platforms?
2. Are influential users consistent across layers, or platform-specific?
3. Do communities align across platforms or fragment differently?
4. What cross-layer patterns emerge (e.g., Twitter influencers who are Facebook novices)?

Dataset Structure
~~~~~~~~~~~~~~~~~

**Example dataset:** Multi-platform social network

* **Nodes:** ~5,000 users (some present on multiple platforms)
* **Layers:** 3 platforms (Facebook, Twitter, LinkedIn)
* **Edges:** ~20,000 connections
* **Attributes:** User demographics (age, location), timestamps

**Data format (edgelist):**

.. code-block:: text

    # Format: source, source_layer, target, target_layer, weight
    user_123, facebook, user_456, facebook, 1
    user_123, twitter, user_789, twitter, 1
    user_123, facebook, user_123, twitter, 1  # Inter-layer link

Loading the Data
----------------

Create and Load Network
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    # Create multilayer network
    network = multinet.multi_layer_network(directed=False)
    
    # Load from edgelist
    network.load_network('social_multiplex.edgelist', input_type='edgelist')
    
    # Verify structure
    print(f"Nodes: {network.number_of_nodes()}")
    print(f"Edges: {len(network.get_edges())}")
    print(f"Layers: {network.get_layers()}")
    
    # Basic statistics
    network.basic_stats()

Expected output:

.. code-block:: text

    Nodes: 5234
    Edges: 18976
    Layers: ['facebook', 'twitter', 'linkedin']

Full Analysis Pipeline
----------------------

Step 1: Exploratory Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start with layer-level statistics:

.. code-block:: python

    from py3plex.dsl import Q, L
    import pandas as pd
    
    # Collect statistics for each layer
    layer_summary = []
    
    for layer in ["facebook", "twitter", "linkedin"]:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree", "clustering")
             .execute(network)
        )
        df = result.to_pandas()
        
        layer_summary.append({
            'layer': layer,
            'nodes': result.count,
            'avg_degree': df['degree'].mean(),
            'max_degree': df['degree'].max(),
            'avg_clustering': df['clustering'].mean()
        })
    
    summary_df = pd.DataFrame(layer_summary)
    print(summary_df)

**Interpretation:** Compare layer densities and clustering to understand platform differences.

Step 2: Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Find communities using multilayer Louvain:

.. code-block:: python

    from py3plex.algorithms.community_detection import multilayer_louvain
    
    # Detect communities
    communities = multilayer_louvain.best_partition(network.core_network)
    
    # Add communities as node attributes
    for node, comm_id in communities.items():
        network.core_network.nodes[node]['community'] = comm_id
    
    # Count communities
    n_communities = len(set(communities.values()))
    print(f"Found {n_communities} communities")
    
    # Largest communities
    from collections import Counter
    community_sizes = Counter(communities.values())
    print("Top 5 communities by size:")
    for comm_id, size in community_sizes.most_common(5):
        print(f"  Community {comm_id}: {size} nodes")

Step 3: Centrality Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Identify influential users using multilayer PageRank:

.. code-block:: python

    from py3plex.algorithms.centrality_toolkit import multilayer_pagerank
    
    # Compute multilayer PageRank
    pagerank_scores = multilayer_pagerank(network.core_network)
    
    # Use DSL to find top influencers
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    df = result.to_pandas()
    df['pagerank'] = df['node_id'].map(pagerank_scores)
    
    # Top influencers
    top_influencers = df.nlargest(20, 'pagerank')
    print(top_influencers[['node_id', 'degree', 'betweenness_centrality', 'pagerank']])

Step 4: Cross-Layer Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Analyze how user importance varies across platforms:

.. code-block:: python

    # For each user, compute degree in each layer
    user_profiles = {}
    
    for layer in ["facebook", "twitter", "linkedin"]:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree")
             .execute(network)
        )
        df = result.to_pandas()
        
        for _, row in df.iterrows():
            user_id = row['node_id'][0]  # Extract base user ID
            if user_id not in user_profiles:
                user_profiles[user_id] = {}
            user_profiles[user_id][f"{layer}_degree"] = row['degree']
    
    # Convert to DataFrame
    profile_df = pd.DataFrame.from_dict(user_profiles, orient='index').fillna(0)
    
    # Find cross-layer imbalances
    profile_df['max_degree'] = profile_df.max(axis=1)
    profile_df['min_degree'] = profile_df.min(axis=1)
    profile_df['imbalance'] = profile_df['max_degree'] / (profile_df['min_degree'] + 1)
    
    # Users with high imbalance (platform specialists)
    specialists = profile_df.nlargest(10, 'imbalance')
    print("Platform specialists (high cross-layer imbalance):")
    print(specialists)

Step 5: Visualization
~~~~~~~~~~~~~~~~~~~~~

Create publication-ready visualizations:

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    import matplotlib.pyplot as plt
    
    # Visualize network with communities colored
    draw_multilayer_default(
        network.get_layers(),
        node_size=8,
        labels=True,
        background_shape="circle",
        scale_by_size=True,  # Scale nodes by degree
        display=True
    )
    
    plt.title("Social Multiplex Network - Community Structure")
    plt.savefig("social_multiplex_communities.png", dpi=300, bbox_inches='tight')

Key Findings (Template)
------------------------

Community Structure
~~~~~~~~~~~~~~~~~~~

**Observation:** Communities tend to form around shared topics or interests. Nodes with high inter-community connectivity (high betweenness) act as bridges between different social groups. The community structure often correlates with geographic or demographic factors in real social networks.

* **Cross-platform communities:** X% of users in same community across all layers
* **Platform-specific communities:** Y% of communities confined to single layer
* **Community alignment:** Normalized Mutual Information = Z

**Interpretation:** Cross-platform community alignment suggests that social structures persist across different communication channels, likely reflecting offline social relationships or shared interests. Platform-specific communities indicate specialized use cases (e.g., professional networking on LinkedIn vs. casual social interaction on Facebook).

Cross-Layer Roles
~~~~~~~~~~~~~~~~~

**Observation:** User roles vary significantly across platforms. A highly central user on one platform may be peripheral on another, reflecting different usage patterns, social contexts, or specialization. Cross-platform influencers (high centrality on multiple layers) are relatively rare but strategically important for information diffusion.

* **Consistent influencers:** N users with high centrality on all platforms
* **Platform specialists:** M users highly central on one platform only
* **Role switching:** Average centrality correlation across layers = ρ

**Interpretation:** [How do user strategies differ by platform?]

Pitfalls Encountered
--------------------

Data Cleaning Issues
~~~~~~~~~~~~~~~~~~~~

**Challenge:** User identity resolution across platforms

* Usernames differ across platforms
* Manual matching required for subset of users
* Missing links lead to underestimated cross-layer effects

**Solution:** Use email-based or profile-based matching when available

Performance Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Challenge:** Betweenness centrality computation slow for large networks

* O(n³) complexity becomes prohibitive for >10,000 nodes
* Consider sampling or approximation algorithms

**Solution:** Use degree or PageRank for large-scale analysis; reserve betweenness for focused subgraphs

Reproducibility
---------------

Code Repository
~~~~~~~~~~~~~~~

This analysis workflow is based on the examples in the repository. To reproduce similar analyses:

.. code-block:: bash

    # Clone repository
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    
    # Install dependencies
    pip install -e .
    
    # Run relevant examples
    uv run examples/05_communities/02_multilayer_detection.py
    uv run examples/03_dsl_v2/03_grouping_aggregation.py
    uv run examples/06_dynamics/02_multilayer_epidemic.py

Data Availability
~~~~~~~~~~~~~~~~~

**Synthetic data** for this case study is available in: ``examples/datasets/synthetic_social_multiplex.edgelist``

For real datasets, consider:

* **Twitter + Facebook:** Similar methodology can be applied to real datasets (subject to API access and data use agreements)
* **Academic multiplex:** DBLP + ArXiv coauthorship networks
* **Contact datasets:** See ``multilayer_datasets/`` directory

Summary
-------

This case study demonstrated:

1. **Data loading** from edgelist format
2. **Exploratory analysis** using DSL for layer statistics
3. **Community detection** with multilayer Louvain
4. **Centrality analysis** with multilayer PageRank
5. **Cross-layer pattern detection** (role switching, specialists)
6. **Visualization** for publication

**Key workflow:**

1. Load → 2. Explore → 3. Detect communities → 4. Compute centrality → 5. Analyze patterns → 6. Visualize

**Adapt this workflow to your own social multiplex datasets by:**

* Adjusting layer names
* Modifying centrality thresholds
* Adding domain-specific measures
* Customizing visualizations
