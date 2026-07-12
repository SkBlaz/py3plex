import Py3plex.DSL.Syntax

/-!
# Py3plex.DSL.Semantics — Executable Plan Semantics

Defines `Plan.eval : Plan α → List α` — the denotational/operational
semantics of a `Plan` — and proves basic sanity theorems about it.

## Semantics

* `eval (scan rows)          = rows`
* `eval (filter p child)     = (eval child).filter p`
-/

namespace Py3plex.DSL

-- ---------------------------------------------------------------------------
-- Evaluation function
-- ---------------------------------------------------------------------------

/-- Execute a `Plan` and return the resulting list of rows. -/
def Plan.eval : Plan α → List α
  | .scan rows      => rows
  | .filter p child => child.eval.filter p

-- ---------------------------------------------------------------------------
-- Equation lemmas (marked @[simp] for use in later proofs)
-- ---------------------------------------------------------------------------

/-- Evaluating a `scan` returns the original rows unchanged. -/
@[simp]
theorem Plan.eval_scan (rows : List α) :
    (Plan.scan rows).eval = rows := rfl

/-- Evaluating a `filter` applies the predicate to the child's result. -/
@[simp]
theorem Plan.eval_filter (p : α → Bool) (child : Plan α) :
    (Plan.filter p child).eval = child.eval.filter p := rfl

-- ---------------------------------------------------------------------------
-- Basic sanity theorems
-- ---------------------------------------------------------------------------

/-- Filtering with a predicate that always returns `true` is the identity. -/
theorem Plan.filter_const_true (child : Plan α) :
    (Plan.filter (fun _ => true) child).eval = child.eval := by
  simp only [Plan.eval_filter]
  generalize child.eval = rows
  induction rows with
  | nil        => rfl
  | cons x xs ih =>
    simp only [List.filter_cons]
    simp [ih]

/-- Filtering with a predicate that always returns `false` yields the empty
    list, regardless of `child`. -/
theorem Plan.filter_const_false (child : Plan α) :
    (Plan.filter (fun _ => false) child).eval = [] := by
  simp only [Plan.eval_filter]
  generalize child.eval = rows
  induction rows with
  | nil        => rfl
  | cons _ xs ih =>
    simp only [List.filter_cons]
    simp [ih]

/-- Filtering *any* predicate over an empty scan always yields the empty list.

    This is the abstract counterpart of the `ShortCircuitEmptyLayer` rule in
    `py3plex/optimizer/rules.py`: when the layer set is empty the sub-plan's
    result is empty regardless of what predicate is applied, so the whole
    sub-tree can be replaced by `LogicalEmptyScan`. -/
theorem Plan.filter_empty_scan (p : α → Bool) :
    (Plan.filter p (Plan.scan [])).eval = [] := by simp

end Py3plex.DSL
