from pathlib import Path


def test_make_type_coverage_target_uses_existing_script() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
    script_path = repo_root / "docfiles" / "check_type_coverage.py"

    assert script_path.exists()
    assert "python docfiles/check_type_coverage.py --verbose" in makefile
