Multilayer Networks 101
=======================

This chapter provides a conceptual foundation for understanding multilayer networks—what they are, why they matter, and when to use them. By the end, you'll have the intuition needed to model your own systems as multilayer networks and understand why py3plex exists.

What are Multilayer Networks?
------------------------------

A **multilayer network** is a complex network structure that goes beyond traditional single-layer graphs by incorporating multiple types of relationships, node types, or interaction contexts. They model the reality that most real-world systems involve multiple, interconnected types of relationships.

Consider a simple question: how do you model the social world of a university researcher? They have:

* **Coauthors** — people they've written papers with
* **Colleagues** — people in their department
* **Students** — people they mentor
* **Conference contacts** — people they've met at workshops
* **Twitter followers** — an entirely different mode of interaction

A traditional graph might combine all of these into a single "social network," but that loses critical information. The coauthor relationship implies deep collaboration; a Twitter follow implies much less. When you flatten everything into one edge type, you can't distinguish these—and your analysis suffers.

Multilayer networks preserve this richness. Each relationship type becomes a **layer**, and the same person can appear in multiple layers with different connection patterns in each.

Traditional vs. Multilayer
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Traditional (Single-Layer) Networks:**

* One type of node (e.g., only people)
* One type of edge (e.g., only friendship)
* Homogeneous structure
* Limited ability to model complex systems
* What NetworkX and most tools assume by default

**Multilayer Networks:**

* Multiple node types (e.g., people, organizations, documents)
* Multiple edge types (e.g., friendship, collaboration, citation)
* Multiple layers of interaction
* Inter-layer and intra-layer connections
* Rich, heterogeneous structure
* What py3plex is designed to handle

Types of Multilayer Networks
-----------------------------

py3plex supports several common multilayer network paradigms. Understanding which type matches your data is the first modeling decision you'll make.

Multiplex Networks
~~~~~~~~~~~~~~~~~~

**Definition:** Multiple layers with the **same set of nodes** but different types of edges.

**Characteristics:**

* Node set is identical across layers
* Each layer represents a different relationship type
* Inter-layer edges typically connect the same node across layers (identity coupling)

**Toy Example:**

Consider Alice, Bob, Carol, and Dave. They have two types of relationships: friendship and professional collaboration.

.. code-block:: text

    Layer 1 (Friends):          Layer 2 (Colleagues):
    
    Alice ---- Bob              Alice ---- Bob
       \       |                          |
        \      |                          |
         Carol |                         Dave
               |
              Dave (not in L1)
    
    Friends: Alice-Bob, Bob-Carol
    Colleagues: Alice-Bob, Bob-Dave

Notice that Alice-Bob is an edge in *both* layers—they're both friends and colleagues. Carol only appears in the friends layer; Dave only in colleagues. In a multiplex analysis, we'd observe that:

* Alice and Bob have **high activity** (appear in both layers)
* Carol and Dave have **low activity** (appear in one layer each)
* The friends and colleagues layers have **partial overlap** (Alice-Bob edge exists in both)

**Code example:**

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network(network_type="multiplex")
    
    # Same nodes, different relationship types
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
        ['Bob', 'colleagues', 'Dave', 'colleagues', 1],
    ], input_type="list")

**Real-world examples:**

* **Social networks:** The same people connected via friendship, colleague, and family relationships
* **Transportation:** Cities connected via air, rail, and road networks
* **Communication:** Users interacting via email, phone, and instant messaging

