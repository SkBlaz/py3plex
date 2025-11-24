Multilayer Networks 101
=======================

This guide explains what multilayer networks are and why they matter for modern network analysis.

What are Multilayer Networks?
------------------------------

A **multilayer network** is a complex network structure that goes beyond traditional single-layer graphs by incorporating multiple types of relationships, node types, or interaction contexts. They model the reality that most real-world systems involve multiple, interconnected types of relationships.

Traditional vs. Multilayer
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Traditional (Single-Layer) Networks:**

* One type of node (e.g., only people)
* One type of edge (e.g., only friendship)
* Homogeneous structure
* Limited ability to model complex systems

**Multilayer Networks:**

* Multiple node types (e.g., people, organizations, documents)
* Multiple edge types (e.g., friendship, collaboration, citation)
* Multiple layers of interaction
* Inter-layer and intra-layer connections
* Rich, heterogeneous structure

Types of Multilayer Networks
-----------------------------

py3plex supports several common multilayer network paradigms:

Multiplex Networks
~~~~~~~~~~~~~~~~~~

**Definition:** Multiple layers with the **same set of nodes** but different types of edges.

**Characteristics:**

* Node set is identical across layers
* Each layer represents a different relationship type
* Inter-layer edges typically connect the same node across layers

**Examples:**

* **Social networks:** The same people connected via friendship, colleague, and family relationships
* **Transportation:** Cities connected via air, rail, and road networks
* **Communication:** Users interacting via email, phone, and instant messaging

**Visual representation:**

.. code-block:: text

    Layer 1 (Friends):        Layer 2 (Colleagues):
    A --- B --- C             A --- B
      \   |                       |
        \ |                       D
          D

**Code example:**

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network(network_type="multiplex")
    
    # Same nodes, different relationship types
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
    ], input_type="list")

