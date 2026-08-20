from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "formal"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_formal_readme_matches_phase1_tree_and_toolchain():
    readme = _read(FORMAL / "README.md")
    toolchain = _read(FORMAL / "lean-toolchain").strip()

    assert "# Py3plex Formal Verification (Phase 1)" in readme
    assert "Syntax.lean" in readme
    assert "Semantics.lean" in readme
    assert "FilterFusion.lean" in readme
    assert "ProjectIdentity.lean" in readme
    assert toolchain in readme


def test_formal_readme_and_lean_comment_reference_conditions_lists():
    readme = _read(FORMAL / "README.md")
    filter_fusion = _read(FORMAL / "Py3plex/Optimizer/FilterFusion.lean")

    assert "`conditions` lists in inner-then-outer order" in readme
    assert "`conditions` lists in inner-then-outer order" in filter_fusion


def test_formal_theorems_listed_in_readme_exist_in_lean_sources():
    readme = _read(FORMAL / "README.md")
    semantics = _read(FORMAL / "Py3plex/DSL/Semantics.lean")
    filter_fusion = _read(FORMAL / "Py3plex/Optimizer/FilterFusion.lean")
    project_identity = _read(FORMAL / "Py3plex/Optimizer/ProjectIdentity.lean")

    theorem_names = [
        "Plan.eval_scan",
        "Plan.eval_emptyScan",
        "Plan.eval_filter",
        "Plan.eval_project",
        "Plan.eval_limit",
        "Plan.filter_const_true",
        "Plan.filter_const_false",
        "Plan.filter_empty_scan",
        "Py3plex.Optimizer.filter_compose",
        "Py3plex.Optimizer.filterFusion",
        "Py3plex.Optimizer.filterFusion_length",
        "Py3plex.Optimizer.remove_redundant_project",
    ]

    for theorem_name in theorem_names:
        assert theorem_name in readme

    assert "theorem Plan.eval_scan" in semantics
    assert "theorem Plan.eval_emptyScan" in semantics
    assert "theorem Plan.eval_filter" in semantics
    assert "theorem Plan.eval_project" in semantics
    assert "theorem Plan.eval_limit" in semantics
    assert "theorem Plan.filter_const_true" in semantics
    assert "theorem Plan.filter_const_false" in semantics
    assert "theorem Plan.filter_empty_scan" in semantics
    assert "theorem filter_compose" in filter_fusion
    assert "theorem filterFusion" in filter_fusion
    assert "theorem filterFusion_length" in filter_fusion
    assert "theorem remove_redundant_project" in project_identity


def test_formal_build_entrypoints_stay_aligned():
    makefile = _read(ROOT / "Makefile")
    workflow = _read(ROOT / ".github/workflows/formal.yml")

    assert "formal: ## Build and verify the Lean formal proofs" in makefile
    assert "cd formal && lake build" in makefile
    assert "branches: [master, main]" in workflow
    assert "working-directory: formal" in workflow
    assert "run: lake build" in workflow


def test_formal_filter_empty_scan_models_short_circuit_empty_layer():
    """Plan.filter_empty_scan is the abstract counterpart of the Python
    ShortCircuitEmptyLayer optimizer rule.  Verify that:
      - the Lean theorem exists in Semantics.lean
      - the README documents the theorem with its Python rule name
      - the Lean docstring explicitly mentions ShortCircuitEmptyLayer
    """
    semantics = _read(FORMAL / "Py3plex/DSL/Semantics.lean")
    readme = _read(FORMAL / "README.md")

    assert "theorem Plan.filter_empty_scan" in semantics
    assert "ShortCircuitEmptyLayer" in semantics
    assert "Plan.filter_empty_scan" in readme
    assert "ShortCircuitEmptyLayer" in readme


def test_formal_readme_python_lean_table_covers_both_proven_rules():
    """The README's Python-to-Lean mapping table must reference both proven
    optimizer rules: CombineAdjacentFilters (filterFusion) and
    ShortCircuitEmptyLayer (filter_empty_scan).
    """
    readme = _read(FORMAL / "README.md")

    assert "CombineAdjacentFilters" in readme
    assert "ShortCircuitEmptyLayer" in readme
    assert "filter_empty_scan" in readme
    assert "filterFusion" in readme


def test_formal_empty_scan_is_marked_done_and_mapped_to_python_node():
    readme = _read(FORMAL / "README.md")
    syntax = _read(FORMAL / "Py3plex/DSL/Syntax.lean")
    semantics = _read(FORMAL / "Py3plex/DSL/Semantics.lean")

    assert "- [x] `Plan.emptyScan` — models `LogicalEmptyScan`" in readme
    assert "| `Plan.emptyScan` | `LogicalEmptyScan` in `plan_nodes.py` |" in readme
    assert "| `Plan.emptyScan` | `LogicalEmptyScan` in the same file |" in syntax
    assert "| emptyScan : Plan α" in syntax
    assert "theorem Plan.eval_emptyScan" in semantics


def test_formal_project_and_limit_are_marked_done_and_defined():
    readme = _read(FORMAL / "README.md")
    syntax = _read(FORMAL / "Py3plex/DSL/Syntax.lean")
    semantics = _read(FORMAL / "Py3plex/DSL/Semantics.lean")
    project_identity = _read(FORMAL / "Py3plex/Optimizer/ProjectIdentity.lean")

    assert "- [x] `Plan.project` — models `LogicalProject`" in readme
    assert "- [x] `Plan.limit` — models `LogicalLimit`" in readme
    assert "- [x] `remove_redundant_project` ↔ `RemoveRedundantProject`" in readme
    assert "| `Plan.project` | `LogicalProject` in `plan_nodes.py` |" in readme
    assert "| `Plan.limit` | `LogicalLimit` in `plan_nodes.py` |" in readme
    assert "| `Plan.project`   | `LogicalProject` in the same file |" in syntax
    assert "| `Plan.limit`     | `LogicalLimit` in the same file |" in syntax
    assert "| project : (α → α) → Plan α → Plan α" in syntax
    assert "| limit : Nat → Plan α → Plan α" in syntax
    assert "theorem Plan.eval_project" in semantics
    assert "theorem Plan.eval_limit" in semantics
    assert "theorem Plan.project_id" in semantics
    assert "theorem remove_redundant_project" in project_identity
