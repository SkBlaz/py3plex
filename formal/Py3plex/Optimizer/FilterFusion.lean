/-!
# Py3plex.Optimizer.FilterFusion — Filter-Fusion Equivalence Theorem

## What this file proves

`Plan.filter p (Plan.filter q child)` is semantically equivalent to
`Plan.filter (fun row => q row && p row) child`.

In other words, two consecutive filter steps can always be *fused* into a
single filter step whose predicate is the conjunction of the two original
predicates.

## Relation to the Python optimizer

The Python implementation of this transformation is `CombineAdjacentFilters`
in `py3plex/optimizer/rules.py` (method `apply`, lines 157–171).  That rule
merges two consecutive `LogicalFilter` nodes by concatenating their predicate
lists.

**Phase 1 boundary**: Lean proves the transformation in the abstract `Plan`
model.  Phase 1 does *not* prove that the Python optimizer always emits
exactly this transformation; Python–Lean conformance belongs to a later phase.

## Notes on predicate order

`List.filter` eliminates elements for which the predicate returns `false`.
Applying `filter q` first and then `filter p` keeps exactly those elements
for which *both* `q` and `p` return `true`.  The combined predicate is
therefore `fun row => q row && p row` (inner predicate first in the `&&`).
-/

import Py3plex.DSL.Semantics

namespace Py3plex.Optimizer

open Py3plex.DSL

-- ---------------------------------------------------------------------------
-- Helper lemma: composition of List.filter
-- ---------------------------------------------------------------------------

/-- Composing two `List.filter` calls is equivalent to a single filter whose
    predicate is the conjunction of both, with the *inner* predicate on the
    left of `&&`. -/
theorem filter_compose {α : Type} (p q : α → Bool) (l : List α) :
    (l.filter q).filter p = l.filter (fun a => q a && p a) := by
  induction l with
  | nil         => rfl
  | cons a as ih =>
    simp only [List.filter_cons]
    cases h₁ : q a <;> cases h₂ : p a <;> simp_all

-- ---------------------------------------------------------------------------
-- Main theorem: Filter Fusion
-- ---------------------------------------------------------------------------

/-- **Filter Fusion** (the primary optimizer theorem).

    Two adjacent `Plan.filter` nodes are semantically equivalent to a single
    `Plan.filter` whose predicate is the conjunction of both predicates,
    inner predicate first.

    This is the abstract counterpart of `CombineAdjacentFilters` in
    `py3plex/optimizer/rules.py`. -/
theorem filterFusion {α : Type} (p q : α → Bool) (child : Plan α) :
    (Plan.filter p (Plan.filter q child)).eval =
      (Plan.filter (fun row => q row && p row) child).eval := by
  simp only [Plan.eval_filter, filter_compose]

-- ---------------------------------------------------------------------------
-- Corollaries
-- ---------------------------------------------------------------------------

/-- Filter fusion preserves the result count (direct consequence of `filterFusion`). -/
theorem filterFusion_length {α : Type} (p q : α → Bool) (child : Plan α) :
    ((Plan.filter p (Plan.filter q child)).eval).length =
      ((Plan.filter (fun row => q row && p row) child).eval).length := by
  rw [filterFusion]

end Py3plex.Optimizer
