/-!
# Py3plex.DSL.Syntax — Abstract Query Plan Type

Defines the inductive type `Plan α`, a minimal abstract query plan
parameterised over row type `α`.  The type is deliberately small but now covers
the minimum additional operators needed for reachable TODO items:
scan/emptyScan/filter plus project/limit.

## Relation to py3plex Python code

| Lean constructor | Python equivalent |
| ---------------- | ---------------- |
| `Plan.scan`      | `LogicalScanNodes` / `LogicalScanEdges` in `py3plex/optimizer/plan_nodes.py` |
| `Plan.emptyScan` | `LogicalEmptyScan` in the same file |
| `Plan.filter`    | `LogicalFilter` in the same file |
| `Plan.project`   | `LogicalProject` in the same file |
| `Plan.limit`     | `LogicalLimit` in the same file |

Phase 1 does **not** prove that the Python optimizer always emits exactly the
transformations proved here; that correspondence belongs to a later phase.
-/

namespace Py3plex.DSL

/-- An abstract query plan, generic over row type `α`.

    * `scan rows`          — base case: yield a fixed list of rows.
    * `emptyScan`          — known-empty result, matching Python's
                             `LogicalEmptyScan`.
    * `filter p child`     — keep only rows from `child` that satisfy
                             boolean predicate `p`.
    * `project f child`    — row-wise projection/map, abstract counterpart of
                             `LogicalProject`.
    * `limit n child`      — keep at most the first `n` rows, abstract
                             counterpart of `LogicalLimit`.
-/
inductive Plan (α : Type) where
  | scan   : List α → Plan α
  | emptyScan : Plan α
  | filter : (α → Bool) → Plan α → Plan α
  | project : (α → α) → Plan α → Plan α
  | limit : Nat → Plan α → Plan α

end Py3plex.DSL
