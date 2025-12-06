Chapter 2: Multilayer Network Basics
====================================

This chapter establishes the formal foundations of multilayer networks. We define key concepts, introduce mathematical notation, and show how different types of multilayer networks relate to each other.

Formal Definitions
------------------

Node-Layer Pairs
~~~~~~~~~~~~~~~~

A **multilayer network** :math:`\mathcal{M}` consists of:

* A set of **nodes** :math:`V = \{v_1, v_2, ..., v_N\}`
* A set of **layers** :math:`L = \{\alpha, \beta, \gamma, ...\}`
* A set of **node-layer pairs** :math:`V_M = V \times L`
* **Intra-layer edges** :math:`E_{\alpha} \subseteq V \times V` within each layer :math:`\alpha`
* **Inter-layer edges** :math:`E_{C} \subseteq V_M \times V_M` connecting node-layer pairs

The **node-layer pair** :math:`(v, \alpha)` is the fundamental unit: it represents node :math:`v` in the context of layer :math:`\alpha`.

Supra-Adjacency Matrix
~~~~~~~~~~~~~~~~~~~~~~

The **supra-adjacency matrix** :math:`\mathbf{A}` is a block matrix that encodes the full multilayer structure:

.. math::

   \mathbf{A} = \begin{pmatrix}
   \mathbf{A}_{\alpha\alpha} & \mathbf{A}_{\alpha\beta} & \cdots \\
   \mathbf{A}_{\beta\alpha} & \mathbf{A}_{\beta\beta} & \cdots \\
   \vdots & \vdots & \ddots
   \end{pmatrix}

Where:

* **Diagonal blocks** :math:`\mathbf{A}_{\alpha\alpha}` are the adjacency matrices of individual layers
* **Off-diagonal blocks** :math:`\mathbf{A}_{\alpha\beta}` encode inter-layer connections

For a multiplex network with :math:`N` nodes and :math:`L` layers, :math:`\mathbf{A}` is an :math:`(N \times L) \times (N \times L)` matrix.

**Example:** A 3-node, 2-layer network:

.. math::

   \mathbf{A} = \begin{pmatrix}
   \mathbf{A}_{\text{friends}} & \omega \mathbf{I} \\
   \omega \mathbf{I} & \mathbf{A}_{\text{colleagues}}
   \end{pmatrix}

where :math:`\omega` is the **inter-layer coupling strength** and :math:`\mathbf{I}` is the identity matrix (representing identity edges: each node connects to itself across layers).

Types of Multilayer Networks
-----------------------------

Multiplex Networks
~~~~~~~~~~~~~~~~~~

**Definition:** A multiplex network has the same node set in all layers, with different edge sets per layer.

.. math::

   V_{\alpha} = V_{\beta} = \cdots = V \quad \text{for all layers}

**Characteristics:**

* **Same entities** appear in all layers
* **Different relationship types** per layer
* **Strong inter-layer coupling** (typically :math:`\omega = 1.0` for identity edges)

**Example: Social Multiplex Network**

.. code-block:: python

    from py3plex.core import multinet
    
    # Create multiplex network
    network = multinet.multi_layer_network(network_type="multiplex")
    
    # Same people, different relationship types
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
        ['Bob', 'colleagues', 'Dave', 'colleagues', 1],
    ], input_type="list")
    
    # Verify structure
    print(f"Layers: {network.get_layers()}")
    print(f"Nodes per layer: {network.get_number_of_nodes_per_layer()}")

**Real-world applications:**

* Social networks across platforms (Facebook, Twitter, LinkedIn)
* Transportation modes (air, rail, road)
* Communication channels (email, phone, chat)
* Biological interactions (genetic, protein, metabolic)

Heterogeneous Information Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Definition:** A network with different node types, where edges connect specific node type pairs.

**Characteristics:**

