Ollivier-Ricci Curvature and Ricci Flow
========================================

Overview
--------

py3plex now provides support for **Ollivier-Ricci curvature** and **Ricci flow** on multilayer networks. These geometric measures reveal important structural properties of networks, including community boundaries, bottlenecks, and hierarchical organization.

What is Ollivier-Ricci Curvature?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ollivier-Ricci curvature is a discrete analog of Ricci curvature from differential geometry, adapted for graphs. For each edge in a network, the Ollivier-Ricci curvature measures the local connectivity between the neighborhoods of the edge's endpoints:

* **Positive curvature** indicates well-connected regions (dense communities)
* **Negative curvature** indicates bottlenecks or community boundaries
* **Near-zero curvature** indicates transitional regions

What is Ricci Flow?
~~~~~~~~~~~~~~~~~~~

Ricci flow is a geometric process that iteratively adjusts edge weights based on their curvature. The flow amplifies structural features:

* Edges with **negative curvature** (community boundaries) have their weights **reduced**
* Edges with **positive curvature** (within communities) have their weights **increased**

After Ricci flow, community detection becomes more effective, and the network's geometric structure is more pronounced.

Why Use These for Multilayer Networks?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Multilayer networks represent complex systems with multiple types of interactions. Ollivier-Ricci curvature and flow help:

* Identify cross-layer community boundaries
* Reveal hierarchical organization across layers
* Detect structural bottlenecks in coupled systems
* Enhance community detection on aggregated or supra-graph representations

Installation
------------

To use Ollivier-Ricci curvature and Ricci flow, you must install the optional **GraphRicciCurvature** library:

.. code-block:: bash

    pip install GraphRicciCurvature

If GraphRicciCurvature is not installed, py3plex will raise a clear error message with installation instructions when you attempt to use these features.

Basic Usage
-----------

Computing Curvature on the Aggregated Network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest use case is computing curvature on the **aggregated (core) network**, which combines all layers:

.. code-block:: python

    from py3plex.core import multinet

    # Load or create a multilayer network
    net = multinet.multi_layer_network().load_network(
        "path/to/multilayer_network.txt",
        input_type="multiedgelist",
        directed=False,
    )

    # Compute Ollivier-Ricci curvature on the aggregated core network
    result = net.compute_ollivier_ricci(
        mode="core",
        alpha=0.5,
        curvature_attr="ricciCurvature",
        inplace=True,
    )

    # Access the graph with curvatures
    G_core = result["core"]

    # Inspect edge curvatures
    for u, v, data in G_core.edges(data=True):
        if "ricciCurvature" in data:
            print(f"Edge {u}-{v}: curvature = {data['ricciCurvature']:.4f}")

After this, edges in ``net.core_network`` (if ``inplace=True``) will have a ``ricciCurvature`` attribute containing the computed curvature value.

Applying Ricci Flow
~~~~~~~~~~~~~~~~~~~

Once curvature is computed, you can apply Ricci flow to adjust edge weights:

.. code-block:: python

    # Run Ricci flow on the core network
    result_flow = net.compute_ollivier_ricci_flow(
        mode="core",
        alpha=0.5,
        iterations=10,
        method="OTD",
        inplace=True,
    )

    # Now edge weights in net.core_network reflect the Ricci flow metric
    G_flow = result_flow["core"]

    # Edge weights are updated to reflect Ricci flow
    for u, v, data in G_flow.edges(data=True):
        print(f"Edge {u}-{v}: weight after flow = {data.get('weight', 1.0):.4f}")

After Ricci flow, edges with negative curvature (community boundaries) will have reduced weights, making them easier to identify or remove during community detection.

Per-Layer Curvature
~~~~~~~~~~~~~~~~~~~

To compute curvature separately for each layer:

