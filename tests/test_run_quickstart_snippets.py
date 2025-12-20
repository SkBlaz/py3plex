import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "docfiles" / "run_quickstart_snippets.py"


@pytest.fixture
def quickstart_module(monkeypatch):
    # Bypass the early sys.exit so the module definitions are reachable.
    monkeypatch.setattr(sys, "exit", lambda code=0: None)
    module_globals = runpy.run_path(str(SCRIPT_PATH), run_name="not_main")
    return SimpleNamespace(**module_globals)


def test_script_exits_with_deprecation_notice():
    result = subprocess.run([sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True)

    assert result.returncode == 1
    assert "DEPRECATED" in result.stdout
    assert "quickstart_5min.rst" in result.stdout


def test_parse_execute_and_report(monkeypatch, tmp_path, capsys, quickstart_module):
    quickstart_content = """
Section One
-----------

.. code-block:: python

    print("hello world")

Files
-----

.. code-block:: python

    print(open("data.edgelist").read().strip())

Binary
------

.. code-block:: python

    binary_path = "infomap"

Setup
-----

.. code-block:: python

    import math

Visual
------

.. code-block:: python

    draw_multilayer_default([])

Error Path
----------

.. code-block:: python

    raise RuntimeError("boom")
"""
    quickstart_file = tmp_path / "quickstart.rst"
    quickstart_file.write_text(quickstart_content)

    runner = quickstart_module.QuickstartRunner(quickstart_file)
    runner.parse_snippets()

    categories = [snippet.category for snippet in runner.snippets]
    assert categories == [
        quickstart_module.SnippetCategory.RUNNABLE,
        quickstart_module.SnippetCategory.REQUIRES_FILES,
        quickstart_module.SnippetCategory.REQUIRES_BINARY,
        quickstart_module.SnippetCategory.SETUP_ONLY,
        quickstart_module.SnippetCategory.VISUALIZATION,
        quickstart_module.SnippetCategory.RUNNABLE,
    ]

    runner.execute_snippets()
    output = capsys.readouterr().out

    # Three snippets execute successfully, two are skipped, one raises an error.
    assert "Summary: 3 executed, 2 skipped" in output
    assert "RuntimeError: boom" in output
    assert "⊘ Skipped - visualization" in output
    assert "⊘ Skipped - requires_binary" in output

    # Executed snippets retain their output, skipped snippets record a note.
    assert runner.snippets[0].output.strip() == "hello world"
    assert "A B" in runner.snippets[1].output  # Contents of data.edgelist
    assert "requires requires_binary" in runner.snippets[2].output
    assert runner.snippets[3].output == ""  # Setup-only snippets capture an empty string
    assert "requires visualization" in runner.snippets[4].output
    assert "RuntimeError: boom" in runner.snippets[5].output

    report = runner.generate_report()
    assert "Total snippets: 6" in report
    assert "- runnable: 2" in report
    assert "- visualization: 1" in report
    assert "- requires_binary: 1" in report
    assert "hello world" in report
    assert "RuntimeError: boom" in report
