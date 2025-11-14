#!/usr/bin/env python3
"""
Property-based tests for validation module.

Tests invariants and correctness properties of input validation functions,
including file existence checks, format validation, and error handling.
"""

import os
import tempfile
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import validation module
try:
    from py3plex.validation import (
        validate_file_exists,
        validate_input_type
    )
    from py3plex.io.schema import _is_json_serializable as schema_json_check
    from py3plex.exceptions import ParsingError
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    pytest.skip("Validation module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Input Type Validation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    input_type=st.sampled_from([
        'gml', 'nx', 'multiplex_folder', 'sparse', 'gpickle',
        'multiedgelist', 'edgelist', 'graphml'
    ])
)
def test_validate_input_type_accepts_valid_types(input_type):
    """Test that validate_input_type accepts all valid input types."""
    # Should not raise exception for valid types
    try:
        validate_input_type(input_type)
    except ParsingError:
        pytest.fail(f"validate_input_type should accept valid type: {input_type}")


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(input_type=st.text(min_size=1, max_size=20).filter(
    lambda s: s not in {
        'gml', 'nx', 'multiplex_folder', 'sparse', 'sparse_network',
        'gpickle_biomine', 'gpickle', 'multiedgelist', 'detangler_json',
        'edgelist', 'edgelist_spin', 'edgelist_with_edge_types',
        'multiedge_tuple_list', 'multiplex_edges', 'graphml'
    }
))
def test_validate_input_type_rejects_invalid_types(input_type):
    """Test that validate_input_type rejects invalid input types."""
    # Should raise ParsingError for invalid types
    with pytest.raises(ParsingError):
        validate_input_type(input_type)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(custom_type=st.text(min_size=1, max_size=20))
def test_validate_input_type_with_custom_valid_set(custom_type):
    """Test that validate_input_type accepts custom valid types."""
    valid_types = {custom_type, 'other_type'}
    
    # Should not raise exception when type is in custom set
    try:
        validate_input_type(custom_type, valid_types=valid_types)
    except ParsingError:
        pytest.fail(f"validate_input_type should accept custom type: {custom_type}")


# ============================================================================
# Property Tests: File Existence Validation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(file_content=st.text(min_size=0, max_size=100))
def test_validate_file_exists_accepts_existing_file(file_content):
    """Test that validate_file_exists accepts existing files."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(file_content)
        temp_path = f.name
    
    try:
        # Should not raise exception for existing file
        validate_file_exists(temp_path)
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(filename=st.text(min_size=1, max_size=20).filter(lambda s: '/' not in s and '\\' not in s))
def test_validate_file_exists_rejects_nonexistent_file(filename):
    """Test that validate_file_exists rejects non-existent files."""
    # Create a path that definitely doesn't exist
    nonexistent_path = f"/tmp/nonexistent_dir_xyz/{filename}"
    
    # Should raise ParsingError for non-existent file
    with pytest.raises(ParsingError):
        validate_file_exists(nonexistent_path)


@pytest.mark.property
def test_validate_file_exists_rejects_directory():
    """Test that validate_file_exists rejects directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Should raise ParsingError for directory
        with pytest.raises(ParsingError):
            validate_file_exists(temp_dir)


# ============================================================================
# Property Tests: Validation Consistency
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.text(max_size=20),
        st.none(),
        st.lists(st.integers(), max_size=5)
    )
)
def test_json_serializable_consistency(value):
    """Test that JSON serializability check is consistent."""
    # Both validation and schema modules should have same result
    result = schema_json_check(value)
    
    # Result should be boolean
    assert isinstance(result, bool), "Should return boolean"
    
    # For these types, should be True
    if value is None or isinstance(value, (bool, int, float, str, list, dict)):
        assert result is True, f"Value {value} should be JSON-serializable"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    input_type=st.sampled_from(['gml', 'gpickle', 'multiedgelist', 'edgelist']),
    valid_twice=st.booleans()
)
def test_validate_input_type_deterministic(input_type, valid_twice):
    """Test that validate_input_type is deterministic."""
    # First call
    try:
        validate_input_type(input_type)
        first_valid = True
    except ParsingError:
        first_valid = False
    
    # Second call should give same result
    try:
        validate_input_type(input_type)
        second_valid = True
    except ParsingError:
        second_valid = False
    
    assert first_valid == second_valid, \
        "validate_input_type should be deterministic"


# ============================================================================
# Property Tests: Error Message Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(invalid_type=st.text(min_size=1, max_size=20).filter(
    lambda s: s not in {
        'gml', 'nx', 'multiplex_folder', 'sparse', 'sparse_network',
        'gpickle_biomine', 'gpickle', 'multiedgelist', 'detangler_json',
        'edgelist', 'edgelist_spin', 'edgelist_with_edge_types',
        'multiedge_tuple_list', 'multiplex_edges', 'graphml'
    }
))
def test_validate_input_type_error_contains_invalid_type(invalid_type):
    """Test that error message contains the invalid input type."""
    try:
        validate_input_type(invalid_type)
        pytest.fail("Should have raised ParsingError")
    except ParsingError as e:
        error_msg = str(e)
        # Error message should mention the invalid type
        assert invalid_type in error_msg, \
            f"Error message should contain '{invalid_type}'"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(filename=st.text(min_size=1, max_size=30).filter(lambda s: '/' not in s and '\\' not in s))
def test_validate_file_exists_error_contains_filename(filename):
    """Test that error message contains the non-existent filename."""
    nonexistent_path = f"/tmp/nonexistent_xyz/{filename}"
    
    try:
        validate_file_exists(nonexistent_path)
        pytest.fail("Should have raised ParsingError")
    except ParsingError as e:
        error_msg = str(e)
        # Error message should mention the filename
        assert filename in error_msg or nonexistent_path in error_msg, \
            f"Error message should contain filename or path"


# ============================================================================
# Property Tests: Validation Preconditions
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    file_content=st.text(min_size=1, max_size=100),
    file_suffix=st.sampled_from(['.txt', '.csv', '.json', '.dat'])
)
def test_validate_file_exists_preserves_file_content(file_content, file_suffix):
    """Test that validate_file_exists doesn't modify the file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=file_suffix) as f:
        f.write(file_content)
        temp_path = f.name
    
    try:
        # Validate file
        validate_file_exists(temp_path)
        
        # Check file content unchanged
        with open(temp_path, 'r') as f:
            content_after = f.read()
        
        assert content_after == file_content, \
            "validate_file_exists should not modify file content"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    input_type=st.sampled_from(['gml', 'gpickle', 'multiedgelist']),
    call_count=st.integers(min_value=1, max_value=5)
)
def test_validate_input_type_idempotent(input_type, call_count):
    """Test that calling validate_input_type multiple times has same effect."""
    # Call multiple times
    for _ in range(call_count):
        try:
            validate_input_type(input_type)
            # All calls should succeed
        except ParsingError:
            pytest.fail("All calls should succeed for valid input type")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
