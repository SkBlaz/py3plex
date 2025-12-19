Key Use Cases
=============

py3plex models systems where the same entities interact through many
relationship types (layers). Each node may appear in multiple layers, and
interlayer edges let you model transfers or couplings between contexts. Below
are common domains, what the layers represent, and the kinds of questions you
can answer.

Social Networks
---------------

Layers represent communication channels or contexts for the same people:

* Friendship, family, and professional connections
* Online interactions: mentions, retweets, replies
* Communication channels: email, chat, video calls

**Example applications:**

* Identifying influential users across multiple platforms
* Detecting communities that span different relationship types
* Predicting information diffusion through multiple channels

.. code-block:: python

    from collections import Counter
    from py3plex.core import multinet

    # Example: Multi-platform social network
    network = multinet.multi_layer_network()
    # List input: [source, source_layer, target, target_layer, weight]
    network.add_edges([
        ['Alice', 'twitter', 'Bob', 'twitter', 1],
        ['Alice', 'linkedin', 'Bob', 'linkedin', 1],
        ['Bob', 'twitter', 'Carol', 'twitter', 1],
    ], input_type="list")
    
    # Find users present in more than one layer
    layer_counts = Counter(node for node, layer in network.get_nodes())
    active_users = [node for node, count in layer_counts.items() if count > 1]
    print(active_users)

Biological Networks
-------------------

Layers capture different biological interaction types:

* Protein-protein interactions (physical binding)
* Gene regulatory networks (transcriptional control)
* Metabolic pathways (biochemical reactions)
* Signaling cascades

**Example applications:**

* Drug target identification across interaction types
* Disease gene prioritization using multiple evidence sources
* Pathway enrichment analysis

.. code-block:: python

    # Example: Multi-omics biological network
    # Protein-protein interactions + gene regulation
    from py3plex.core import multinet
    from py3plex.dsl import execute_query

    network = multinet.multi_layer_network()
    
    # Physical interactions
    network.add_edge('TP53', 'ppi', 'MDM2', 'ppi')

    # Regulatory interactions
    network.add_edge('TP53', 'regulation', 'CDKN1A', 'regulation')

    # Compute centrality within the regulatory layer
    result = execute_query(network,
        'SELECT nodes WHERE layer="regulation" '
        'COMPUTE betweenness_centrality'
    )

Transportation Networks
-----------------------

Layers represent travel modes and transfers between them:

* Road networks
* Public transit (bus, metro, train)
* Air travel
* Pedestrian paths

**Example applications:**

* Optimizing multimodal route planning
* Identifying critical transfer points
* Analyzing resilience to disruptions

.. code-block:: python

    # Example: Multimodal city transportation
    from py3plex.core import multinet

    network = multinet.multi_layer_network()
    
    # Different transportation modes
    network.add_edge('StationA', 'metro', 'StationB', 'metro')
    network.add_edge('StationA', 'bus', 'StationC', 'bus')
    network.add_edge('StationB', 'metro', 'StationC', 'metro')
    
    # Inter-layer connections (transfers)
    network.add_edge('StationA', 'metro', 'StationA', 'bus', 
                     type='interlayer')
    
    # Identify busy transfer points (degree > 2 across all modes)
    busy_stations = [
        node for node in network.get_nodes()
        if network.core_network.degree(node) > 2
    ]

Knowledge Graphs
----------------

Layers separate relation types between entities:

* Entity types: people, organizations, locations, concepts
* Relation types: employment, location, authorship, citation

Keeping relations in distinct layers preserves meaning (employment vs. location)
while still allowing cross-layer queries.

**Example applications:**

* Entity linking and disambiguation
* Knowledge graph completion
* Question answering over structured data

Scientific Collaboration
------------------------

Layers represent collaboration contexts:

* Joint publications
* Grant collaborations
* Conference attendance
* Social media interactions

**Example applications:**

* Identifying interdisciplinary researchers
* Detecting emerging research communities
* Predicting future collaborations