.. code-block:: python

    # Compute curvature separately for each layer
    layer_results = net.compute_ollivier_ricci(
        mode="layers",
        layers=None,  # None means all layers
        alpha=0.5,
        inplace=True,
    )

    # layer_results is a dictionary mapping layer identifiers to NetworkX graphs
    for layer_id, G_layer in layer_results.items():
        print(f"\nLayer: {layer_id}")
        for u, v, data in G_layer.edges(data=True):
            if "ricciCurvature" in data:
                print(f"  Edge {u}-{v}: curvature = {data['ricciCurvature']:.4f}")

You can also specify a subset of layers:

.. code-block:: python

    # Compute curvature only for specific layers
    layer_results = net.compute_ollivier_ricci(
        mode="layers",
        layers=["layer1", "layer2"],  # Only these layers
        alpha=0.5,
        inplace=False,
    )

Supra-Graph Curvature
~~~~~~~~~~~~~~~~~~~~~

The **supra-graph** representation includes both intra-layer edges (within each layer) and inter-layer edges (coupling nodes across layers). This is the most comprehensive view of the multilayer network:

.. code-block:: python

    # Compute curvature on the supra-graph representation
    supra_result = net.compute_ollivier_ricci(
        mode="supra",
        alpha=0.5,
        interlayer_weight=1.0,  # Weight for inter-layer coupling edges
        inplace=False,
    )

    G_supra = supra_result["supra"]

    # Identify inter-layer edges with negative curvature (weak coupling)
    for u, v, data in G_supra.edges(data=True):
        if isinstance(u, tuple) and isinstance(v, tuple):
            if u[0] == v[0] and u[1] != v[1]:  # Same node, different layers
                curvature = data.get("ricciCurvature", 0)
                print(f"Inter-layer edge {u}-{v}: curvature = {curvature:.4f}")

Similarly, you can apply Ricci flow to the supra-graph:

.. code-block:: python

    # Apply Ricci flow on the supra-graph
    supra_flow_result = net.compute_ollivier_ricci_flow(
        mode="supra",
        alpha=0.5,
        iterations=5,
        inplace=False,
    )

    G_supra_flow = supra_flow_result["supra"]

API Reference
-------------

compute_ollivier_ricci
~~~~~~~~~~~~~~~~~~~~~~

Compute Ollivier-Ricci curvature on the multilayer network.

**Signature:**

.. code-block:: python

    def compute_ollivier_ricci(
        self,
        mode: str = "core",
        layers: Optional[List[Any]] = None,
        alpha: float = 0.5,
        weight_attr: str = "weight",
        curvature_attr: str = "ricciCurvature",
        verbose: str = "ERROR",
        backend_kwargs: Optional[Dict[str, Any]] = None,
        inplace: bool = True,
        interlayer_weight: float = 1.0,
    ) -> Dict[str, Any]:

**Parameters:**

* ``mode`` : str, default "core"
    Scope of the computation. Options:
    
    - ``"core"``: Compute curvature on the aggregated (core) network
    - ``"layers"``: Compute curvature separately for each layer
    - ``"supra"``: Compute curvature on the supra-graph (includes inter-layer edges)

* ``layers`` : list or None, default None
    List of layer identifiers to process when ``mode="layers"``. If ``None``, all layers are processed. Ignored for other modes.

* ``alpha`` : float, default 0.5
    Ollivier-Ricci parameter in [0, 1] controlling the mass distribution. ``alpha=0`` uses pure neighbors, ``alpha=0.5`` is standard, and ``alpha=1`` uses uniform distribution over all nodes.

* ``weight_attr`` : str, default "weight"
    Name of the edge attribute containing edge weights.

* ``curvature_attr`` : str, default "ricciCurvature"
    Name of the edge attribute to store computed curvature values.

* ``verbose`` : str, default "ERROR"
    Verbosity level for GraphRicciCurvature. Options: ``"INFO"``, ``"DEBUG"``, ``"ERROR"``.

* ``backend_kwargs`` : dict or None, default None
    Optional dictionary of additional keyword arguments to pass to the ``OllivierRicci`` constructor from GraphRicciCurvature.

