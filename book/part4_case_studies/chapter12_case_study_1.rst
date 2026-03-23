Case Study 1 — Social Multiplex: Influence vs Brokerage
=========================================================

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

Tiny Result Table (Illustrative)
--------------------------------

+-------------------------------+-----------------------------+-------------------------------------+
| Rank position                | Flattened top-k             | Multilayer brokerage top-k          |
+===============================+=============================+=====================================+
| 1                            | P07                         | P12                                 |
+-------------------------------+-----------------------------+-------------------------------------+
| 2                            | P03                         | P07                                 |
+-------------------------------+-----------------------------+-------------------------------------+
| 3                            | P11                         | P19                                 |
+-------------------------------+-----------------------------+-------------------------------------+
| 4                            | P12                         | P03                                 |
+-------------------------------+-----------------------------+-------------------------------------+
| 5                            | P25                         | P11                                 |
+-------------------------------+-----------------------------+-------------------------------------+

Interpretive shift: P12 looks secondary in flattened degree but becomes first-ranked under cross-layer brokerage because it links mentorship and collaboration substructures.

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
Under bootstrap/UQ, the top-3 set remained stable while positions 4–8 swapped frequently, so we report a robust core and a contingent middle tier rather than a single rigid ordering.

Transferable Lesson
-------------------

If the practical question concerns cross-context brokerage, flattened centrality is usually a poor proxy. Layer-aware selection with explicit coverage criteria is more informative.

Local Caveat
------------

This case relies on relatively stable layer definitions. If labels such as "mentorship" and "collaboration" are noisy or drift over time, cross-layer brokerage can be spuriously inflated or suppressed, directly altering who appears "strategically central."
