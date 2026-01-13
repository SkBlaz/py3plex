"""
Tests for community detection examples in examples/05_communities/.

Tests that the example scripts run successfully and produce expected outputs.
"""
import importlib.util
import sys
from pathlib import Path

import pytest


def load_example_module(example_path: Path):
    """Load an example script as a module."""
    spec = importlib.util.spec_from_file_location("example_module", example_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["example_module"] = module
    return spec, module


def test_louvain_single_example_runs(capsys):
    """Test that 01_louvain_single.py runs successfully."""
    example_path = Path(__file__).parent.parent / "examples" / "05_communities" / "01_louvain_single.py"
    
    spec, module = load_example_module(example_path)
    
    # Execute the example
    spec.loader.exec_module(module)
    
    # Check output
    captured = capsys.readouterr()
    output = captured.out
    
    # Verify key outputs
    assert "Network loaded:" in output
    assert "Layers:" in output
    assert "Running Louvain on layer" in output
    assert "Community detection complete!" in output
    assert "Communities found:" in output
    assert "Sample communities" in output


def test_louvain_single_example_finds_communities(capsys):
    """Test that 01_louvain_single.py finds multiple communities."""
    example_path = Path(__file__).parent.parent / "examples" / "05_communities" / "01_louvain_single.py"
    
    spec, module = load_example_module(example_path)
    spec.loader.exec_module(module)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Parse number of communities from output
    for line in output.split('\n'):
        if "Communities found:" in line:
            # Extract number
            num_communities = int(line.split(':')[1].strip())
            assert num_communities > 0, "Should find at least 1 community"
            assert num_communities > 1, "Should find multiple communities for this network"
            break
    else:
        pytest.fail("Could not find 'Communities found:' in output")


def test_multilayer_detection_example_runs(capsys):
    """Test that 02_multilayer_detection.py runs successfully."""
    example_path = Path(__file__).parent.parent / "examples" / "05_communities" / "02_multilayer_detection.py"
    
    spec, module = load_example_module(example_path)
    
    # Execute the example
    spec.loader.exec_module(module)
    
    # Check output
    captured = capsys.readouterr()
    output = captured.out
    
    # Verify key outputs
    assert "Multilayer network loaded:" in output
    assert "Nodes:" in output
    assert "Layers:" in output
    assert "Layer names:" in output
    assert "Running layer-wise community detection" in output
    assert "Evaluating multilayer modularity" in output
    assert "Results:" in output
    assert "Multilayer modularity Q:" in output


def test_multilayer_detection_positive_modularity(capsys):
    """Test that 02_multilayer_detection.py finds positive modularity."""
    example_path = Path(__file__).parent.parent / "examples" / "05_communities" / "02_multilayer_detection.py"
    
    spec, module = load_example_module(example_path)
    spec.loader.exec_module(module)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Parse modularity from output
    for line in output.split('\n'):
        if "Multilayer modularity Q:" in line:
            # Extract Q value
            q_str = line.split('Q:')[1].strip()
            q_value = float(q_str)
            assert q_value > 0, f"Modularity should be positive, got {q_value}"
            assert q_value <= 1.0, f"Modularity should be <= 1, got {q_value}"
            break
    else:
        pytest.fail("Could not find 'Multilayer modularity Q:' in output")


def test_multilayer_detection_processes_all_layers(capsys):
    """Test that 02_multilayer_detection.py processes all layers."""
    example_path = Path(__file__).parent.parent / "examples" / "05_communities" / "02_multilayer_detection.py"
    
    spec, module = load_example_module(example_path)
    spec.loader.exec_module(module)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Check that multiple layers are processed (at least 3)
    layer_count = 0
    for line in output.split('\n'):
        if line.strip().startswith('Layer ') and ':' in line:
            layer_count += 1
    
    assert layer_count >= 3, f"Should process at least 3 layers, found {layer_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
