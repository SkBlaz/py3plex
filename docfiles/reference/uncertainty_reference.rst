Uncertainty Reference
=====================

Complete reference for py3plex's first-class uncertainty support.

.. note::
   For practical examples, see :doc:`../examples/index` > Uncertainty Examples.
   This page is a complete API reference.

Overview
--------

py3plex provides native uncertainty support through two complementary systems:

1. **High-level API:** ``StatSeries``, ``StatMatrix`` for arrays of uncertain values
2. **Low-level primitives:** ``UncertainValue`` for individual uncertain scalars

This reference covers the low-level primitives and canonical schema.

UncertainValue Class
--------------------

**Module:** ``py3plex.uncertainty.models``

The ``UncertainValue`` class represents a single scalar value that may be deterministic or uncertain.

Constructor
~~~~~~~~~~~

.. code-block:: python

    UncertainValue(kind: str, params: dict)

**Parameters:**

* ``kind`` (str) — Distribution type: ``"deterministic"``, ``"bernoulli"``, ``"normal"``, ``"empirical"``
* ``params`` (dict) — Distribution parameters (depends on ``kind``)

**Supported Kinds:**

Deterministic
^^^^^^^^^^^^^

Fixed value with no uncertainty.

**Parameters:**

* ``value`` (float) — The fixed value

**Example:**

.. code-block:: python

    from py3plex.uncertainty import UncertainValue
    
    v = UncertainValue(kind="deterministic", params={"value": 5.0})
    print(v.mean())  # 5.0
    print(v.var())   # 0.0

Bernoulli
^^^^^^^^^

Binary distribution (0 or 1). Useful for edge existence probability.

**Parameters:**

* ``p`` (float) — Probability of 1 (must be in [0, 1])

**Example:**

.. code-block:: python

    # Edge exists with 80% probability
    v = UncertainValue(kind="bernoulli", params={"p": 0.8})
    print(v.mean())  # 0.8
    print(v.var())   # 0.16

Normal (Gaussian)
^^^^^^^^^^^^^^^^^

Normal distribution. Useful for uncertain edge weights or measurements.

**Parameters:**

* ``mu`` (float) — Mean
* ``sigma`` (float) — Standard deviation (must be >= 0)

**Example:**

.. code-block:: python

    # Edge weight ~ N(2.5, 0.5)
    v = UncertainValue(kind="normal", params={"mu": 2.5, "sigma": 0.5})
    print(v.mean())  # 2.5
    print(v.std())   # 0.5

Empirical
^^^^^^^^^

Distribution from observed samples. Useful for bootstrap or measured data.

**Parameters:**

* ``samples`` (array-like) — Observed values

**Example:**

.. code-block:: python

    import numpy as np
    
    # Distribution from measurements
    data = np.array([1.2, 2.3, 2.5, 2.8, 3.1])
    v = UncertainValue(kind="empirical", params={"samples": data})
    print(v.mean())  # 2.38

Methods
~~~~~~~

mean() -> float
^^^^^^^^^^^^^^^

Compute the expected value (mean) of the distribution.

**Returns:** Mean value as float

**Example:**

.. code-block:: python

    v = UncertainValue(kind="normal", params={"mu": 5.0, "sigma": 1.0})
    print(v.mean())  # 5.0

var() -> float
^^^^^^^^^^^^^^

Compute the variance of the distribution.

**Returns:** Variance as float (0.0 for deterministic)

**Example:**

.. code-block:: python

    v = UncertainValue(kind="normal", params={"mu": 5.0, "sigma": 2.0})
    print(v.var())  # 4.0

std() -> float
^^^^^^^^^^^^^^

Compute the standard deviation of the distribution.

**Returns:** Standard deviation as float

**Example:**

.. code-block:: python

    v = UncertainValue(kind="normal", params={"mu": 5.0, "sigma": 2.0})
    print(v.std())  # 2.0

sample(rng, n=1) -> np.ndarray
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Draw random samples from the distribution.

**Parameters:**

* ``rng`` (np.random.Generator) — NumPy random generator
* ``n`` (int) — Number of samples to draw (default: 1)

**Returns:** Array of samples with shape ``(n,)``

**Example:**

