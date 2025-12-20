import builtins
import importlib.util
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest


GENERATE_PATH = Path(__file__).resolve().parent.parent / "docfiles" / "generate_all_outputs.py"


@pytest.fixture
def loaded_generator(monkeypatch, tmp_path):
    """Load generate_all_outputs.py with controlled output path and captured stdout."""
    target_file = tmp_path / "quickstart_outputs.txt"
    real_open = builtins.open

    def patched_open(file, mode="r", *args, **kwargs):
        if file == "/tmp/quickstart_outputs.txt":
            return real_open(target_file, mode, *args, **kwargs)
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", patched_open)

    spec = importlib.util.spec_from_file_location("generate_all_outputs_test", GENERATE_PATH)
    module = importlib.util.module_from_spec(spec)
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        spec.loader.exec_module(module)

    return module, target_file, stdout_buffer.getvalue()


def test_capture_output_filters_logging_and_stderr(loaded_generator):
    module, _, _ = loaded_generator

    @module.capture_output
    def noisy():
        print("keep this")
        print("INFO noisy line")
        print("BarnesHut details")
        import sys
        sys.stderr.write("errline\n")

    captured = noisy()
    assert captured == "keep this"


def test_capture_output_strips_filtered_lines_only(loaded_generator):
    module, _, _ = loaded_generator

    @module.capture_output
    def only_filtered():
        print("INFO: skip me")
        print("BarnesHut noise")
        print("Repulsion forces  took  0.00  seconds")
        print(" %| pattern ")

    assert only_filtered() == ""


def test_section_and_add_output_structure(monkeypatch, loaded_generator):
    module, _, _ = loaded_generator
    monkeypatch.setattr(module, "outputs", [])

    module.section("My Section")
    module.add_output(3, "Title", "", "line1\n\nline2", notes="note here")

    assert module.outputs == [
        f"\n{'='*70}",
        "My Section",
        "="*70,
        "\nSnippet 3: Title",
        "-"*70,
        "NOTE: note here\n",
        "Expected Output:",
        "",
        ".. code-block:: text",
        "",
        "    line1",
        "    line2",
        "",
    ]


def test_script_writes_expected_output_file(loaded_generator):
    module, output_file, captured_stdout = loaded_generator

    assert output_file.exists()
    content = output_file.read_text()

    assert "QUICKSTART.RST CODE SNIPPET OUTPUTS" in content
    assert "Snippet 1: Creating Your First Multilayer Network" in content
    assert "Snippet 21: Save Adjacency Matrix" in content

    assert "Generated outputs for all 21 snippets" in captured_stdout


def test_output_file_reflects_computed_values(loaded_generator):
    module, output_file, _ = loaded_generator
    content = output_file.read_text()

    assert (
        f"Nodes: {len(module.nodes)}, Edges: {len(module.edges)}, Layers: {len(module.layers)}"
        in content
    )
    assert f"Layer density: {module.density}" in content
    assert f"Node activity: {module.activity}" in content
    assert str(module.top_nodes) in content
    assert f"Neighbors of node 'A' in 'layer1': {module.neighbors}" in content
    assert f"Generated {len(module.walks)} walks" in content
