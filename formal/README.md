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
| `Py3plex.Optimizer.filter_compose` | `Py3plex/Optimizer/FilterFusion.lean` | Two `List.filter` calls compose into one with a conjunctive predicate |
| `Py3plex.Optimizer.filterFusion` | `Py3plex/Optimizer/FilterFusion.lean` | **Main theorem**: two adjacent `Plan.filter` nodes are semantically equal to a single filter with a conjunctive predicate |
| `Py3plex.Optimizer.filterFusion_length` | `Py3plex/Optimizer/FilterFusion.lean` | Filter fusion preserves the result length |

All proofs are fully machine-checked; none use `sorry`, `admit`, or unsafe
axioms.

### What is NOT proved in Phase 1

* The Python `CombineAdjacentFilters` optimizer rule always emits exactly the
  transformation proved here.
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
which merges two consecutive `LogicalFilter` nodes by combining their predicate
lists).

Lean proves the transformation is correct in the abstract model.  Whether the
Python rule is always invoked correctly is a Python-level question that Phase 1
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
| Phase 1 (current) | Abstract model, `filterFusion` theorem, CI enforcement |
| Phase 2 | Python-to-Lean AST serialization; compare optimizer output against Lean model |
| Phase 3 | Certificate replay: optimizer emits a Lean certificate, Lean verifies it |
| Phase 4 | Broader coverage: multi-step rewrites, cost model, other optimizer rules |

Formalization of NetworkX internals, floating-point numerics, temporal dynamics,
uncertainty quantification, or centrality algorithms is explicitly out of scope
for all near-term phases.