Layered collaboration data keeps formal publications separate from informal
interactions while still letting you track cross-context teams.

Epidemic Modeling
-----------------

Layers represent contact types with different transmission risks:

* Household contacts
* Workplace interactions
* Social gatherings
* Healthcare settings

**Example applications:**

* Predicting disease spread
* Evaluating intervention strategies
* Identifying super-spreader events

Assign layer-specific transmission probabilities to model different risks (e.g.,
household vs. workplace).

See :doc:`../how-to/simulate_dynamics` for epidemic modeling how-tos.

Communication Networks
----------------------

Layers capture organizational communication channels:

* Email correspondence
* Instant messaging
* Video conferencing
* Document collaboration

**Example applications:**

* Organizational structure analysis
* Information flow optimization
* Team effectiveness measurement

Layered communication captures channel preferences without losing the underlying
person identifiers.

Financial Networks
------------------

Layers distinguish financial instruments and ownership ties:

* Trade networks (goods, services)
* Financial flows (investments, loans)
* Ownership structures (subsidiaries, shareholding)
* Interbank lending networks

**Example applications:**

* Systemic risk assessment
* Contagion analysis
* Market structure analysis
* Regulatory network analysis

**Example: Multi-layer financial network**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import execute_query
    
    # Build financial network with multiple relationship types
    network = multinet.multi_layer_network(directed=True)
    
    # Trade relationships
    network.add_edges([
        ['BankA', 'trade', 'BankB', 'trade', 1.5],  # Trade volume in billions
        ['BankB', 'trade', 'BankC', 'trade', 2.3],
        ['BankC', 'trade', 'BankA', 'trade', 1.8],
    ], input_type="list")
    
    # Ownership structures
    network.add_edges([
        ['BankA', 'ownership', 'SubsidiaryX', 'ownership', 0.75],  # 75% ownership
        ['BankB', 'ownership', 'SubsidiaryY', 'ownership', 0.60],
    ], input_type="list")
    
    # Interbank lending
    network.add_edges([
        ['BankA', 'lending', 'BankB', 'lending', 500],  # Lending amount
        ['BankB', 'lending', 'BankC', 'lending', 300],
        ['BankC', 'lending', 'BankA', 'lending', 200],
    ], input_type="list")
    
    # Identify systemically important institutions using DSL
    # (unweighted betweenness across all layers; pass weight='weight' to include amounts)
    centrality = execute_query(
        network,
        'SELECT nodes COMPUTE betweenness_centrality'
    )['computed']['betweenness_centrality']
    
    top_3 = sorted(
        centrality.items(),
        key=lambda item: item[1],
        reverse=True
    )[:3]
    
    print("Top betweenness nodes (node, betweenness):")
    for node, score in top_3:
        print(f"  {node}: {score:.4f}")
    
    # Find institutions represented in multiple layers
    from collections import Counter
    node_layer_count = Counter(node for node, layer in network.get_nodes())
    multi_layer_nodes = [
        node for node, count in node_layer_count.items() if count >= 2
    ]
    
    print(f"\nInstitutions with multiple relationship types: {len(multi_layer_nodes)}")
    for node in sorted(multi_layer_nodes):
        print(f"  {node}")

**Use cases for financial network analysis:**

* **Systemic risk:** Identify institutions whose failure would cascade through multiple layers
* **Regulatory oversight:** Detect hidden dependencies across different financial instruments
* **Market surveillance:** Monitor unusual patterns in multi-layer trading relationships
* **Portfolio diversification:** Understand correlation structures across asset types

See :doc:`../how-to/run_community_detection` for detecting financial communities and :doc:`../how-to/simulate_dynamics` for contagion modeling.

Next Steps
----------

* **Try an example:** :doc:`../getting_started/tutorial_10min`
* **See complete examples:** :doc:`../examples/index`
* **Learn the concepts:** :doc:`../concepts/multilayer_networks_101`
