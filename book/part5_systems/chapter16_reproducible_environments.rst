Reproducible Environments and Replayable Analysis
==================================================

Reproducibility is an analytical requirement: independent reviewers must be able to re-run your workflow and inspect the same assumptions.

For basic environment setup commands, see Chapter 4. For container/deployment detail, see Appendix B.

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

Link to Scientific Credibility
------------------------------

In multilayer analysis, representation and parameter choices are often contestable. Reproducibility makes those choices inspectable and debateable rather than opaque.
