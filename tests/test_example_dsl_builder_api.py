import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "_downloads"
    / "16ed82c0e4ef3b71b84550a2e3c40481"
    / "example_dsl_builder_api.py"
)


def test_dsl_builder_example_runs_end_to_end():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True
    )

    assert result.returncode == 0, result.stderr

    output = result.stdout
    assert "DSL V2 PYTHON BUILDER API EXAMPLES" in output
    assert "Nodes in social layer: 6" in output
    assert "Nodes in both social AND work: 0" in output
    assert "Computed measures for 18 nodes" in output
    assert "Sample results (first 5):" in output
    assert "('Alice', 'social')" in output
    assert "Top 5 nodes by degree:" in output
    assert "Error caught: Unknown measure 'betweenes'" in output
    assert "Did you mean 'betweenness'?" in output
    assert "Available measures (" in output
    assert "DSL V2 BUILDER API EXAMPLES COMPLETE" in output
    assert "Traceback" not in output
