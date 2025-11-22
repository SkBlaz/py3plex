"""
Tests for config-driven workflows.
"""

import json
import tempfile
from pathlib import Path

import pytest

from py3plex.workflows import WorkflowConfig, WorkflowRunner


def test_workflow_config_from_json():
    """Test loading workflow config from JSON."""
    config_data = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "datasets": [
            {
                "name": "test_net",
                "type": "generate",
                "generator": "random",
                "parameters": {
                    "nodes": 10,
                    "layers": 2,
                    "probability": 0.1,
                    "seed": 42,
                },
            }
        ],
        "operations": [{"type": "stats", "dataset": "test_net", "parameters": {}}],
        "output": {"directory": "test_output", "summary": "summary.json"},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name

    try:
        config = WorkflowConfig.from_file(config_path)
        assert config.name == "Test Workflow"
        assert len(config.datasets) == 1
        assert len(config.operations) == 1
    finally:
        Path(config_path).unlink()


def test_workflow_config_validation():
    """Test workflow config validation."""
    # Valid config
    config_data = {
        "name": "Test",
        "datasets": [
            {
                "name": "net1",
                "type": "generate",
                "generator": "random",
                "parameters": {},
            }
        ],
        "operations": [{"type": "stats", "dataset": "net1", "parameters": {}}],
    }
    config = WorkflowConfig(config_data)
    errors = config.validate()
    assert len(errors) == 0

    # Invalid: missing dataset name
    bad_config = {
        "name": "Test",
        "datasets": [{"type": "generate"}],
        "operations": [{"type": "stats", "dataset": "net1"}],
    }
    config = WorkflowConfig(bad_config)
    errors = config.validate()
    assert len(errors) > 0
    assert any("name" in error.lower() for error in errors)


def test_workflow_runner_generate_network():
    """Test workflow runner with network generation."""
    config_data = {
        "name": "Generate Test",
        "datasets": [
            {
                "name": "test_net",
                "type": "generate",
                "generator": "random",
                "parameters": {
                    "nodes": 10,
                    "layers": 2,
                    "probability": 0.2,
                    "seed": 123,
                },
            }
        ],
        "operations": [{"type": "stats", "dataset": "test_net", "parameters": {}}],
        "output": {},
    }

    config = WorkflowConfig(config_data)
    runner = WorkflowRunner(config)

    # Load datasets
    runner.load_datasets()
    assert "test_net" in runner.datasets
    network = runner.datasets["test_net"]
    assert network.core_network.number_of_nodes() == 20  # 10 nodes * 2 layers

    # Execute operations
    runner.execute_operations()
    assert len(runner.results) > 0


def test_workflow_stats_operation():
    """Test stats operation."""
    config_data = {
        "name": "Stats Test",
        "datasets": [
            {
                "name": "test_net",
                "type": "generate",
                "generator": "random",
                "parameters": {
                    "nodes": 15,
                    "layers": 2,
                    "probability": 0.15,
                    "seed": 42,
                },
            }
        ],
        "operations": [{"type": "stats", "dataset": "test_net", "parameters": {}}],
        "output": {},
    }

    config = WorkflowConfig(config_data)
    runner = WorkflowRunner(config)
    runner.load_datasets()
    runner.execute_operations()

    # Check stats result
    result_key = list(runner.results.keys())[0]
    stats = runner.results[result_key]
    assert "nodes" in stats
    assert "edges" in stats
    assert stats["nodes"] == 30  # 15 nodes * 2 layers


def test_workflow_community_operation():
    """Test community detection operation."""
    config_data = {
        "name": "Community Test",
        "datasets": [
            {
                "name": "test_net",
                "type": "generate",
                "generator": "random",
                "parameters": {
                    "nodes": 20,
                    "layers": 2,
                    "probability": 0.2,
                    "seed": 42,
                },
            }
        ],
        "operations": [
            {
                "type": "community",
                "dataset": "test_net",
                "parameters": {"algorithm": "louvain"},
            }
        ],
        "output": {},
    }

    config = WorkflowConfig(config_data)
    runner = WorkflowRunner(config)
    runner.load_datasets()
    runner.execute_operations()

    # Check community result
    result_key = list(runner.results.keys())[0]
    result = runner.results[result_key]
    assert "algorithm" in result
    assert result["algorithm"] == "louvain"
    assert "num_communities" in result
    assert "communities" in result
    assert result["num_communities"] > 0


def test_workflow_centrality_operation():
    """Test centrality computation operation."""
    config_data = {
        "name": "Centrality Test",
        "datasets": [
            {
                "name": "test_net",
                "type": "generate",
                "generator": "random",
                "parameters": {
                    "nodes": 10,
                    "layers": 2,
                    "probability": 0.3,
                    "seed": 42,
                },
            }
        ],
        "operations": [
            {
                "type": "centrality",
                "dataset": "test_net",
                "parameters": {"measure": "degree"},
            }
        ],
        "output": {},
    }

    config = WorkflowConfig(config_data)
    runner = WorkflowRunner(config)
    runner.load_datasets()
    runner.execute_operations()

    # Check centrality result
    result_key = list(runner.results.keys())[0]
    result = runner.results[result_key]
    assert "measure" in result
    assert result["measure"] == "degree"
    assert "centrality" in result
    assert len(result["centrality"]) > 0


def test_workflow_visualization_operation():
    """Test visualization operation."""
    config_data = {
        "name": "Viz Test",
        "datasets": [
            {
                "name": "test_net",
                "type": "generate",
                "generator": "random",
                "parameters": {
                    "nodes": 10,
                    "layers": 2,
                    "probability": 0.2,
                    "seed": 42,
                },
            }
        ],
        "operations": [
            {
                "type": "visualize",
                "dataset": "test_net",
                "parameters": {"output": "test_viz.png", "layout": "spring"},
            }
        ],
        "output": {},
    }

    config = WorkflowConfig(config_data)
    runner = WorkflowRunner(config)
    runner.load_datasets()
    runner.execute_operations()

    # Check that visualization was created
    result_key = list(runner.results.keys())[0]
    output_path = runner.results[result_key]
    assert Path(output_path).exists()

    # Cleanup
    Path(output_path).unlink()


def test_workflow_unsupported_format():
    """Test error handling for unsupported config format."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("not a valid config")
        config_path = f.name

    try:
        with pytest.raises(ValueError, match="Unsupported config format"):
            WorkflowConfig.from_file(config_path)
    finally:
        Path(config_path).unlink()


def test_workflow_file_not_found():
    """Test error handling for missing config file."""
    with pytest.raises(FileNotFoundError):
        WorkflowConfig.from_file("nonexistent_config.yaml")
