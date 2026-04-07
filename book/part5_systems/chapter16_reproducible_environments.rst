Reproducible Environments and Replayable Analysis
==================================================

Reproducibility is an analytical requirement: independent reviewers must be able to re-run your workflow and verify the assumptions made and parameters used in the analysis.

For basic environment setup commands, see Chapter 5. For container/deployment detail, see Appendix B.

Reproducibility Stack
---------------------

A reproducible py3plex study should preserve:

1. dependency versions,
2. data snapshots or immutable references,
3. query definitions and parameters,
4. random seeds,
5. execution metadata/provenance.

Minimal Practice Pattern
------------------------

* pin package versions in environment files,
* record py3plex version and Python version in outputs,
* store query text/AST and parameter bindings,
* store seeds for stochastic methods,
* save result artifacts with timestamps and scenario labels.

What Reproducibility Does Not Guarantee
---------------------------------------

A replayable pipeline can still encode weak assumptions. Reproducibility supports auditability; it does not prove substantive validity.

Common Failure Modes
--------------------

* hidden notebook state,
* unpinned dependencies,
* overwritten intermediate files,
* undocumented manual edits,
* inconsistent data extraction windows.

Mitigation
----------

* use scriptable pipelines over ad-hoc notebook-only workflows,
* keep immutable raw inputs separate from derived data,
* include an explicit run manifest with versions, seeds, and hashes.

Concrete Run-Manifest Example
-----------------------------

.. code-block:: yaml

    run_id: social_multiplex_2026_03_22_001
    py3plex_version: 1.1.6
    python_version: 3.12.3
    git_commit: f2ffa0813a9c
    dataset_checksum: sha256:2a0c...9f4b
    query_ast_hash: 4f8a73c2b1d8e9aa
    seed: 42
    output_bundle: results/social_multiplex_2026_03_22_001.bundle.json.gz

From DSL execution, preserve at minimum: query AST hash, bound parameters, layer scope, seed/randomness configuration, and network fingerprint fields (node/edge/layer counts).

Link to Scientific Credibility
------------------------------

In multilayer analysis, representation and parameter choices are often contestable. Reproducibility makes those choices inspectable and debatable rather than opaque.
Counterexample: two teams can reproduce the same flattened-ranking script bit-for-bit and still reach a substantively invalid conclusion if the chosen representation erased the layer semantics needed for the scientific question.
