Case Study 1 — Social Multiplex: Influence vs Brokerage
=========================================================

.. admonition:: workflow template
   :class: note

   This chapter uses a reusable workflow template for social multiplex analysis. The template is intentionally explicit about assumptions so readers can adapt it to their own data.

Research Question
-----------------

How does influence ranking change when friendship, collaboration, and mentorship ties are modeled as separate layers instead of a single flattened graph?

Data and Representation Choices
-------------------------------

We represent each person as replicas across three layers:

* ``friendship``
* ``collaboration``
* ``mentorship``

Contestable choice: inter-layer edges connect replicas of the same person with uniform coupling weight. This simplifies identity continuity but may underrepresent context switching costs.

Baseline: Flattened Analysis
----------------------------

.. code-block:: python

    flat = network.flatten_to_monoplex(method='union')
    # Run standard centrality on flattened graph

Flattened ranking highlights well-connected generalists. It cannot distinguish whether influence comes from one dominant layer or cross-layer brokerage.

Multilayer Analysis
-------------------

.. code-block:: python

    from py3plex.dsl import Q, L

    per_layer = (
        Q.nodes()
         .from_layers(L['friendship'] + L['collaboration'] + L['mentorship'])
         .compute('degree', 'betweenness_centrality')
         .per_layer()
           .top_k(15, 'betweenness_centrality')
         .end_grouping()
         .coverage(mode='at_least', k=2)
         .execute(network)
    )

Key finding: several individuals absent from flattened top-k appear repeatedly as high-brokerage nodes across layers.

Why Multilayer Changed the Result
---------------------------------

Flattening merged semantically different ties and amplified dense collaboration clusters. The multilayer query isolated cross-context connectors that are structurally modest in any single layer but strategically important across layers.

Fragile Assumptions
-------------------

1. Uniform inter-layer coupling may overstate identity continuity.
2. Missingness differs by layer (mentorship ties are often underreported).
3. Top-k thresholds are sensitive to layer size imbalance.

Robustness Checks
-----------------

.. code-block:: python

    uq_result = (
        Q.nodes()
         .compute('betweenness_centrality')
         .uq(method='bootstrap', n_samples=100, seed=42)
         .execute(network)
    )

We treat rank changes within confidence overlap as ambiguous rather than definitive.

Transferable Lesson
-------------------

If the practical question concerns cross-context brokerage, flattened centrality is usually a poor proxy. Layer-aware selection with explicit coverage criteria is more informative.

Local Caveat
------------

This case relies on relatively stable layer definitions. In domains where layer labels are noisy or evolving, the same workflow needs temporal and schema-uncertainty extensions.
