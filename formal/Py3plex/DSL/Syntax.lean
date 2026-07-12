/-!
# Py3plex.DSL.Syntax — Abstract Query Plan Type

Defines the inductive type `Plan α`, a minimal abstract query plan
parameterised over row type `α`.  The type is deliberately small: only a
base-case scan and a filter step are included.  This is enough to state and
machine-check optimizer equivalence theorems.

## Relation to py3plex Python code

| Lean constructor | Python equivalent |
| ---------------- | ---------------- |
| `Plan.scan`      | `LogicalScanNodes` / `LogicalScanEdges` in `py3plex/optimizer/plan_nodes.py` |
| `Plan.filter`    | `LogicalFilter` in the same file |

Phase 1 does **not** prove that the Python optimizer always emits exactly the
transformations proved here; that correspondence belongs to a later phase.
-/

namespace Py3plex.DSL

/-- An abstract query plan, generic over row type `α`.

    * `scan rows`       — base case: yield a fixed list of rows.
    * `filter p child`  — keep only rows from `child` that satisfy
                          boolean predicate `p`.
-/
inductive Plan (α : Type) where
  | scan   : List α → Plan α
  | filter : (α → Bool) → Plan α → Plan α

end Py3plex.DSL