* ``inplace`` : bool, default True
    If ``True``, update internal graphs (e.g., ``self.core_network``). If ``False``, return new graphs without modifying the network.

* ``interlayer_weight`` : float, default 1.0
    Weight for inter-layer coupling edges (only used when ``mode="supra"``).

**Returns:**

* ``dict``
    Dictionary mapping scope identifiers to NetworkX graphs with computed curvatures:
    
    - ``mode="core"``: ``{"core": graph_with_curvature}``
    - ``mode="layers"``: ``{layer_id: graph_with_curvature, ...}``
    - ``mode="supra"``: ``{"supra": supra_graph_with_curvature}``

**Raises:**

* ``RicciBackendNotAvailable``
    If GraphRicciCurvature is not installed.
* ``ValueError``
    If ``mode`` is invalid or ``layers`` contains invalid identifiers.

compute_ollivier_ricci_flow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compute Ollivier-Ricci flow on the multilayer network.

**Signature:**

.. code-block:: python

    def compute_ollivier_ricci_flow(
        self,
        mode: str = "core",
        layers: Optional[List[Any]] = None,
        alpha: float = 0.5,
        iterations: int = 10,
        method: str = "OTD",
        weight_attr: str = "weight",
        curvature_attr: str = "ricciCurvature",
        verbose: str = "ERROR",
        backend_kwargs: Optional[Dict[str, Any]] = None,
        inplace: bool = True,
        interlayer_weight: float = 1.0,
    ) -> Dict[str, Any]:

**Parameters:**

* ``mode`` : str, default "core"
    Scope of the computation. Same options as ``compute_ollivier_ricci``.

* ``layers`` : list or None, default None
    List of layer identifiers to process when ``mode="layers"``.

* ``alpha`` : float, default 0.5
    Ollivier-Ricci parameter in [0, 1].

* ``iterations`` : int, default 10
    Number of Ricci flow iterations to perform. More iterations lead to stronger effects but take longer to compute.

* ``method`` : str, default "OTD"
    Method for Ricci flow computation. Options:
    
    - ``"OTD"``: Optimal Transport Distance (recommended)
    - ``"ATD"``: Average Transport Distance

* ``weight_attr`` : str, default "weight"
    Name of the edge attribute containing edge weights. After Ricci flow, these weights are updated to reflect the flow metric.

* ``curvature_attr`` : str, default "ricciCurvature"
    Name of the edge attribute to store curvature values.

* ``verbose`` : str, default "ERROR"
    Verbosity level.

* ``backend_kwargs`` : dict or None, default None
    Additional keyword arguments for the ``OllivierRicci`` constructor.

* ``inplace`` : bool, default True
    If ``True``, update internal graphs. If ``False``, return new graphs.

* ``interlayer_weight`` : float, default 1.0
    Weight for inter-layer coupling edges (only for ``mode="supra"``).

**Returns:**

* ``dict``
    Dictionary mapping scope identifiers to NetworkX graphs with Ricci flow applied.

**Raises:**

* ``RicciBackendNotAvailable``
    If GraphRicciCurvature is not installed.
* ``ValueError``
    If ``mode`` is invalid or ``layers`` contains invalid identifiers.

Advanced Examples
-----------------

Identifying Community Boundaries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edges with negative curvature often correspond to community boundaries:

.. code-block:: python

    # Compute curvature
    result = net.compute_ollivier_ricci(mode="core", inplace=True)
    G = result["core"]

    # Find edges with negative curvature (potential community boundaries)
    boundary_edges = [
        (u, v, data["ricciCurvature"])
        for u, v, data in G.edges(data=True)
        if data.get("ricciCurvature", 0) < -0.1  # Threshold
    ]

    print(f"Found {len(boundary_edges)} potential community boundary edges")
    for u, v, curvature in sorted(boundary_edges, key=lambda x: x[2]):
        print(f"  {u} -- {v}: {curvature:.4f}")

