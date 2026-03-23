Appendix C: Detailed Validation Scripts
========================================

This appendix complements :ref:`testing-chapter` by grouping script patterns by methodological principle rather than by tool catalog.

What to Run First
-----------------

Prioritize, in order:

1. conservation/invariant checks on small fixtures,
2. differential checks across equivalent APIs,
3. perturbation/UQ stability checks for claim-bearing outputs.

These three catch most analytical drift early.

Principle 1: Conservation and Structural Invariants
---------------------------------------------------

Use compact tests to verify invariants such as probability conservation in random walks, population conservation in SIS/SIR trajectories, and valid bounds for modularity or centrality outputs.

.. code-block:: python

    # pseudocode: conservation-style check
    result = run_model(network, seed=42)
    assert invariant_holds(result)

Principle 2: Differential Equivalence
-------------------------------------

Check that equivalent analysis paths agree when they should.

.. code-block:: python

    # pseudocode: equivalent query paths
    a = dsl_query_path(network)
    b = equivalent_graph_ops_path(network)
    assert compare_semantics(a, b)

Principle 3: Stability Under Perturbation
-----------------------------------------

For rank- or partition-based claims, include perturbation or bootstrap checks and report what changed.

.. code-block:: python

    # pseudocode: stability envelope
    base = compute_ranking(network)
    perturbed = [compute_ranking(perturb(network, seed=s)) for s in seeds]
    summarize_rank_stability(base, perturbed)

Methodological Framing
----------------------

These scripts are not only software QA artifacts. They are methodological controls that bound overinterpretation by testing whether conclusions survive equivalent formulations, perturbations, and known invariants.

For executable, repository-specific script variants, see the ``tests/`` and ``tests/property/`` directories referenced in :ref:`testing-chapter`.
