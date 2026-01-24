"""
Test documentation examples pipeline.

This test suite validates:
1. Examples in examples/docs/ can be executed
2. Outputs are captured correctly
3. RST files reference the correct outputs
4. Validation catches errors
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


# Paths
REPO_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples" / "docs"
OUTPUTS_DIR = REPO_ROOT / "examples" / "docs_outputs"
MANIFEST_FILE = OUTPUTS_DIR / "manifest.json"
SCRIPTS_DIR = REPO_ROOT / "scripts"


def test_examples_directory_exists():
    """Test that examples/docs directory exists."""
    assert EXAMPLES_DIR.exists(), f"Examples directory not found: {EXAMPLES_DIR}"
    assert EXAMPLES_DIR.is_dir(), f"Examples path is not a directory: {EXAMPLES_DIR}"


def test_generate_script_exists():
    """Test that the generate_docs_outputs.py script exists."""
    script = SCRIPTS_DIR / "generate_docs_outputs.py"
    assert script.exists(), f"Generate script not found: {script}"


def test_validate_script_exists():
    """Test that the validate_docs_outputs.py script exists."""
    script = SCRIPTS_DIR / "validate_docs_outputs.py"
    assert script.exists(), f"Validate script not found: {script}"


def test_generate_outputs():
    """Test that generate_docs_outputs.py runs successfully."""
    script = SCRIPTS_DIR / "generate_docs_outputs.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    
    assert result.returncode == 0, (
        f"Generate script failed:\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
    
    # Check that manifest was created
    assert MANIFEST_FILE.exists(), f"Manifest file not created: {MANIFEST_FILE}"
    
    # Load and validate manifest
    with open(MANIFEST_FILE, 'r') as f:
        manifest = json.load(f)
    
    assert 'version' in manifest
    assert 'examples' in manifest
    assert len(manifest['examples']) > 0, "No examples found in manifest"


def test_manifest_structure():
    """Test that the manifest has the correct structure."""
    # Generate first
    script = SCRIPTS_DIR / "generate_docs_outputs.py"
    subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        timeout=60,
    )
    
    # Load manifest
    with open(MANIFEST_FILE, 'r') as f:
        manifest = json.load(f)
    
    # Check structure
    assert 'version' in manifest
    assert 'examples' in manifest
    assert 'generated' in manifest
    
    # Check each example entry
    for example_name, example_data in manifest['examples'].items():
        assert 'success' in example_data
        if example_data['success']:
            assert 'output_file' in example_data
            # Verify output file exists
            output_file = OUTPUTS_DIR / example_data['output_file']
            assert output_file.exists(), f"Output file not found: {output_file}"


def test_output_files_created():
    """Test that output files are created for successful examples."""
    # Generate first
    script = SCRIPTS_DIR / "generate_docs_outputs.py"
    subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        timeout=60,
    )
    
    # Load manifest
    with open(MANIFEST_FILE, 'r') as f:
        manifest = json.load(f)
    
    # Check each successful example has an output file
    for example_name, example_data in manifest['examples'].items():
        if example_data['success']:
            output_file = OUTPUTS_DIR / f"{example_name}.txt"
            assert output_file.exists(), f"Output file not found: {output_file}"
            # Check file is not empty
            content = output_file.read_text()
            assert len(content) > 0, f"Output file is empty: {output_file}"


def test_validate_outputs():
    """Test that validate_docs_outputs.py runs successfully."""
    # Generate first
    gen_script = SCRIPTS_DIR / "generate_docs_outputs.py"
    subprocess.run(
        [sys.executable, str(gen_script)],
        cwd=REPO_ROOT,
        capture_output=True,
        timeout=60,
    )
    
    # Validate
    val_script = SCRIPTS_DIR / "validate_docs_outputs.py"
    result = subprocess.run(
        [sys.executable, str(val_script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    
    assert result.returncode == 0, (
        f"Validate script failed:\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


@pytest.mark.parametrize("example_file", list(EXAMPLES_DIR.glob("*.py")) if EXAMPLES_DIR.exists() else [])
def test_individual_example(example_file):
    """Test that each example can be run individually."""
    result = subprocess.run(
        [sys.executable, str(example_file)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        env={
            **subprocess.os.environ,
            'TQDM_DISABLE': '1',
            'PYTHONWARNINGS': 'ignore',
        },
    )
    
    assert result.returncode == 0, (
        f"Example {example_file.name} failed:\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