.. code-block:: python

    import numpy as np
    
    v = UncertainValue(kind="normal", params={"mu": 0.0, "sigma": 1.0})
    rng = np.random.default_rng(42)
    samples = v.sample(rng, n=100)
    print(samples.mean())  # ~0.0

is_deterministic() -> bool
^^^^^^^^^^^^^^^^^^^^^^^^^^

Check if the value is deterministic (no uncertainty).

**Returns:** True if deterministic, False otherwise

**Example:**

.. code-block:: python

    v1 = UncertainValue(kind="deterministic", params={"value": 5.0})
    print(v1.is_deterministic())  # True
    
    v2 = UncertainValue(kind="normal", params={"mu": 5.0, "sigma": 1.0})
    print(v2.is_deterministic())  # False

Serialization Methods
~~~~~~~~~~~~~~~~~~~~~

to_dict() -> dict
^^^^^^^^^^^^^^^^^

Convert to JSON-serializable dictionary.

**Returns:** Dictionary with ``kind`` and ``params`` keys

**Example:**

.. code-block:: python

    v = UncertainValue(kind="normal", params={"mu": 5.0, "sigma": 1.0})
    d = v.to_dict()
    # {'kind': 'normal', 'params': {'mu': 5.0, 'sigma': 1.0}}

from_dict(data: dict) -> UncertainValue
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create UncertainValue from dictionary (class method).

**Parameters:**

* ``data`` (dict) — Dictionary with ``kind`` and ``params``

**Returns:** UncertainValue instance

**Example:**

.. code-block:: python

    d = {'kind': 'normal', 'params': {'mu': 5.0, 'sigma': 1.0}}
    v = UncertainValue.from_dict(d)

from_value(value) -> UncertainValue
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create UncertainValue from scalar or existing UncertainValue (class method).

**Parameters:**

* ``value`` (float, int, or UncertainValue) — Value to wrap

**Returns:** UncertainValue instance

**Example:**

.. code-block:: python

    # Wrap scalar
    v1 = UncertainValue.from_value(5.0)  # deterministic
    
    # Pass through UncertainValue
    v2 = UncertainValue.from_value(v1)  # returns v1 unchanged

Special Methods
~~~~~~~~~~~~~~~

__float__() -> float
^^^^^^^^^^^^^^^^^^^^

Convert to float (returns mean value). Enables backward compatibility.

**Example:**

.. code-block:: python

    v = UncertainValue(kind="normal", params={"mu": 5.0, "sigma": 1.0})
    x = float(v)  # 5.0

Schema Constants
----------------

**Module:** ``py3plex.uncertainty.schema``

Canonical attribute names for uncertainty-aware network data.

Edge Attributes
~~~~~~~~~~~~~~~

Standard attributes for edges with uncertainty:

* ``WEIGHT`` (``"weight"``) — Deterministic weight (legacy)
* ``WEIGHT_MEAN`` (``"weight_mean"``) — Mean of weight distribution
* ``WEIGHT_VAR`` (``"weight_var"``) — Variance of weight distribution
* ``WEIGHT_STD`` (``"weight_std"``) — Standard deviation of weight
* ``WEIGHT_DIST`` (``"weight_dist"``) — Full weight distribution (UncertainValue)
* ``P_EXIST`` (``"p_exist"``) — Edge existence probability [0, 1]
* ``CERTAINTY`` (``"certainty"``) — Legacy alias for ``P_EXIST``

**Example:**

.. code-block:: python

    from py3plex.uncertainty import schema
    
    edge_data = {
        schema.WEIGHT_MEAN: 2.5,
        schema.WEIGHT_VAR: 0.1,
        schema.P_EXIST: 0.85,
    }

Node Attributes
~~~~~~~~~~~~~~~

Standard attributes for nodes with uncertainty:

* ``NODE_P_EXIST`` (``"p_exist"``) — Node existence probability [0, 1]

**Example:**

.. code-block:: python

    from py3plex.uncertainty import schema
    
    node_data = {
        schema.NODE_P_EXIST: 0.95,
        "label": "Node A",
    }

Computed Statistics Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Standard attributes for computed metrics with uncertainty:

