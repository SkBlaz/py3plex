from pathlib import Path


def test_pypi_publish_uses_skip_existing():
    workflow = Path(__file__).resolve().parents[1] / ".github/workflows/pypi-publish.yml"
    text = workflow.read_text(encoding="utf-8")
    assert "skip-existing: true" in text
