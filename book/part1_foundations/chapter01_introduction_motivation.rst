Introduction: Why Multilayer Modeling Changes Results
======================================================

Most network tutorials begin with capabilities. This chapter begins with failure: what single-layer analysis gets wrong when relationships are heterogeneous.

Problem Framing
---------------

In many domains, edges carry incompatible semantics. Consider a hospital contact network where one layer records formal care-team coordination, one records informal consultation, and one records shared-shift overlap. Flattening those layers into one tie type mixes institutional structure, social behavior, and scheduling artifacts.

Flattening these into one graph is not just information loss. It changes the estimand. A centrality score in a flattened graph answers a different question than a score on a structured multilayer representation, and mathematically replaces layer-conditioned adjacency operators with a single aggregate operator.

A Running Contrast: Flattened vs Multilayer
-------------------------------------------

Consider a commuter system with rail and bus layers:

* In a flattened graph, high transfer stations can dominate centrality by construction.
* In a multilayer model, we can separate within-mode influence from transfer dependence.

The practical consequence is interpretive: "important node" may mean resilient hub, fragile bottleneck, or mode-bridging artifact depending on representation.

Concrete estimand shift: in a flattened commuter graph, Station X can rank #2 by aggregate betweenness because all transfer traffic is merged, while in the multilayer representation it can drop below the top 20 in metro-only betweenness and rise to #1 in cross-layer brokerage. The metric name is similar, but the estimand is not.

What py3plex Contributes (and What It Does Not)
-----------------------------------------------

py3plex provides a multilayer data model and analysis interfaces that make these distinctions executable in Python workflows.

It does **not** remove modeling judgment. You still choose:

* how layers are defined,
* what inter-layer edges mean,
* whether approximation is acceptable,
* which uncertainty quantification method is relevant.

These choices are methodological, not merely software settings.

Three Questions to Carry Through the Book
-----------------------------------------

1. **Representation:** Is a layer boundary meaningful, or only convenient?
2. **Inference:** Does an algorithm estimate what we think it estimates under this representation?
3. **Credibility:** Are the results stable under perturbation, alternative parameterizations, and reproducibility constraints?

Audience and Prerequisites
--------------------------

This text is aimed at graduate researchers and practitioners who already use graph analytics and now need multilayer rigor. We assume:

* Python proficiency,
* familiarity with basic graph metrics,
* willingness to inspect assumptions rather than accept defaults.

Chapter Roadmap
---------------

* Chapter 3 formalizes multilayer semantics and common traps.
* Chapter 4 explains py3plex design trade-offs.
* Part II moves to practical workflows.
* Part III focuses on DSL reasoning.
* Part IV turns methods into domain arguments through case studies.

The next chapter provides the semantic rules that make these distinctions operational rather than rhetorical.
