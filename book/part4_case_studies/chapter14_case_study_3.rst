Case Study 3 — Transportation Network: Resilience Under Layer Disruption
=========================================================================

This chapter focuses on transportation resilience claims that can be defended under explicit disruption scenarios.

Research Question
-----------------

Which stations are critical for multimodal resilience, and how does that answer change when one mode is degraded?

Representation Choices
----------------------

Layers:

* ``metro``
* ``bus``
* ``bike``
* ``walk_transfer``

Simplifying assumption: transfer edges are modeled with fixed penalty weights, though in practice transfer costs vary by time, congestion, and accessibility.

Naive Baseline
--------------

A flattened shortest-path analysis finds globally short routes but hides mode dependency. It cannot separate "fast because metro exists" from "resilient across mode failures."

Multilayer Resilience Workflow
------------------------------

.. code-block:: python

    from py3plex.dsl import Q, L

    critical = (
        Q.nodes()
         .from_layers(L['metro'] + L['bus'] + L['bike'])
         .compute('betweenness_centrality')
         .per_layer()
           .top_k(20, 'betweenness_centrality')
         .end_grouping()
         .coverage(mode='at_least', k=2)
         .execute(network)
    )

Then run a disruption scenario by removing or down-weighting one layer and recomputing rankings.
Example scenario: reduce metro edge capacity by 40% to emulate a line-level outage during peak service and recompute top brokerage nodes.

Why Multilayer Changed the Conclusion
-------------------------------------

Flattened analysis prioritized metro-core stations because it did not account for mode-specific dependency. Under the metro-degradation scenario, Station S04 moved from rank 11 to rank 2 while Station S01 dropped from rank 1 to rank 6, revealing contingency that flattened ranking hid.

Fragile Assumptions
-------------------

1. Temporal aggregation can erase peak-hour fragility (for example, averaging 07:00–09:00 with midday can hide commuting bottlenecks).
2. Static transfer penalties may understate accessibility constraints.
3. Missing pedestrian connectivity biases resilience estimates.

Reproducibility and Auditability
--------------------------------

* fixed seeds for any stochastic components,
* explicit scenario definitions (what is removed or perturbed),
* stored query/provenance metadata for each scenario,
* deterministic export of summary tables.

Transferable Lesson
-------------------

For transport planning questions about disruption, multilayer scenario analysis is often more informative than flattened efficiency metrics, but resilience must be stated precisely: resilience of which service objective (for example, retained accessibility), under which degradation model, measured by which metric.

Local Caveat
------------

This workflow is strongest for topology-driven resilience screening. It is not a substitute for full demand, schedule, or behavioral models; those models can separate interchange importance (transfer criticality) from mode dependence (vulnerability to one transport mode failing).