* **Different node types** per layer (authors, papers, venues)
* **Type-specific edges** (author-paper, paper-venue)
* **No inter-layer coupling** (nodes don't repeat across layers)

**Example: Academic Network**

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Different node types
    network.add_edges([
        ['Alice', 'authors', 'Paper1', 'papers', 1],
        ['Bob', 'authors', 'Paper1', 'papers', 1],
        ['Paper1', 'papers', 'ICML', 'venues', 1],
        ['Paper2', 'papers', 'ICML', 'venues', 1],
    ], input_type="list")

This creates a **tripartite** network with three node types: authors, papers, and venues.

**Real-world applications:**

* Academic networks (authors, papers, venues, keywords)
* E-commerce (users, products, sellers, categories)
* Biomedical (drugs, diseases, targets, pathways)
* Knowledge graphs (entities, relations, concepts)

Temporal Networks
~~~~~~~~~~~~~~~~~

**Definition:** Networks that evolve over time, represented as time-sliced layers.

**Characteristics:**

* **Time windows as layers** (2020, 2021, 2022, ...)
* **Node presence varies** across time slices
* **Temporal edges** connect adjacent time slices

**Example: Temporal Social Network**

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Time-sliced layers
    network.add_edges([
        ['Alice', '2020', 'Bob', '2020', 1],
        ['Alice', '2021', 'Bob', '2021', 1],
        ['Bob', '2021', 'Carol', '2021', 1],
        ['Alice', '2022', 'Carol', '2022', 1],
    ], input_type="list")

**Real-world applications:**

* Communication patterns over time
* Disease spread through populations
* Financial transaction networks
* Collaboration evolution

Interdependent Networks
~~~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Multiple networks where the function of nodes in one layer depends on nodes in other layers.

**Characteristics:**

* **Dependency edges** encode functional relationships
* **Cascading failures** possible across layers
* **Critical infrastructure** applications

**Example:** Power grid (layer 1) depends on communication network (layer 2). If communication fails, power grid control fails.

**Real-world applications:**

* Infrastructure systems (power, water, communication)
* Supply chain networks
* Cyber-physical systems
* Ecological networks (species, habitats, resources)

Inter-Layer Coupling
--------------------

The **coupling strength** :math:`\omega` controls how strongly layers are connected.

Identity Coupling
~~~~~~~~~~~~~~~~~

The most common form connects each node to itself across layers:

.. math::

   E_C = \{((v, \alpha), (v, \beta)) : v \in V, \alpha \neq \beta \in L\}

with edge weight :math:`\omega`.

**Choice of** :math:`\omega`:

* :math:`\omega = 1.0` — Layers are equally important, nodes fully correspond
* :math:`\omega < 1.0` — Layers are loosely coupled, favor intra-layer paths
* :math:`\omega > 1.0` — Inter-layer transitions are encouraged

**Example:**

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Add intra-layer edges
    network.add_edges([
        ['A', 'layer1', 'B', 'layer1', 1],
        ['A', 'layer2', 'C', 'layer2', 1],
    ], input_type="list")
    
    # Add inter-layer coupling (identity edges)
    network.add_edges([
        ['A', 'layer1', 'A', 'layer2', 0.5],  # omega = 0.5
    ], input_type="list")

General Coupling
~~~~~~~~~~~~~~~~

More complex couplings allow different nodes to connect across layers:

.. math::

   E_C = \{((v, \alpha), (w, \beta)) : (v, w) \in C_{\alpha\beta}\}

where :math:`C_{\alpha\beta}` defines which nodes couple between layers :math:`\alpha` and :math:`\beta`.

When to Use Multilayer Networks
--------------------------------

Use multilayer modeling when:

1. **Multiple relationship types have distinct semantics**
   
   Example: Friendship vs. professional collaboration—these networks have different properties and dynamics.

2. **Node roles vary by context**
   
   Example: A person central in academic network may be peripheral in social media network.

3. **Cross-layer interactions matter**
   
   Example: Information spreads from Twitter to traditional media—this cross-layer flow is meaningful.

4. **Temporal evolution is important**
   
   Example: Community structure evolves over time—time-sliced layers preserve this evolution.

5. **System-level resilience depends on layer dependencies**
   
   Example: Power grid failure affects communication, which affects emergency response.

Choosing a Modeling Approach
-----------------------------

Decision Tree
~~~~~~~~~~~~~

.. code-block:: text

    1. Do relationships have fundamentally different types?
       YES → Use layers (multiplex or heterogeneous)
       NO  → Use edge weights or attributes

    2. Are the same entities present in all layers?
       YES → Multiplex network (strong coupling)
       NO  → Heterogeneous network (weak/no coupling)

    3. Does time evolution matter?
       YES → Temporal layers (time-sliced)
       NO  → Static multilayer network

    4. Are there functional dependencies between layers?
       YES → Interdependent network (dependency edges)
       NO  → Standard multiplex/heterogeneous

Common Mistakes
~~~~~~~~~~~~~~~

**Over-aggregation**
  Combining layers that should stay separate (e.g., merging email and meeting networks loses information about mode transitions).

**Under-aggregation**
  Creating too many sparse layers when edge weights would suffice (e.g., separate layer for each email vs. email timestamp as attribute).

**Wrong coupling strength**
  Using :math:`\omega = 1.0` when nodes don't fully correspond, or :math:`\omega \to 0` when they do.

**Mismatched identifiers**
  Using different IDs for the same entity across layers breaks multiplex structure.

Why Flattening Fails
---------------------

Flattening (aggregating all layers into a single graph) loses critical information:

**1. Community Structure**

Multilayer communities may have:

* **Core in one layer, periphery in another**
* **Cross-layer bridges** that appear as spurious intra-layer connections when flattened

**Example:** Academic collaboration (dense group) + Twitter followers (different dense group). Flattening creates false bridges.

**2. Centrality**

A node's importance depends on layer:

* **Structural centrality** in one layer (high degree)
* **Functional centrality** in another (betweenness for information flow)

Flattening mixes these distinct roles.

**3. Path Structure**

Meaningful paths often cross layers:

* Email → meeting → collaboration
* Twitter mention → news coverage → policy change

Flattening hides these cross-layer transitions.

**4. Dynamics**

Disease spreading, information diffusion, and cascading failures all depend on layer-specific parameters and inter-layer transitions. Flattening cannot capture:

* **Layer-specific transmission rates**
* **Mode-switching dynamics**
* **Asymmetric cross-layer effects**

Key Terminology
---------------

.. glossary::

   Intra-layer edges
      Edges within a single layer, connecting :math:`(v, \alpha)` to :math:`(w, \alpha)`.

   Inter-layer edges
      Edges between layers, connecting :math:`(v, \alpha)` to :math:`(w, \beta)` with :math:`\alpha \neq \beta`.

   Node-layer pair
      The tuple :math:`(v, \alpha)` representing node :math:`v` in layer :math:`\alpha`—the fundamental unit of a multilayer network.

   Supra-adjacency matrix
      The block matrix :math:`\mathbf{A}` encoding all intra-layer and inter-layer edges.

   Coupling strength
      The weight :math:`\omega` of inter-layer edges, controlling how strongly layers interact.

   Multiplex network
      Multilayer network with the same nodes in all layers.

   Heterogeneous information network
      Multilayer network with different node types per layer.

Working with Supra-Adjacency Matrices in Py3plex
-------------------------------------------------

.. code-block:: python

    from py3plex.core import multinet, random_generators
    
    # Generate random multilayer network
    network = random_generators.random_multilayer_ER(
        num_nodes=100, 
        num_layers=3, 
        probability=0.05, 
        directed=False
    )
    
    # Get supra-adjacency matrix (sparse format)
    supra_matrix = network.get_supra_adjacency_matrix()
    
    print(f"Matrix shape: {supra_matrix.shape}")  # (300, 300) for 100 nodes × 3 layers
    print(f"Matrix density: {supra_matrix.nnz / (supra_matrix.shape[0] ** 2):.4f}")
    
    # Visualize matrix structure
    network.visualize_matrix({"display": True})

The supra-adjacency matrix enables tensor-based algorithms and linear algebra operations on the full multilayer structure.

Summary
-------

Multilayer networks formalize systems with multiple relationship types by:

* Using **node-layer pairs** as the fundamental unit
* Encoding structure in the **supra-adjacency matrix**
* Supporting various types: **multiplex**, **heterogeneous**, **temporal**, **interdependent**
* Controlling interaction via **coupling strength** :math:`\omega`

Key takeaways:

1. **Multiplex** = same nodes, different edge types
2. **Heterogeneous** = different node types per layer
3. **Temporal** = time-sliced layers
4. **Coupling** = inter-layer connections (identity edges most common)
5. **Flattening loses information** — use multilayer analysis when layer structure matters

The next chapter explains how py3plex implements these concepts and why its design choices support efficient, correct multilayer analysis.

Further Reading
---------------

* **Theory:** Kivelä et al. (2014). "Multilayer networks." *J. Complex Networks* 2(3): 203-271.
* **Physics:** Boccaletti et al. (2014). "The structure and dynamics of multilayer networks." *Physics Reports* 544(1): 1-122.
* **Textbook:** Bianconi, G. (2018). *Multilayer Networks: Structure and Function.* Oxford University Press.
* **Applications:** De Domenico et al. (2013). "Mathematical formulation of multilayer networks." *Physical Review X* 3(4): 041022.