* ``CENTRALITY_MEAN`` (``"centrality_mean"``) — Mean centrality value
* ``CENTRALITY_STD`` (``"centrality_std"``) — Std of centrality
* ``CENTRALITY_DIST`` (``"centrality_dist"``) — Full distribution
* ``COMMUNITY_LABEL`` (``"community"``) — Community assignment (deterministic)
* ``COMMUNITY_STABILITY`` (``"community_stability"``) — Assignment stability [0, 1]

Metadata Attributes
~~~~~~~~~~~~~~~~~~~

Tracking uncertainty estimation:

* ``UNCERTAINTY_SOURCE`` (``"uncertainty_source"``) — Source: ``"bootstrap"``, ``"perturbation"``, etc.
* ``N_SAMPLES`` (``"n_samples"``) — Number of samples/runs used
* ``CONFIDENCE_LEVEL`` (``"confidence_level"``) — Confidence level (e.g., 0.95)

Attribute Groups
~~~~~~~~~~~~~~~~

Immutable sets of attribute names:

* ``EDGE_UNCERTAINTY_ATTRS`` (frozenset) — All edge uncertainty attributes
* ``NODE_UNCERTAINTY_ATTRS`` (frozenset) — All node uncertainty attributes
* ``STAT_UNCERTAINTY_ATTRS`` (frozenset) — All stat uncertainty attributes
* ``METADATA_ATTRS`` (frozenset) — All metadata attributes
* ``ALL_UNCERTAINTY_ATTRS`` (frozenset) — Union of all above

**Example:**

.. code-block:: python

    from py3plex.uncertainty import schema
    
    # Check all edge uncertainty attributes
    for attr in schema.EDGE_UNCERTAINTY_ATTRS:
        print(attr)
    
    # Attribute groups are immutable (frozenset)
    # schema.EDGE_UNCERTAINTY_ATTRS.add("foo")  # raises AttributeError

Schema Helper Functions
-----------------------

is_uncertainty_attr(attr_name: str) -> bool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check if an attribute name is uncertainty-related.

**Parameters:**

* ``attr_name`` (str) — Attribute name to check

**Returns:** True if uncertainty-related, False otherwise

**Example:**

.. code-block:: python

    from py3plex.uncertainty import schema
    
    print(schema.is_uncertainty_attr("weight_mean"))  # True
    print(schema.is_uncertainty_attr("weight"))       # False
    print(schema.is_uncertainty_attr("p_exist"))      # True

is_deterministic_edge(edge_data: dict) -> bool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check if an edge has no uncertainty attributes.

**Parameters:**

* ``edge_data`` (dict) — Edge attribute dictionary

**Returns:** True if deterministic (no uncertainty attrs), False otherwise

**Example:**

.. code-block:: python

    from py3plex.uncertainty import schema
    
    edge1 = {"weight": 1.0}
    print(schema.is_deterministic_edge(edge1))  # True
    
    edge2 = {"weight_mean": 1.0, "weight_var": 0.1}
    print(schema.is_deterministic_edge(edge2))  # False

is_deterministic_node(node_data: dict) -> bool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check if a node has no uncertainty attributes.

**Parameters:**

* ``node_data`` (dict) — Node attribute dictionary

**Returns:** True if deterministic, False otherwise

**Example:**

.. code-block:: python

    from py3plex.uncertainty import schema
    
    node1 = {"label": "A"}
    print(schema.is_deterministic_node(node1))  # True
    
    node2 = {"p_exist": 0.9}
    print(schema.is_deterministic_node(node2))  # False

get_edge_weight(edge_data: dict, default=1.0) -> float
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get edge weight, handling both deterministic and uncertain representations.

**Priority order:**

1. ``weight`` (deterministic, legacy)
2. ``weight_mean`` (uncertain)
3. ``weight_dist.mean()`` (full distribution)
4. ``default`` value

**Parameters:**

* ``edge_data`` (dict) — Edge attribute dictionary
* ``default`` (float) — Default weight if none found (default: 1.0)

**Returns:** Edge weight as float

**Example:**

