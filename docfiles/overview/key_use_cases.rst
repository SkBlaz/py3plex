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

**Example applications:**

* Systemic risk assessment
* Contagion analysis
* Market structure analysis

TODO: Add specific examples for financial networks

Next Steps
----------

* **Try an example:** :doc:`../getting_started/quickstart_5min`
* **See complete examples:** :doc:`../examples/index`
* **Learn the concepts:** :doc:`../concepts/multilayer_networks_101`
