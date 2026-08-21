import Py3plex.DSL.Semantics

/-!
# Py3plex.Optimizer.ProjectIdentity — Redundant Project Elimination

## What this file proves

`Plan.project (fun x => x) child` is semantically equivalent to `child`.

This is the abstract counterpart of the Python optimizer rule
`RemoveRedundantProject` in `py3plex/optimizer/rules.py`.
-/

namespace Py3plex.Optimizer

open Py3plex.DSL

/-- Removing an identity project preserves semantics. -/
theorem remove_redundant_project {α : Type} (child : Plan α) :
    (Plan.project (fun x => x) child).eval = child.eval := by
  simpa using Plan.project_id child

end Py3plex.Optimizer