Heterogeneous Information Networks (HINs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Networks with **different node types** and type-specific relationships.

**Characteristics:**

* Multiple node types (e.g., authors, papers, venues)
* Edges connect nodes of specific types (authors write papers; papers are published in venues)
* Meta-paths describe relationship sequences (Author → Paper → Venue → Paper → Author)

**Toy Example:**

An academic citation network with three node types:

.. code-block:: text

    Authors           Papers            Venues
    
    [Alice] ----writes----> [P1] ----published_in----> [ICML]
       |                      ^                           ^
       |                      |                           |
       +----writes----> [P2] ----published_in-------------+
    [Bob] ----writes----> [P2]

Alice wrote papers P1 and P2. Bob co-authored P2. P1 appeared at ICML; P2 also appeared at ICML. This structure lets us answer questions like:

* "Which authors have published at ICML?" (follow Author→Paper→Venue)
* "Which authors are likely collaborators?" (Author→Paper→Author meta-path)
* "Which venues publish similar work?" (Venue→Paper→Author→Paper→Venue)

**Code example:**

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Different node types on different layers
    network.add_edges([
        ['Alice', 'authors', 'P1', 'papers', 1],
        ['Alice', 'authors', 'P2', 'papers', 1],
        ['Bob', 'authors', 'P2', 'papers', 1],
        ['P1', 'papers', 'ICML', 'venues', 1],
        ['P2', 'papers', 'ICML', 'venues', 1],
    ], input_type="list")

**Real-world examples:**

* **Academic networks:** Authors write papers published in venues
* **E-commerce:** Users purchase products from sellers in categories
* **Biomedical:** Drugs treat diseases via molecular targets

Temporal Multilayer Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Networks that **evolve over time**, with time-sliced layers.

**Characteristics:**

* Each layer represents a time period (year, month, day)
* Nodes may appear/disappear over time
* Edges show relationships at specific times
* Inter-layer edges can connect temporal states (same node in adjacent time periods)

**Toy Example:**

A friendship network evolving over three years:

.. code-block:: text

    Year 2020:           Year 2021:           Year 2022:
    
    A ---- B             A ---- B             A ---- B ---- E
           |                   |                     |
           C                   C ---- D               C ---- D

In 2020, only A-B and B-C edges exist. By 2021, C-D appears. By 2022, B-E appears and the network has grown. Temporal analysis reveals:

* A-B is a **persistent edge** (exists in all time periods)
* B-E is a **new edge** (appears in 2022)
* The network is **growing** over time

**Code example:**

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Different time periods as layers
    network.add_edges([
        ['A', '2020', 'B', '2020', 1],
        ['B', '2020', 'C', '2020', 1],
        ['A', '2021', 'B', '2021', 1],
        ['B', '2021', 'C', '2021', 1],
        ['C', '2021', 'D', '2021', 1],
        ['A', '2022', 'B', '2022', 1],
        ['B', '2022', 'C', '2022', 1],
        ['B', '2022', 'E', '2022', 1],
        ['C', '2022', 'D', '2022', 1],
    ], input_type="list")

**Real-world examples:**

* **Communication networks:** Who-contacts-whom over different time periods
* **Social dynamics:** Friendship evolution over years
* **Disease spread:** Contact networks during epidemic progression

Interdependent Networks
~~~~~~~~~~~~~~~~~~~~~~~~

**Definition:** Multiple networks where **nodes in one network depend on nodes in another**.

**Characteristics:**

* Networks with distinct functions (power grid, communication network)
* Dependencies between networks (power station needs communication to operate)
* Cascading failures possible (communication failure → power failure → more communication failures)
* Critical for infrastructure modeling

**Toy Example:**

A simplified power grid + communication network:

.. code-block:: text

    Power Grid:               Communication Network:
    
    [P1] ---- [P2] ---- [P3]       [C1] ---- [C2] ---- [C3]
      |         |                    |          |
      |    depends on                |     depends on
      |         |                    |          |
      v         v                    v          v
    [C1]      [C2]                 [P1]       [P2]

Power station P1 needs communication node C1 to operate (for control signals). Communication node C1 needs power from P1. This creates a dependency loop. If C1 fails:

1. P1 loses control signals and may fail
2. C1 loses power anyway (was depending on P1)
3. This can cascade to other dependent nodes

**Real-world examples:**

* **Infrastructure:** Power grid depends on communication network (and vice versa)
* **Supply chain:** Manufacturing depends on logistics network
* **Cyber-physical systems:** Software layer depends on hardware layer
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

*Example:* Studying information diffusion in social networks where both online and offline relationships matter. Information might spread quickly through Twitter (one layer) but trust is built through face-to-face interactions (another layer). A model that conflates these misses how online virality depends on offline trust networks.

**2. Node Roles Vary by Context**

When nodes play different roles in different contexts or layers.

*Example:* A person might be a hub in their work network (many professional connections) but peripheral in their hobby network (few connections to fellow hobbyists). If you aggregate, you see only their overall degree—you miss that their influence is context-specific.

**3. Layer Interactions Are Important**

When understanding how layers interact is crucial to your analysis.

*Example:* How transportation failures in one mode (air travel) affect alternatives (rail, road). During an airport closure, passenger flow shifts to other modes. Modeling this requires inter-layer dependencies, not just separate single-layer analyses.

**4. Temporal Evolution Matters**

When the timing and sequence of relationships are important.

*Example:* Understanding how community structure evolves over time in a social network. A friendship that existed in 2020 but not 2021 tells a different story than a friendship that exists in all years. Temporal layers capture this evolution.

**5. System-Level Properties Emerge**

When whole-system properties can't be understood by analyzing layers independently.

*Example:* Resilience of infrastructure systems depends on cross-layer dependencies. A city's power grid might be robust in isolation, but if it depends on a fragile communication network, the system as a whole is fragile.

Choosing a Modeling Approach
-----------------------------

Before building your multilayer network, ask yourself these questions:

**Decision 1: Are layers truly distinct, or are they attributes?**

* If relationships have different *types* (friendship vs. professional) → Use **layers**
* If relationships vary only in *weight* or *time* → Consider edge **attributes** instead
* Rule of thumb: If you'd naturally analyze them separately, they're layers

**Decision 2: Same nodes across layers, or different nodes?**

* Same entities in all layers → **Multiplex** (e.g., same people on different platforms)
* Different entity types → **Heterogeneous** (e.g., authors, papers, venues)
* Same entities but some missing → **General multilayer** with identity coupling

**Decision 3: How strong is inter-layer coupling?**

* Identity coupling only (same node = same node) → Set ``omega=1.0`` in algorithms
* Nodes can differ across layers → Lower omega or explicit inter-layer edges
* No coupling (analyze layers independently) → Consider separate single-layer analyses

**Decision 4: Is temporal structure important?**

* Yes → Create time-sliced layers (e.g., one layer per month/year)
* No → Aggregate across time into a single static network per relationship type

What Goes Wrong When You Flatten
---------------------------------

To truly understand why multilayer networks matter, consider what goes wrong when you ignore layer structure.

Example: Flattening Destroys Community Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Consider a simple network with two layers:

.. code-block:: text

    Layer 1 (Work):                 Layer 2 (Hobby):
    
    A ---- B ---- C                 D ---- E ---- F
    
    (A, B, C are work colleagues)   (D, E, F share a hobby)

In the true multilayer view, there are two distinct communities: the work group {A, B, C} and the hobby group {D, E, F}. Now imagine A and D are the same person (they just appear in different contexts):

.. code-block:: text

    Flattened Network:
    
    A ---- B ---- C
    |
    E ---- F
    
    (A=D connects the two groups)

Community detection on the flattened network might merge these into one community, because A bridges them. But this is misleading—A doesn't actually connect their work colleagues to their hobby friends. The edge A-E only exists *within the hobby context*. Flattening created a spurious bridge.

**In py3plex:** By keeping layers separate, multilayer community detection correctly identifies two communities, with A participating in both.

Example: Centrality Becomes Misleading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Consider a researcher who:

* Has 2 coauthors (layer 1: coauthorship)
* Has 500 Twitter followers (layer 2: social media)

In a flattened network, this researcher has degree 502. In a degree-centrality ranking, they appear highly central. But this is misleading—their academic influence (measured by coauthorship) is minimal. Their "centrality" comes entirely from a different domain (social media).

**In py3plex:** Layer-specific centrality shows 2 in coauthorship, 500 in social media. Versatility centrality accounts for cross-layer participation without conflating different types of connections.

Example: Path Analysis Fails
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Consider trying to find how information might flow from Alice to Dave:

.. code-block:: text

    Layer 1 (Email):        Layer 2 (Meeting):
    Alice ---- Bob          Bob ---- Carol
                            Carol ---- Dave

The true path is: Alice → Bob (email) → Bob transitions to meeting context → Carol (meeting) → Dave (meeting).

In a flattened network, you might see Alice → Bob → Carol → Dave as a single path, but this obscures the crucial fact that the information had to *change modalities* (from email to meeting). This matters if, say, confidential information can only travel through secure channels.

**In py3plex:** Paths can be analyzed with layer constraints or meta-path patterns that respect modal transitions.

Domain-Specific Examples
------------------------

Biological Networks
~~~~~~~~~~~~~~~~~~~

**Protein-Protein Interaction Networks with Evidence Types**

Proteins interact through various mechanisms, and we learn about these interactions through different experimental methods. Each evidence type has different reliability:

* **Experimental evidence** (yeast two-hybrid, co-immunoprecipitation): High confidence
* **Computational prediction** (sequence similarity, domain interactions): Lower confidence  
* **Text mining** (extracted from literature): Variable confidence

Modeling this as a multilayer network:

* Layer 1: Experimental interactions
* Layer 2: Predicted interactions
* Layer 3: Text-mined interactions

**Why multilayer matters:** A protein pair connected in all three layers is much more likely to truly interact than one connected only by text mining. Aggregating would lose this confidence information.

**Gene Regulatory Networks**

Genes regulate each other through multiple mechanisms:

* **Transcriptional regulation** (transcription factors binding promoters)
* **Post-transcriptional regulation** (microRNAs targeting mRNAs)
* **Epigenetic regulation** (chromatin modification affecting expression)

Each mechanism operates at different timescales and has different effects. A multilayer model captures this heterogeneity.

Social Networks
~~~~~~~~~~~~~~~

**Multi-Platform Analysis**

Users interact across platforms with very different characteristics:

* **Twitter/X:** Public, broadcast, rapid, shallow interactions
* **Facebook:** Semi-private, friendship-based, richer interactions
* **LinkedIn:** Professional, career-oriented, formal interactions
* **WhatsApp:** Private, group-based, intimate interactions

The same person may be an influencer on Twitter but invisible on LinkedIn. Platform-specific analysis misses cross-platform patterns; aggregation loses context.

**Relationship Type Analysis**

Within a single platform, relationships vary:

* **Friends:** Bidirectional, social
* **Followers:** Unidirectional, interest-based
* **Mentions:** Ephemeral, attention-based
* **Retweets:** Content amplification

A multilayer model reveals how influence flows through different channel types.

Transportation and Infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Multi-Modal Transportation**

Urban mobility involves multiple modes:

* **Metro/Subway:** High capacity, fixed routes, high speed
* **Bus:** Lower capacity, flexible routes, variable speed
* **Bike-sharing:** Individual, flexible, weather-dependent
* **Walking:** Universal, slow, connects everything

Travelers make multi-modal trips: walk to metro, metro to city center, bike to final destination. Modeling as a multilayer network enables:

* Route optimization across modes
* Resilience analysis (what happens if metro fails?)
* Congestion spillover analysis

**Infrastructure Dependencies**

Critical infrastructure systems depend on each other:

* **Power grid** requires communication for control systems
* **Communication** requires power for equipment
* **Water** requires power for pumps
* **Transportation** requires communication for signals

Failure cascades can propagate across systems. Multilayer analysis is essential for resilience planning.

Knowledge Graphs
~~~~~~~~~~~~~~~~

**Academic Knowledge Graphs**

Research involves multiple entity types:

* **Authors** who write papers
* **Papers** that cite other papers
* **Venues** (journals, conferences) that publish papers
* **Institutions** that employ authors
* **Topics/Keywords** that describe papers

This forms a heterogeneous information network where meta-paths enable rich queries:

* Author → Paper → Venue → Paper → Author (same-venue co-authorship)
* Author → Institution → Author (institutional collaboration)
* Paper → Topic → Paper (topically similar papers)

Common Pitfalls When Modeling Multilayer Networks
--------------------------------------------------

**1. Over-Aggregating**

Combining layers that should remain separate. If relationships have fundamentally different meanings, keep them as separate layers.

*Symptom:* Your analysis produces results that don't make sense when you think about the original relationship types.

**2. Under-Aggregating**

Creating too many layers when some could be combined. If two relationship types are essentially the same (e.g., "friend" and "close friend"), consider using edge weights instead of separate layers.

*Symptom:* Many layers with few edges each; sparse statistics.

**3. Ignoring Inter-Layer Coupling**

Treating layers as completely independent when nodes have natural correspondences. In a multiplex network, "Alice in layer 1" and "Alice in layer 2" are the same person—this should be modeled.

*Symptom:* Cross-layer patterns invisible; node activity undefined.

**4. Wrong Coupling Strength**

Setting inter-layer coupling too high (forces artificial consistency across layers) or too low (loses cross-layer information).

*Symptom:* Community detection produces all-same-community or all-different-community results.

**5. Treating Layers as Ordered When They're Not**

Layers like "Facebook" and "Twitter" have no natural ordering. Layers like "2020, 2021, 2022" do. Using the wrong model loses temporal or modal structure.

*Symptom:* Temporal analysis fails; nonsensical transitions.

**6. Mismatched Node Identifiers**

The same entity must have the same identifier across layers. "alice@email.com" in layer 1 and "Alice Smith" in layer 2 are treated as different nodes unless you map them.

*Symptom:* Node activity appears low; entities seem layer-specific when they're not.

Key Concepts Summary
--------------------

This section provides quick reference definitions for the terminology used throughout py3plex.

Intra-Layer Edges
~~~~~~~~~~~~~~~~~

Edges **within** a single layer connecting nodes in that layer.

*Example:* Friendships within the "friends" layer.

Inter-Layer Edges
~~~~~~~~~~~~~~~~~

Edges **between** layers, typically connecting the same node across layers or different nodes in different layers.

*Example:* Connecting Alice in the "friends" layer to Alice in the "colleagues" layer. This is often called an "identity edge" when it connects the same entity.

Node-Layer Pairs
~~~~~~~~~~~~~~~~

In py3plex, nodes are represented as ``(node_id, layer_id)`` tuples. This is the fundamental representation.

*Example:* ``('Alice', 'friends')`` and ``('Alice', 'colleagues')`` are different node-layer pairs, even though they represent the same person in different contexts.

Supra-Adjacency Matrix
~~~~~~~~~~~~~~~~~~~~~~

A matrix representation that stacks layer adjacency matrices into a block structure, encoding both intra-layer and inter-layer connections. The diagonal blocks represent within-layer edges; off-diagonal blocks represent between-layer edges.

See :doc:`py3plex_core_model` for implementation details and a numeric example.

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
