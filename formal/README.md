# Py3plex Formal Verification (Phase 1)

This directory contains a self-contained [Lean 4](https://leanprover.github.io/)
project that machine-checks selected semantic properties of py3plex's query /
optimizer architecture.

---

## Contents

```
formal/
├── lean-toolchain              Exact Lean release pin
├── lakefile.toml               Lake project definition
├── lake-manifest.json          Reproducible dependency lock (no external deps)
├── README.md                   This file
├── Py3plex.lean                Root import (entry point)
└── Py3plex/
    ├── DSL/
    │   ├── Syntax.lean         Abstract Plan type
    │   └── Semantics.lean      Plan.eval + basic correctness theorems
    └── Optimizer/
        └── FilterFusion.lean   Filter-fusion equivalence theorem
```

---

## Purpose

The goal of Phase 1 is to establish a minimal, reproducible Lean formalization
of the abstract semantics underlying py3plex's query optimizer, and to prove at
least one non-trivial optimizer equivalence property by machine-checked
mathematical proof.

---

## Scope of Phase 1

### What IS proved

| Theorem | File | Statement |
| ------- | ---- | --------- |
| `Plan.eval_scan` | `Py3plex/DSL/Semantics.lean` | Evaluating a scan returns the original rows |
| `Plan.eval_filter` | `Py3plex/DSL/Semantics.lean` | Evaluating a filter applies the predicate to the child's result |
| `Plan.filter_const_true` | `Py3plex/DSL/Semantics.lean` | Filtering with `fun _ => true` is the identity |
| `Plan.filter_const_false` | `Py3plex/DSL/Semantics.lean` | Filtering with `fun _ => false` yields `[]` |
| `Plan.filter_empty_scan` | `Py3plex/DSL/Semantics.lean` | Filtering *any* predicate over an empty scan yields `[]` (models `ShortCircuitEmptyLayer`) |
| `Py3plex.Optimizer.filter_compose` | `Py3plex/Optimizer/FilterFusion.lean` | Two `List.filter` calls compose into one with a conjunctive predicate |
| `Py3plex.Optimizer.filterFusion` | `Py3plex/Optimizer/FilterFusion.lean` | **Main theorem**: two adjacent `Plan.filter` nodes are semantically equal to a single filter with a conjunctive predicate |
| `Py3plex.Optimizer.filterFusion_length` | `Py3plex/Optimizer/FilterFusion.lean` | Filter fusion preserves the result length |

All proofs are fully machine-checked; none use `sorry`, `admit`, or unsafe
axioms.

### What is NOT proved in Phase 1

* The Python `CombineAdjacentFilters` optimizer rule always emits exactly the
  transformation proved here.
* The Python `ShortCircuitEmptyLayer` rule always emits exactly the
  transformation proved by `Plan.filter_empty_scan` (the Lean theorem proves
  the abstract model; Python-level invocation correctness is out of scope).
* Any property of NetworkX, centrality algorithms, floating-point numerics,
  temporal dynamics, or uncertainty quantification.
* End-to-end correctness of the full py3plex pipeline.

Python–Lean conformance (certificate replay, schema alignment) belongs to a
later phase.

---

## Relationship to py3plex Python code

The Lean `Plan` type abstracts:

| Lean | Python (`py3plex/optimizer/`) |
| ---- | ----------------------------- |
| `Plan.scan` | `LogicalScanNodes` / `LogicalScanEdges` in `plan_nodes.py` |
| `Plan.filter` | `LogicalFilter` in `plan_nodes.py` |

The `filterFusion` theorem models the `CombineAdjacentFilters` rule in
`py3plex/optimizer/rules.py` (class `CombineAdjacentFilters`, method `apply`,
which merges two consecutive `LogicalFilter` nodes by combining their
`conditions` lists in inner-then-outer order).

The `filter_empty_scan` theorem models the `ShortCircuitEmptyLayer` rule in
`py3plex/optimizer/rules.py` (class `ShortCircuitEmptyLayer`, which replaces
any `LogicalFilter` whose child scan has an empty layer set with a
`LogicalEmptyScan` node).  The Lean proof captures the key semantic insight:
`(Plan.filter p (Plan.scan [])).eval = []` — filtering *any* predicate over an
empty input always returns the empty list.

Lean proves each transformation is correct in the abstract model.  Whether the
Python rules are always invoked correctly is a Python-level question that Phase 1
does not address.

---

## Prerequisites for contributors

* **Normal py3plex users do not need Lean.**  The Python package is a standard
  `pip install py3plex` and Lean is not a runtime dependency.

* For contributors who want to build or extend the Lean formalization:
  * [Elan](https://github.com/leanprover/elan) — the Lean toolchain manager
    (analogous to `rustup`).  Install with:
    ```sh
    curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y
    source ~/.elan/env   # or restart your shell
    ```
  * Lake — the Lean build system — is bundled with Lean and installed
    automatically by Elan.
  * No other tools are required; the project has no external Lean dependencies.

---

## Local build instructions

```sh
# one-time (or after a machine reset): install Elan
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y
source ~/.elan/env

# build and type-check all proofs
cd formal
lake build
```

Because `lake-manifest.json` is committed with an empty package list (no
external Lean libraries), `lake update` is **not** needed for a reproducible
build.  Run `lake update` only if you intentionally change dependencies.

A successful build means every theorem is fully machine-checked.

---

## Toolchain pinning

`lean-toolchain` contains the exact Lean release:

```
leanprover/lean4:v4.14.0
```

Elan reads this file automatically when you run `lake build` from the `formal/`
directory.

`lake-manifest.json` records the exact dependency set (currently empty — the
project uses only Lean's built-in `Init` / `Std` library).

### Upgrading Lean or adding Mathlib

1. Change the version string in `lean-toolchain`.
2. If adding Mathlib, add it to `lakefile.toml` and run `lake update`, then
   commit the updated `lake-manifest.json`.
3. Fix any API changes in `.lean` source files.
4. Open a pull request; CI will verify the build before merge.

---

## Roadmap for later phases

| Phase | Scope |
| ----- | ----- |
| Phase 1 (current) | Abstract model, `filterFusion` theorem, `filter_empty_scan` theorem, CI enforcement |
| Phase 2 | Extend `Plan` to cover all plan-node types; prove one theorem per optimizer rule |
| Phase 3 | Python-to-Lean AST serialization; compare optimizer output against Lean model |
| Phase 4 | Certificate replay: optimizer emits a Lean certificate, Lean verifies it |
| Phase 5 | End-to-end: composed optimizer preserves `eval` for a full DSL query |

Formalization of NetworkX internals, floating-point numerics, temporal dynamics,
uncertainty quantification, or centrality algorithms is explicitly out of scope
for all near-term phases.

---

## TODO: Steps toward an end-to-end provable base

The items below are ordered from "next immediate win" (concrete Lean work) to
"eventual e2e closure" (Python–Lean bridge).  Each group is a prerequisite for
the one that follows.  Checked items are already done.

### Group 1 — Extend the abstract `Plan` type (Phase 1 extension)

New constructors mirror every `LogicalOp` subclass in
`py3plex/optimizer/plan_nodes.py`.

- [x] `Plan.scan` — models `LogicalScanNodes` / `LogicalScanEdges`
- [x] `Plan.filter` — models `LogicalFilter`
- [ ] `Plan.project` — models `LogicalProject`
- [ ] `Plan.limit` — models `LogicalLimit`
- [ ] `Plan.topK` — models `LogicalTopK`
- [ ] `Plan.orderBy` — models `LogicalOrderBy`
- [ ] `Plan.compute` — models `LogicalCompute`
- [ ] `Plan.aggregate` — models `LogicalAggregate`
- [ ] `Plan.groupByLayer` — models `LogicalGroupByLayer` / `LogicalGroupByLayerPair`
- [ ] `Plan.coverage` — models `LogicalCoverage`
- [ ] `Plan.layerFilter` — models `LogicalLayerFilter`
- [ ] `Plan.uq` — models `LogicalUQ`
- [ ] `Plan.emptyScan` — models `LogicalEmptyScan`

### Group 2 — One theorem per optimizer rule (Phase 2)

One machine-checked theorem per rule class in `py3plex/optimizer/rules.py`.
The two checked items are already proved; the rest are open.

- [x] `filterFusion` ↔ `CombineAdjacentFilters`
- [x] `filter_empty_scan` ↔ `ShortCircuitEmptyLayer`
- [ ] `filter_pushdown_compute` ↔ `PushFilterBelowCompute`  
      Statement: `filter p (compute f plan)`.eval = `compute f (filter (p ∘ f) plan)`.eval  
      (when predicate does not depend on a freshly computed column)
- [ ] `layer_filter_pushdown_compute` ↔ `PushLayerFilterBelowCompute`
- [ ] `filter_pushdown_aggregate` ↔ `PushFilterBelowAggregate`
- [ ] `filter_reorder_selectivity` ↔ `ReorderFiltersBySelectivity`  
      Statement: reordering independent filters preserves semantics
- [ ] `orderby_limit_to_topk` ↔ `ConvertOrderByLimitToTopK`  
      Statement: `limit k (orderBy key plan)`.eval = `topK k key plan`.eval
- [ ] `remove_redundant_project` ↔ `RemoveRedundantProject`  
      Statement: `project id plan`.eval = `plan`.eval
- [ ] `early_limit_pushdown` ↔ `EarlyLimitPushdown`  
      Statement: `limit k (compute f plan)`.eval = `compute f (limit k plan)`.eval  
      (when compute does not change ordering)
- [ ] `aggregate_hash_equiv` ↔ `ConvertAggregateToHashIfSmallGroups`
- [ ] `cached_centrality_equiv` ↔ `UseCachedCentralityIfAvailable`
- [ ] `collapse_per_layer_scan` ↔ `CollapsePerLayerIntoScanPartition`
- [ ] `coverage_bitmask_equiv` ↔ `ConvertCoverageToBitmaskAggregation`
- [ ] `uq_shared_base` ↔ `ConvertUQComputeToSharedBaseCompute`
- [ ] `merge_computes` ↔ `MergeMultipleComputesIntoSinglePass`

### Group 3 — Python–Lean AST bridge (Phase 3)

Makes the Lean model executable against real optimizer output without running
Lean's kernel on production data.

- [ ] Add a Python serializer (`py3plex/optimizer/lean_export.py`) that converts
      any `LogicalOp` tree to a stable s-expression / JSON format.
- [ ] Add a Lean `#eval`-level reader that reconstructs a `Plan` value from that
      format at proof-check time.
- [ ] Extend `tests/test_formal_phase1_alignment.py` with a round-trip test: run
      a toy query through the Python optimizer, serialize, deserialize in Lean,
      assert `.eval` of before-plan equals `.eval` of after-plan.
- [ ] Add a CI step (`lake script run check_roundtrip`) that invokes the above
      test automatically on every push.

### Group 4 — Certificate replay (Phase 4)

Each Python rule application produces a self-contained Lean snippet that Lean
can verify independently of py3plex's runtime.

- [ ] Define a `Certificate` datatype in Lean: `{ before : Plan, after : Plan,
      proof : before.eval = after.eval }`.
- [ ] Have the Python `RuleEngine` emit a certificate JSON file alongside normal
      optimizer output (opt-in flag `--emit-lean-certs`).
- [ ] Write a Lean `#check`-level verifier that reads the certificate JSON and
      type-checks the proof term.
- [ ] CI verifies every emitted certificate on the example queries in
      `tests/test_optimizer_submodules.py`.

### Group 5 — End-to-end query equivalence (Phase 5)

The ultimate goal: machine-check that the composed optimizer produces a plan
whose `eval` equals the original plan's `eval` for the full DSL query language.

- [ ] Define `DSLQuery` in Lean as a structured query built from the DSL v2
      builder's output (covers nodes/edges, `from_layers`, `where`, `compute`,
      `order_by`, `limit`).
- [ ] Prove `RuleEngine.sound`: for any `DSLQuery q`, applying all rules in
      sequence yields a plan `q'` such that `q'.eval = q.eval`.
- [ ] Prove `Plan.eval_deterministic`: given the same input network,
      `plan.eval` always returns the same result (referential transparency of
      the abstract model).
- [ ] Prove or assume (as an axiom) `Python.conformsToModel`: the Python
      `LogicalOp.execute()` output agrees with `Plan.eval` on all inputs covered
      by the Lean model (requires the AST bridge from Group 3).
- [ ] Compose the above to obtain: "the end-to-end py3plex query pipeline
      returns results consistent with the abstract Lean semantics."

### Non-goals (explicitly out of scope forever)

These items are excluded to keep the formalization tractable:

* Correctness of NetworkX's graph algorithms.
* Floating-point precision of centrality computations.
* Temporal dynamics or uncertainty quantification semantics.
* I/O format parsing correctness.
* Any property that requires modelling Python's object model or mutable state.
