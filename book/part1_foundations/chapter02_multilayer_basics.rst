.. _multilayer-basics-chapter:

Multilayer Basics: Semantics Before Computation
================================================

This chapter defines multilayer network objects and highlights semantic mistakes that produce misleading analyses.

Formal Object
-------------

A multilayer network can be represented as :math:`\mathcal{M} = (V, L, V_M, E_{intra}, E_{inter})`, where:

* :math:`V` is the set of physical entities,
* :math:`L` is the set of layers,
* :math:`V_M \subseteq V \times L` is the set of node replicas,
* :math:`E_{intra}` links replicas within a layer,
* :math:`E_{inter}` links replicas across layers.

Concept vs Implementation
-------------------------

**Concept:** node replicas are analytical units that encode context.

**py3plex implementation:** nodes are stored as ``(node, layer)`` pairs in the core graph, so many operations naturally return replica-level results.

Do not silently reinterpret replica counts as physical-node counts.

Replica Semantics: The First Major Pitfall
------------------------------------------

If a physical node appears in three layers, it has three replicas. This matters for:

* counts,
* degree interpretation,
* top-k selection,
* community assignments.

A frequent novice error is to compute top hubs globally, then report them as physical entities without de-duplicating by base node.

Degree Is Ambiguous in Multilayer Contexts
------------------------------------------

At least three notions of degree can be relevant:

* **intra-layer degree** (within one layer),
* **inter-layer degree** (coupling/transfer links),
* **aggregate degree** (combined).

In py3plex workflows, aggregate degree is often the default unless per-layer operations are explicitly applied.

Interpretive warning: aggregate degree is not necessarily a better statistic; it is a different statistic.

Coverage Semantics and False Certainty
--------------------------------------

Coverage filters encode cross-group logic:

* ``all``: intersection,
* ``any``: union,
* thresholded modes (``at_least``, ``fraction``): partial overlap.

``all`` is strict and can yield very small result sets. This is often interpreted as "only a few robust nodes," but it may instead reflect harsh filtering under high layer heterogeneity.

Global vs Per-Layer Operations
------------------------------

Two analyses can be correct yet answer different questions:

* **global** community detection: seeks communities spanning layers,
* **per-layer** detection: compares community structure between layers.

Neither is universally preferred. Choose based on hypothesis, not convenience.

Minimal Sanity Checklist
------------------------

Before trusting any multilayer output:

1. Confirm whether reported units are replicas or physical nodes.
2. State which degree semantics are used.
3. State whether operations were global or grouped by layer.
4. Report coverage mode and thresholds.
5. Provide at least one alternative analysis path as a robustness check.

Why This Chapter Matters
------------------------

Most downstream errors are not coding errors. They are semantic errors introduced before algorithm choice. Getting these distinctions right is the main precondition for meaningful multilayer inference.
