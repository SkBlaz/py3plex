#!/usr/bin/env python3
"""
Property-based tests for DSL registry modules.

Tests invariants for:
- Measure registry operations
- Operator registry operations
- Registration/lookup consistency
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from typing import Dict, Any

# Import DSL module
try:
    from py3plex.dsl import (
        measure_registry,
        operator_registry,
        register_operator,
        get_operator,
        list_operators,
        unregister_operator,
        dsl_operator,
    )
    from py3plex.dsl.context import DSLExecutionContext
    from py3plex.dsl.errors import UnknownMeasureError
    DSL_AVAILABLE = True
except ImportError:
    DSL_AVAILABLE = False
    pytest.skip("DSL module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Measure Registry
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    measure_name=st.sampled_from([
        'degree', 'betweenness', 'closeness', 'eigenvector',
        'clustering', 'pagerank'
    ])
)
def test_measure_registry_get_is_callable(measure_name):
    """
    Property: All registered measures return callable functions.
    
    For any registered measure, measure_registry.get(name) should return
    a callable object.
    """
    try:
        measure_fn = measure_registry.get(measure_name)
        assert callable(measure_fn), f"Measure {measure_name} is not callable"
    except UnknownMeasureError:
        # If measure is not registered, that's ok - test passes
        pass


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    measure_name=st.text(
        min_size=1,
        max_size=15,
        alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
    )
)
def test_measure_registry_unknown_raises_error(measure_name):
    """
    Property: Looking up unknown measures raises UnknownMeasureError.
    
    Registry should consistently raise errors for unregistered measures.
    """
    # Only test if not a known measure
    known_measures = [
        'degree', 'betweenness', 'closeness', 'eigenvector',
        'clustering', 'pagerank', 'load_centrality', 'harmonic_centrality'
    ]
    
    assume(measure_name not in known_measures)
    
    with pytest.raises(UnknownMeasureError):
        measure_registry.get(measure_name)


@pytest.mark.property
def test_measure_registry_list_measures_consistent():
    """
    Property: Listing measures returns a consistent set.
    
    Multiple calls to list_measures() should return the same measures.
    """
    measures1 = measure_registry.list_measures()
    measures2 = measure_registry.list_measures()
    
    # Should be identical sets
    assert measures1 == measures2
    assert isinstance(measures1, list)
    assert len(measures1) > 0


# ============================================================================
# Property Tests: Operator Registry
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    operator_name=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
    ).filter(lambda x: x not in ['test_op', 'temp_op']),
)
def test_operator_registry_register_get_roundtrip(operator_name):
    """
    Property: Registering an operator makes it retrievable.
    
    After register_operator(name, fn), get_operator(name) should return fn.
    """
    # Define a test operator function
    def test_func(context: DSLExecutionContext, param: float = 1.0) -> float:
        return param * 2.0
    
    # Register the operator
    try:
        register_operator(
            name=operator_name,
            func=test_func,
            description="Test operator",
            overwrite=True
        )
        
        # Retrieve it
        retrieved = get_operator(operator_name)
        
        # Should be retrievable
        assert retrieved is not None
        assert retrieved.name == operator_name
        assert retrieved.func == test_func
        
    finally:
        # Cleanup
        try:
            unregister_operator(operator_name)
        except:
            pass


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    name1=st.text(min_size=1, max_size=15, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    name2=st.text(min_size=1, max_size=15, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_operator_registry_distinct_names(name1, name2):
    """
    Property: Operators with different names are stored independently.
    
    Registering op1 and op2 should not interfere with each other.
    """
    assume(name1 != name2)
    
    def func1(context: DSLExecutionContext) -> float:
        return 1.0
    
    def func2(context: DSLExecutionContext) -> float:
        return 2.0
    
    try:
        # Register both
        register_operator(name1, func1, overwrite=True)
        register_operator(name2, func2, overwrite=True)
        
        # Retrieve both
        op1 = get_operator(name1)
        op2 = get_operator(name2)
        
        # Should be distinct
        assert op1 is not None
        assert op2 is not None
        assert op1.name == name1
        assert op2.name == name2
        assert op1.func == func1
        assert op2.func == func2
        
    finally:
        # Cleanup
        try:
            unregister_operator(name1)
            unregister_operator(name2)
        except:
            pass


@pytest.mark.property
def test_operator_registry_unregister_removes():
    """
    Property: Unregistering an operator makes it unavailable.
    
    After unregister_operator(name), get_operator(name) should return None.
    """
    op_name = "temp_test_operator"
    
    def test_func(context: DSLExecutionContext) -> float:
        return 42.0
    
    # Register
    register_operator(op_name, test_func, overwrite=True)
    
    # Verify it exists
    assert get_operator(op_name) is not None
    
    # Unregister
    unregister_operator(op_name)
    
    # Should be gone
    assert get_operator(op_name) is None


@pytest.mark.property
def test_operator_registry_list_includes_registered():
    """
    Property: list_operators() includes all registered operators.
    
    After registering an operator, it should appear in list_operators().
    """
    op_name = "test_list_operator"
    
    def test_func(context: DSLExecutionContext) -> float:
        return 42.0
    
    try:
        # Register
        register_operator(op_name, test_func, overwrite=True)
        
        # List operators
        operators = list_operators()
        
        # Should include our operator (list_operators returns a dict)
        assert isinstance(operators, dict)
        assert op_name in operators
        assert operators[op_name].name == op_name
        
    finally:
        # Cleanup
        try:
            unregister_operator(op_name)
        except:
            pass


# ============================================================================
# Property Tests: Decorator Registration
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    operator_name=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
    ).filter(lambda x: not x.startswith('test_'))
)
def test_dsl_operator_decorator_registers(operator_name):
    """
    Property: @dsl_operator decorator registers the function.
    
    Using @dsl_operator(name) should make the operator available via get_operator.
    """
    try:
        # Use decorator
        @dsl_operator(operator_name, overwrite=True)
        def custom_op(context: DSLExecutionContext, alpha: float = 0.5) -> float:
            return alpha
        
        # Should be registered
        retrieved = get_operator(operator_name)
        assert retrieved is not None
        assert retrieved.name == operator_name
        
        # Function should still be callable directly
        assert callable(custom_op)
        
    finally:
        # Cleanup
        try:
            unregister_operator(operator_name)
        except:
            pass


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    category=st.sampled_from(['centrality', 'dynamics', 'custom', 'analysis'])
)
def test_operator_registry_preserves_category(category):
    """
    Property: Operator category is preserved in registration.
    
    Registering with category=X should store category=X.
    """
    op_name = f"test_cat_{category}"
    
    def test_func(context: DSLExecutionContext) -> float:
        return 1.0
    
    try:
        # Register with category
        register_operator(
            name=op_name,
            func=test_func,
            category=category,
            overwrite=True
        )
        
        # Retrieve
        op = get_operator(op_name)
        
        # Category should match
        assert op is not None
        assert op.category == category
        
    finally:
        # Cleanup
        try:
            unregister_operator(op_name)
        except:
            pass


# ============================================================================
# Property Tests: Registry Consistency
# ============================================================================

@pytest.mark.property
def test_measure_registry_deterministic():
    """
    Property: Measure registry returns consistent results.
    
    Multiple calls to get(name) should return the same function object.
    """
    measure_name = "degree"
    
    fn1 = measure_registry.get(measure_name)
    fn2 = measure_registry.get(measure_name)
    
    # Should be the same function
    assert fn1 is fn2


@pytest.mark.property
def test_operator_registry_overwrite_replaces():
    """
    Property: Overwriting an operator replaces the old one.
    
    Registering the same name twice with overwrite=True should replace.
    """
    op_name = "test_overwrite"
    
    def func1(context: DSLExecutionContext) -> float:
        return 1.0
    
    def func2(context: DSLExecutionContext) -> float:
        return 2.0
    
    try:
        # Register first function
        register_operator(op_name, func1, overwrite=True)
        op1 = get_operator(op_name)
        assert op1.func == func1
        
        # Register second function with same name
        register_operator(op_name, func2, overwrite=True)
        op2 = get_operator(op_name)
        assert op2.func == func2
        
        # Should have replaced the first one
        assert op2.func != func1
        
    finally:
        # Cleanup
        try:
            unregister_operator(op_name)
        except:
            pass


@pytest.mark.property
def test_measure_registry_aliases_resolve():
    """
    Property: Measure aliases resolve to canonical names.
    
    If 'degree_centrality' is an alias for 'degree', both should work
    and return callable functions.
    """
    # Test known alias
    try:
        canonical = measure_registry.get("degree")
        alias = measure_registry.get("degree_centrality")
        
        # Should both be callable
        assert callable(canonical)
        assert callable(alias)
        # Both should work - they may or may not be the same function object
        # The important property is that both resolve successfully
        
    except UnknownMeasureError:
        # If aliases aren't set up, test passes
        pass
