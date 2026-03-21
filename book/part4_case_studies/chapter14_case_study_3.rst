Case Study 3 — Transportation Network: Resilience Under Layer Disruption
=========================================================================

.. admonition:: workflow template
   :class: note

   This chapter provides a workflow template for transportation multilayer analysis with an emphasis on contestable assumptions and resilience interpretation.

Readers adapting this template should document transfer-cost assumptions, temporal aggregation choices, and missing-data handling before interpreting ranking outputs.

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

Contestable choice: transfer edges are modeled with fixed penalty weights. In practice, transfer costs vary by time, congestion, and accessibility.

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

Why Multilayer Changed the Conclusion
-------------------------------------

Flattened analysis overemphasized metro-core stations. The multilayer disruption comparison identified secondary interchange nodes that become dominant under bus or metro degradation.

Fragile Assumptions
-------------------

1. Temporal aggregation can erase peak-hour fragility.
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

For transport planning questions about disruption, multilayer scenario analysis is often more informative than flattened efficiency metrics.

Local Caveat
------------

This workflow is strongest for topology-driven resilience screening. It is not a substitute for full demand, schedule, or behavioral models.