Enhanced Community Detection with Ricci Flow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ricci flow can improve community detection by reducing weights on boundary edges:

.. code-block:: python

    from py3plex.algorithms.community_detection import community_wrapper

    # Apply Ricci flow
    result = net.compute_ollivier_ricci_flow(
        mode="core",
        iterations=20,
        inplace=True
    )
    G_flow = result["core"]

    # Run community detection on the flow-adjusted network
    communities = community_wrapper.best_partition(G_flow)

    # Analyze communities
    from collections import defaultdict
    comm_sizes = defaultdict(int)
    for node, comm_id in communities.items():
        comm_sizes[comm_id] += 1

    print(f"Detected {len(comm_sizes)} communities")
    for comm_id, size in sorted(comm_sizes.items()):
        print(f"  Community {comm_id}: {size} nodes")

Cross-Layer Analysis with Supra-Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the supra-graph to analyze relationships between layers:

.. code-block:: python

    # Compute curvature on supra-graph
    supra_result = net.compute_ollivier_ricci(
        mode="supra",
        alpha=0.5,
        interlayer_weight=1.0,
        inplace=False
    )
    G_supra = supra_result["supra"]

    # Analyze intra-layer vs. inter-layer curvatures
    intra_curvatures = []
    inter_curvatures = []

    for u, v, data in G_supra.edges(data=True):
        if isinstance(u, tuple) and isinstance(v, tuple):
            curvature = data.get("ricciCurvature", 0)
            if u[1] == v[1]:  # Same layer (intra-layer edge)
                intra_curvatures.append(curvature)
            elif u[0] == v[0]:  # Same node, different layers (inter-layer edge)
                inter_curvatures.append(curvature)

    import numpy as np
    print(f"Intra-layer curvature: mean={np.mean(intra_curvatures):.4f}, "
          f"std={np.std(intra_curvatures):.4f}")
    print(f"Inter-layer curvature: mean={np.mean(inter_curvatures):.4f}, "
          f"std={np.std(inter_curvatures):.4f}")

Performance Considerations
--------------------------

Computing Ollivier-Ricci curvature can be computationally expensive for large networks, as it involves optimal transport calculations for each edge. Here are some tips:

* **Start small**: Test on small networks or subgraphs first
* **Use mode="layers"**: If you only need per-layer analysis, this avoids processing the full core network
* **Adjust alpha**: Lower values of alpha (e.g., 0.3) can be faster to compute
* **Reduce iterations**: For Ricci flow, start with fewer iterations (e.g., 5-10) and increase as needed
* **Parallel computation**: GraphRicciCurvature supports parallel computation via ``backend_kwargs={"proc": 4}`` (use number of CPU cores)

Example with parallel computation:

.. code-block:: python

    # Use 4 CPU cores for parallel computation
    result = net.compute_ollivier_ricci(
        mode="core",
        alpha=0.5,
        backend_kwargs={"proc": 4}
    )

References
----------

* Ni, C. C., Lin, Y. Y., Gao, J., Gu, X. D., & Saucan, E. (2015). Ricci curvature of the Internet topology. *2015 IEEE Conference on Computer Communications (INFOCOM)*, 2758-2766.

* Ni, C. C., Lin, Y. Y., Luo, F., & Gao, J. (2019). Community detection on networks with Ricci flow. *Scientific Reports*, 9(1), 9984.

* Ollivier, Y. (2009). Ricci curvature of Markov chains on metric spaces. *Journal of Functional Analysis*, 256(3), 810-864.

* GraphRicciCurvature library: https://github.com/saibalmars/GraphRicciCurvature

See Also
--------

* :doc:`ricci_visualization` - Ricci-flow-based visualization utilities
* :doc:`user_guide/community_detection` - Community detection algorithms
* :doc:`multilayer_concepts` - Understanding multilayer networks
* :doc:`supra` - Supra-adjacency matrix representation
