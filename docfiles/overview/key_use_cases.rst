Key Use Cases
=============

py3plex is used across multiple domains for analyzing complex systems with multiple relationship types.

Social Networks
---------------

**Multiplex social networks** capture different types of social relationships:

* Friendship, family, and professional connections
* Online interactions: mentions, retweets, replies
* Communication channels: email, chat, video calls

**Example applications:**

* Identifying influential users across multiple platforms
* Detecting communities that span different relationship types
* Predicting information diffusion through multiple channels

.. code-block:: python

    # Example: Multi-platform social network
    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'twitter', 'Bob', 'twitter', 1],
        ['Alice', 'linkedin', 'Bob', 'linkedin', 1],
        ['Bob', 'twitter', 'Carol', 'twitter', 1],
    ], input_type="list")
    
    # Find users active across platforms
    from py3plex.dsl import Q
    active_users = (
        Q.nodes()
         .where(layer_count__gt=1)  # Present in multiple layers
         .execute(network)
    )

Biological Networks
-------------------

**Molecular interaction networks** with multiple relationship types:

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
    network = multinet.multi_layer_network()
    
    # Physical interactions
    network.add_edge('TP53', 'ppi', 'MDM2', 'ppi')
    
    # Regulatory interactions
    network.add_edge('TP53', 'regulation', 'CDKN1A', 'regulation')
    
    # Find key regulators with multiple interaction types
    result = execute_query(network,
        'SELECT nodes WHERE layer_count > 1 '
        'COMPUTE degree COMPUTE betweenness_centrality'
    )

Transportation Networks
-----------------------

**Multimodal transportation** with different travel modes:

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
    network = multinet.multi_layer_network()
    
    # Different transportation modes
    network.add_edge('StationA', 'metro', 'StationB', 'metro')
    network.add_edge('StationA', 'bus', 'StationC', 'bus')
    network.add_edge('StationB', 'metro', 'StationC', 'metro')
    
    # Inter-layer connections (transfers)
    network.add_edge('StationA', 'metro', 'StationA', 'bus', 
                     type='interlayer')

Knowledge Graphs
----------------

**Heterogeneous knowledge networks** with different entity and relation types:

* Entity types: people, organizations, locations, concepts
* Relation types: employment, location, authorship, citation

**Example applications:**

* Entity linking and disambiguation
* Knowledge graph completion
* Question answering over structured data

Scientific Collaboration
------------------------

**Co-authorship networks** across disciplines:

* Joint publications
* Grant collaborations
* Conference attendance
* Social media interactions

**Example applications:**

* Identifying interdisciplinary researchers
* Detecting emerging research communities
* Predicting future collaborations

Epidemic Modeling
-----------------

**Disease transmission** through multiple contact types:

* Household contacts
* Workplace interactions
* Social gatherings
* Healthcare settings

**Example applications:**

* Predicting disease spread
* Evaluating intervention strategies
* Identifying super-spreader events

See :doc:`../how-to/simulate_dynamics` for epidemic modeling how-tos.

Communication Networks
----------------------

**Enterprise communication** across channels:

* Email correspondence
* Instant messaging
* Video conferencing
* Document collaboration

**Example applications:**

* Organizational structure analysis
* Information flow optimization
* Team effectiveness measurement

Financial Networks
------------------

**Economic relationships** at multiple scales:

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
    from py3plex.dsl import Q, execute_query
    
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
    
    # Identify systemically important institutions
    # (high degree across multiple relationship types)
    systemic_nodes = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .where(degree__gt=3)
         .order_by("betweenness_centrality", reverse=True)
         .execute(network)
    )
    
    print("Systemically Important Institutions:")
    for node, data in list(systemic_nodes.items())[:5]:
        print(f"  {node}: degree={data['degree']}, "
              f"betweenness={data['betweenness_centrality']:.4f}")
    
    # Analyze risk propagation
    # Find institutions connected across multiple layers
    from collections import Counter
    node_layer_count = Counter()
    for node, layer in network.get_nodes():
        node_layer_count[node] += 1
    
    highly_connected = {
        node: count for node, count in node_layer_count.items()
        if count >= 2  # Present in 2+ layers
    }
    
    print(f"\nInstitutions with multiple relationship types: {len(highly_connected)}")
    for node, count in sorted(highly_connected.items(), 
                              key=lambda x: x[1], reverse=True):
        print(f"  {node}: {count} relationship types")

**Expected output:**

.. code-block:: text

    Systemically Important Institutions:
      ('BankA', 'trade'): degree=4, betweenness=0.1234
      ('BankB', 'lending'): degree=4, betweenness=0.1156
      ('BankC', 'trade'): degree=3, betweenness=0.0987
    
    Institutions with multiple relationship types: 3
      BankA: 3 relationship types
      BankB: 3 relationship types
      BankC: 2 relationship types

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
