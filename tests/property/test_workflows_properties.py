#!/usr/bin/env python3
"""
Property-based tests for workflows module.

Tests invariants for config-driven workflow execution.
"""

import json
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck
from pathlib import Path
import tempfile

# Import workflows module
try:
    from py3plex.workflows import WorkflowConfig, WorkflowRunner
    WORKFLOWS_AVAILABLE = True
except ImportError:
    WORKFLOWS_AVAILABLE = False
    pytest.skip("Workflows module not available", allow_module_level=True)


# ============================================================================
# Property Tests: WorkflowConfig
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), 
        whitelist_characters='_-'
    )),
    description=st.text(max_size=200)
)
def test_workflow_config_preserves_name_and_description(name, description):
    """Test that WorkflowConfig preserves name and description."""
    config_dict = {
        "name": name,
        "description": description,
        "datasets": [],
        "operations": []
    }
    
    config = WorkflowConfig(config_dict)
    
    assert config.name == name
    assert config.description == description


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    datasets=st.lists(
        st.dictionaries(
            keys=st.sampled_from(["name", "path", "type"]),
            values=st.text(min_size=1, max_size=50)
        ),
        min_size=0,
        max_size=5
    )
)
def test_workflow_config_preserves_datasets(datasets):
    """Test that WorkflowConfig preserves dataset configuration."""
    config_dict = {
        "name": "test_workflow",
        "datasets": datasets,
        "operations": []
    }
    
    config = WorkflowConfig(config_dict)
    
    assert config.datasets == datasets
    assert len(config.datasets) == len(datasets)


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    operations=st.lists(
        st.dictionaries(
            keys=st.sampled_from(["type", "params"]),
            values=st.one_of(
                st.text(min_size=1, max_size=30),
                st.dictionaries(
                    keys=st.text(min_size=1, max_size=20),
                    values=st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text(max_size=20))
                )
            )
        ),
        min_size=0,
        max_size=5
    )
)
def test_workflow_config_preserves_operations(operations):
    """Test that WorkflowConfig preserves operations configuration."""
    config_dict = {
        "name": "test_workflow",
        "datasets": [],
        "operations": operations
    }
    
    config = WorkflowConfig(config_dict)
    
    assert config.operations == operations
    assert len(config.operations) == len(operations)


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), 
        whitelist_characters='_-'
    )),
    output_dir=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), 
        whitelist_characters='/_-.'
    ))
)
def test_workflow_config_json_roundtrip(name, output_dir):
    """Test that WorkflowConfig can survive JSON serialization roundtrip."""
    config_dict = {
        "name": name,
        "description": "Test workflow",
        "datasets": [{"name": "test", "path": "/tmp/test.txt"}],
        "operations": [{"type": "load", "params": {}}],
        "output": {"directory": output_dir}
    }
    
    # Serialize to JSON
    json_str = json.dumps(config_dict)
    
    # Deserialize and create config
    restored_dict = json.loads(json_str)
    config = WorkflowConfig(restored_dict)
    
    # Check that key properties are preserved
    assert config.name == name
    assert config.output.get("directory") == output_dir


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    has_name=st.booleans(),
    has_datasets=st.booleans(),
    has_operations=st.booleans()
)
def test_workflow_config_handles_missing_fields(has_name, has_datasets, has_operations):
    """Test that WorkflowConfig handles missing optional fields gracefully."""
    config_dict = {}
    
    if has_name:
        config_dict["name"] = "test_workflow"
    if has_datasets:
        config_dict["datasets"] = [{"name": "test"}]
    if has_operations:
        config_dict["operations"] = [{"type": "load"}]
    
    # Should not raise an exception
    config = WorkflowConfig(config_dict)
    
    # Check that defaults are applied
    assert isinstance(config.name, str)
    assert isinstance(config.datasets, list)
    assert isinstance(config.operations, list)


# ============================================================================
# Property Tests: Config File Loading
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    name=st.text(min_size=1, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), 
        whitelist_characters='_-'
    )),
    n_operations=st.integers(min_value=0, max_value=5)
)
def test_workflow_config_from_json_file(name, n_operations):
    """Test loading WorkflowConfig from JSON file."""
    config_dict = {
        "name": name,
        "description": "Test workflow from file",
        "datasets": [],
        "operations": [{"type": f"op_{i}"} for i in range(n_operations)]
    }
    
    # Write to temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        # Load from file
        with open(temp_path, 'r') as f:
            loaded_dict = json.load(f)
        
        config = WorkflowConfig(loaded_dict)
        
        # Verify loaded config matches original
        assert config.name == name
        assert len(config.operations) == n_operations
    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)


# ============================================================================
# Property Tests: Configuration Validation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    config_dict=st.dictionaries(
        keys=st.sampled_from(["name", "description", "datasets", "operations", "output"]),
        values=st.one_of(
            st.text(max_size=50),
            st.lists(st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.text(max_size=30)
            ), max_size=3),
            st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.text(max_size=30)
            )
        )
    )
)
def test_workflow_config_accepts_various_configs(config_dict):
    """Test that WorkflowConfig can handle various valid configurations."""
    # Should not raise an exception for any valid dictionary
    config = WorkflowConfig(config_dict)
    
    # Basic invariants
    assert hasattr(config, 'name')
    assert hasattr(config, 'datasets')
    assert hasattr(config, 'operations')
    assert hasattr(config, 'output')
