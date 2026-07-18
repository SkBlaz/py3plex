#!/usr/bin/env python3
"""
Property-based tests for the out_of_core module.

Tests condition-kwarg parsing logic and OutOfCoreNetwork construction.
"""

import pytest
from hypothesis import given, settings, strategies as st

# Import out_of_core module
try:
    from py3plex.out_of_core import (
        OutOfCoreNetwork,
        OutOfCoreError,
        OutOfCoreIOError,
        SchemaError,
        UnsupportedOutOfCoreOperation,
    )
    from py3plex.out_of_core.network import _parse_condition_kwargs
    OOC_AVAILABLE = True
except ImportError:
    OOC_AVAILABLE = False
    pytest.skip("out_of_core module not available", allow_module_level=True)


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_field_name = st.text(
    min_size=1, max_size=20,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
)

_numeric_value = st.one_of(
    st.integers(min_value=-1000, max_value=1000),
    st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
)

_scalar_value = st.one_of(_numeric_value, st.text(min_size=0, max_size=20))


# ---------------------------------------------------------------------------
# _parse_condition_kwargs – suffix → operator mapping
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(field=_field_name, value=_numeric_value)
def test_parse_plain_field_produces_eq(field, value):
    """A plain field name (no suffix) maps to the 'eq' operator."""
    result = _parse_condition_kwargs({field: value})
    assert len(result) == 1
    assert result[0]["field"] == field
    assert result[0]["op"] == "eq"
    assert result[0]["value"] == value


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(field=_field_name, value=_numeric_value)
def test_parse_gt_suffix(field, value):
    """A field with __gt suffix maps to the 'gt' operator."""
    result = _parse_condition_kwargs({f"{field}__gt": value})
    assert result[0]["op"] == "gt"
    assert result[0]["field"] == field
    assert result[0]["value"] == value


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(field=_field_name, value=_numeric_value)
def test_parse_gte_suffix(field, value):
    """A field with __gte suffix maps to the 'gte' operator."""
    result = _parse_condition_kwargs({f"{field}__gte": value})
    assert result[0]["op"] == "gte"
    assert result[0]["field"] == field


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(field=_field_name, value=_numeric_value)
def test_parse_lt_suffix(field, value):
    """A field with __lt suffix maps to the 'lt' operator."""
    result = _parse_condition_kwargs({f"{field}__lt": value})
    assert result[0]["op"] == "lt"
    assert result[0]["field"] == field


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(field=_field_name, value=_numeric_value)
def test_parse_lte_suffix(field, value):
    """A field with __lte suffix maps to the 'lte' operator."""
    result = _parse_condition_kwargs({f"{field}__lte": value})
    assert result[0]["op"] == "lte"
    assert result[0]["field"] == field


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(field=_field_name, value=_scalar_value)
def test_parse_eq_suffix(field, value):
    """A field with __eq suffix maps to the 'eq' operator."""
    result = _parse_condition_kwargs({f"{field}__eq": value})
    assert result[0]["op"] == "eq"
    assert result[0]["field"] == field


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(field=_field_name, value=_scalar_value)
def test_parse_ne_suffix(field, value):
    """A field with __ne suffix maps to the 'ne' operator."""
    result = _parse_condition_kwargs({f"{field}__ne": value})
    assert result[0]["op"] == "ne"
    assert result[0]["field"] == field


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    field1=_field_name,
    field2=_field_name,
    val1=_numeric_value,
    val2=_numeric_value,
)
def test_parse_multiple_conditions(field1, field2, val1, val2):
    """Multiple conditions parse to a list of the same length."""
    kwargs = {f"{field1}__gt": val1, f"{field2}__lt": val2}
    result = _parse_condition_kwargs(kwargs)
    assert len(result) == len(kwargs)


@pytest.mark.property
def test_parse_empty_conditions():
    """Empty kwargs parse to an empty list."""
    result = _parse_condition_kwargs({})
    assert result == []


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(field=_field_name, value=_numeric_value)
def test_parse_condition_dicts_have_required_keys(field, value):
    """Every condition dict has 'field', 'op', and 'value' keys."""
    for suffix in ("__gt", "__gte", "__lt", "__lte", "__eq", "__ne"):
        result = _parse_condition_kwargs({f"{field}{suffix}": value})
        for cond in result:
            assert "field" in cond
            assert "op" in cond
            assert "value" in cond


# ---------------------------------------------------------------------------
# OutOfCoreError hierarchy
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_out_of_core_error_is_exception():
    """OutOfCoreError is an Exception subclass."""
    assert issubclass(OutOfCoreError, Exception)


@pytest.mark.property
def test_out_of_core_io_error_subclass():
    """OutOfCoreIOError is an OutOfCoreError subclass."""
    assert issubclass(OutOfCoreIOError, OutOfCoreError)


@pytest.mark.property
def test_schema_error_subclass():
    """SchemaError is an OutOfCoreError subclass."""
    assert issubclass(SchemaError, OutOfCoreError)


@pytest.mark.property
def test_unsupported_operation_subclass():
    """UnsupportedOutOfCoreOperation is an OutOfCoreError subclass."""
    assert issubclass(UnsupportedOutOfCoreOperation, OutOfCoreError)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(msg=st.text(min_size=0, max_size=100))
def test_out_of_core_error_preserves_message(msg):
    """OutOfCoreError preserves the error message."""
    err = OutOfCoreError(msg)
    assert str(err) == msg


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(msg=st.text(min_size=0, max_size=100))
def test_schema_error_preserves_message(msg):
    """SchemaError preserves the error message."""
    err = SchemaError(msg)
    assert str(err) == msg


# ---------------------------------------------------------------------------
# OutOfCoreNetwork – repr / info
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_out_of_core_network_repr_is_string(tmp_path):
    """OutOfCoreNetwork.__repr__ returns a string."""
    edges_file = tmp_path / "edges.csv"
    edges_file.write_text("source,target,layer\n")
    net = OutOfCoreNetwork(str(edges_file))
    r = repr(net)
    assert isinstance(r, str)


@pytest.mark.property
def test_out_of_core_network_info_is_dict(tmp_path):
    """OutOfCoreNetwork.info() returns a dict."""
    edges_file = tmp_path / "edges.csv"
    edges_file.write_text("source,target,layer\n")
    net = OutOfCoreNetwork(str(edges_file))
    info = net.info()
    assert isinstance(info, dict)


@pytest.mark.property
def test_out_of_core_network_info_has_edges_path_key(tmp_path):
    """OutOfCoreNetwork.info() contains an 'edges_path' key."""
    edges_file = tmp_path / "edges.csv"
    edges_file.write_text("source,target,layer\n")
    net = OutOfCoreNetwork(str(edges_file))
    info = net.info()
    assert "edges_path" in info


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
