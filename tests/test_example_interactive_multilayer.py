import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_FILE = REPO_ROOT / "examples" / "visualization" / "example_interactive_multilayer.py"


def test_interactive_multilayer_example_handles_missing_plotly():
    """Example should not fail the suite when optional plotly dependency is absent."""
    result = subprocess.run(
        [sys.executable, str(EXAMPLE_FILE)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT),
            "FAST_EXAMPLES": "1",
            "TQDM_DISABLE": "1",
            "PYTHONWARNINGS": "ignore",
        },
    )
    assert result.returncode == 0, result.stderr or result.stdout