.. code-block:: python

    from py3plex.uncertainty import schema
    
    edge1 = {"weight": 2.0}
    print(schema.get_edge_weight(edge1))  # 2.0
    
    edge2 = {"weight_mean": 3.5}
    print(schema.get_edge_weight(edge2))  # 3.5
    
    edge3 = {}
    print(schema.get_edge_weight(edge3))  # 1.0 (default)

get_edge_existence_prob(edge_data: dict, default=1.0) -> float
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get edge existence probability.

**Priority order:**

1. ``p_exist``
2. ``certainty`` (legacy)
3. ``default`` value

**Parameters:**

* ``edge_data`` (dict) — Edge attribute dictionary
* ``default`` (float) — Default probability if none found (default: 1.0)

**Returns:** Existence probability as float [0, 1]

**Example:**

.. code-block:: python

    from py3plex.uncertainty import schema
    
    edge1 = {"p_exist": 0.8}
    print(schema.get_edge_existence_prob(edge1))  # 0.8
    
    # Legacy attribute
    edge2 = {"certainty": 0.9}
    print(schema.get_edge_existence_prob(edge2))  # 0.9
    
    edge3 = {}
    print(schema.get_edge_existence_prob(edge3))  # 1.0

get_node_existence_prob(node_data: dict, default=1.0) -> float
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get node existence probability.

**Parameters:**

* ``node_data`` (dict) — Node attribute dictionary
* ``default`` (float) — Default probability if none found (default: 1.0)

**Returns:** Existence probability as float [0, 1]

**Example:**

.. code-block:: python

    from py3plex.uncertainty import schema
    
    node1 = {"p_exist": 0.95}
    print(schema.get_node_existence_prob(node1))  # 0.95
    
    node2 = {}
    print(schema.get_node_existence_prob(node2))  # 1.0

Usage Patterns
--------------

Pattern 1: Storing Uncertain Edge Weights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.uncertainty import UncertainValue, schema
    from py3plex.core import multinet
    
    # Create network
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {"source": "A", "type": "L1"},
        {"source": "B", "type": "L1"},
    ])
    
    # Option 1: Store mean and variance
    net.core_network.add_edge(
        ("A", "L1"), ("B", "L1"),
        **{
            schema.WEIGHT_MEAN: 2.5,
            schema.WEIGHT_VAR: 0.1,
            schema.P_EXIST: 0.9,
        }
    )
    
    # Option 2: Store full distribution
    weight_dist = UncertainValue(kind="normal", params={"mu": 2.5, "sigma": 0.32})
    net.core_network.add_edge(
        ("A", "L1"), ("C", "L1"),
        **{
            schema.WEIGHT_DIST: weight_dist,
            schema.P_EXIST: 0.85,
        }
    )

Pattern 2: Reading Uncertain Edge Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.uncertainty import schema
    
    # Get edge data (handles both deterministic and uncertain)
    for u, v, key, data in network.core_network.edges(keys=True, data=True):
        weight = schema.get_edge_weight(data)
        prob = schema.get_edge_existence_prob(data)
        
        print(f"Edge {u}->{v}: weight={weight}, p_exist={prob}")
        
        # Check if uncertain
        if not schema.is_deterministic_edge(data):
            print(f"  (has uncertainty)")

Pattern 3: Backward Compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.uncertainty import schema
    
    # Old code might use 'certainty'
    legacy_edge = {"weight": 1.5, "certainty": 0.7}
    
    # Schema helpers automatically support legacy attributes
    prob = schema.get_edge_existence_prob(legacy_edge)  # 0.7
    
    # New code should use P_EXIST
    modern_edge = {
        schema.WEIGHT_MEAN: 1.5,
        schema.P_EXIST: 0.7,
    }

See Also
--------

* :doc:`../how-to/compute_statistics` — Computing stats with uncertainty
* :doc:`../examples/index` — Working examples
* :doc:`algorithm_reference` — Algorithms supporting uncertainty

Related Modules
---------------

* ``py3plex.uncertainty.types`` — ``StatSeries``, ``StatMatrix`` for arrays
* ``py3plex.uncertainty.estimation`` — ``estimate_uncertainty()`` helper
* ``py3plex.uncertainty.bootstrap`` — Bootstrap resampling
* ``py3plex.uncertainty.null_models`` — Null model generation