Heterogeneous Networks (HINs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Networks with **different node types** and type-specific relationships.

**Characteristics:**

* Multiple node types (e.g., authors, papers, venues)
* Edges connect nodes of specific types
* Meta-paths describe relationship sequences

**Examples:**

* **Academic networks:** Authors write papers published in venues
* **E-commerce:** Users purchase products from sellers
* **Biomedical:** Drugs treat diseases via molecular targets

**Visual representation:**

.. code-block:: text

    Authors       Papers        Venues
    [Alice] ----> [P1] --------> [ICML]
       |           ^               ^
       |           |               |
       +---------> [P2] -----------+
    [Bob]

**Code example:**

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Different node types on different layers
    network.add_edges([
        ['Alice', 'authors', 'Paper1', 'papers', 1],
        ['Paper1', 'papers', 'ICML', 'venues', 1],
    ], input_type="list")

Temporal Networks
~~~~~~~~~~~~~~~~~

**Definition:** Networks that **evolve over time**, with time-sliced layers.

**Characteristics:**

* Each layer represents a time period
* Nodes may appear/disappear over time
* Edges show relationships at specific times
* Inter-layer edges connect temporal states

**Examples:**

* **Communication networks:** Who-contacts-whom over different time periods
* **Social dynamics:** Friendship evolution over years
* **Disease spread:** Contact networks during epidemic progression

**Visual representation:**

.. code-block:: text

    t=1: A --- B --- C
              |
              D
              
    t=2: A --- B --- C --- E
              |       |
              D ------+
              
    t=3: A --- B --- C --- E
                     |
                     D

**Code example:**

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Different time periods as layers
    network.add_edges([
        ['A', 't1', 'B', 't1', 1],
        ['A', 't2', 'B', 't2', 1],
        ['B', 't2', 'D', 't2', 1],
    ], input_type="list")

Interdependent Networks
~~~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Multiple networks where **nodes in one network depend on nodes in another**.

**Characteristics:**

* Networks with distinct functions
* Dependencies between networks
* Cascading failures possible
* Critical infrastructure modeling

**Examples:**

* **Infrastructure:** Power grid depends on communication network
* **Supply chain:** Manufacturing depends on logistics network
* **Cyber-physical systems:** Software layer depends on hardware layer

**Visual representation:**

.. code-block:: text

    Power Grid:           Communication Net:
    P1 --- P2 --- P3      C1 --- C2 --- C3
     |      |              |      |
    Depends on            C4      |
     |      |                     |
     v      v              v      v
     C1 --- C2            P1 --- P2

When to Use Multilayer Networks
--------------------------------

Use multilayer networks when:

**1. Multiple Relationship Types Matter**

If your system has multiple types of connections that interact, a multilayer model is essential.

*Example:* Studying information diffusion in social networks where both online and offline relationships matter.

**2. Node Roles Vary by Context**

When nodes play different roles in different contexts or layers.

*Example:* A person might be central in their work network but peripheral in their hobby network.

**3. Layer Interactions Are Important**

When understanding how layers interact is crucial to your analysis.

*Example:* How transportation failures in one mode (air) affect alternatives (rail, road).

**4. Temporal Evolution Matters**

When the timing and sequence of relationships are important.

*Example:* Understanding how community structure evolves over time in a social network.

**5. System-Level Properties Emerge**

When whole-system properties can't be understood by analyzing layers independently.

*Example:* Resilience of infrastructure systems depends on cross-layer dependencies.

Comparison with Single-Layer Approaches
----------------------------------------

Why Not Just Aggregate?
~~~~~~~~~~~~~~~~~~~~~~~~

You might ask: "Why not just combine all layers into one network?"

**Problems with aggregation:**

1. **Loss of Information:** Different relationship types get conflated
2. **Misleading Metrics:** Centrality computed on aggregated network can be wrong
3. **Hidden Patterns:** Layer-specific patterns are lost
4. **Incorrect Analysis:** Communities and pathways depend on layer structure

**Example:**

.. code-block:: python

    # DON'T: Naive aggregation loses information
    all_edges = []
    all_edges.extend(friends_edges)
    all_edges.extend(colleague_edges)
    single_layer = nx.Graph(all_edges)  # Information about edge types lost!
    
    # DO: Use multilayer representation
    network = multinet.multi_layer_network()
    network.add_edges(friends_edges + colleague_edges, input_type="list")

Why Not Analyze Each Layer Separately?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You might ask: "Why not just analyze each layer independently?"

**Problems with separate analysis:**

1. **Ignores Cross-Layer Effects:** Nodes may be important because of multi-layer presence
2. **Misses Inter-Layer Patterns:** Communities often span multiple layers
3. **Incomplete View:** Node importance depends on cross-layer activity
4. **Lost Synergies:** Complementary information across layers is ignored

**Example:** A person who is moderately connected in multiple social contexts may be more influential than someone highly connected in just one context.

Key Concepts
------------

Intra-Layer Edges
~~~~~~~~~~~~~~~~~

Edges **within** a single layer connecting nodes in that layer.

*Example:* Friendships within the "friends" layer.

Inter-Layer Edges
~~~~~~~~~~~~~~~~~

Edges **between** layers, typically connecting the same node across layers or different nodes in different layers.

*Example:* Connecting Alice in the "friends" layer to Alice in the "colleagues" layer.

Node-Layer Pairs
~~~~~~~~~~~~~~~~

In py3plex, nodes are represented as ``(node_id, layer_id)`` tuples.

*Example:* ``('Alice', 'friends')`` and ``('Alice', 'colleagues')`` are different node-layer pairs.

Supra-Adjacency Matrix
~~~~~~~~~~~~~~~~~~~~~~

A matrix representation that stacks layer adjacency matrices into a block structure, encoding both intra-layer and inter-layer connections.

See :doc:`py3plex_core_model` for implementation details.

Real-World Applications
-----------------------

py3plex has been used for analyzing:

**Biological Networks:**

* Protein-protein interactions with multiple evidence types
* Gene regulatory networks with transcription, translation, and metabolic layers
* Brain networks with structural and functional connectivity

**Social Networks:**

* Multi-platform social media analysis (Twitter + Facebook + Instagram)
* Relationship type analysis (friends, family, colleagues)
* Online-offline integration studies

**Citation Networks:**

* Author-paper-venue multilayer structures
* Knowledge graphs with entities, relationships, and contexts
* Research collaboration networks

**Transportation:**

* Multi-modal networks (bus, train, metro, air)
* Urban mobility analysis
* Resilience and failure analysis

**Infrastructure:**

* Critical infrastructure interdependencies
* Smart city systems
* Cyber-physical systems

Further Reading
---------------

* :doc:`py3plex_core_model` - How py3plex represents multilayer networks internally
* :doc:`design_principles` - Design philosophy and API principles
* :doc:`algorithm_landscape` - Overview of multilayer algorithms
* :doc:`../user_guide/networks` - Creating and loading multilayer networks in code

**Academic References:**

* Kivelä et al. (2014). "Multilayer networks." *Journal of Complex Networks* 2(3): 203-271.
* Boccaletti et al. (2014). "The structure and dynamics of multilayer networks." *Physics Reports* 544(1): 1-122.
* De Domenico et al. (2013). "Mathematical formulation of multilayer networks." *Physical Review X* 3(4): 041022.
