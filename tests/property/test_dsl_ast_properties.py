#!/usr/bin/env python3
"""
Property-based tests for DSL AST module.

Tests invariants for AST node construction and validation:
- AST node immutability
- Valid AST structure
- Type safety
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from typing import List

# Import DSL module
try:
    from py3plex.dsl.ast import (
        Query,
        SelectStmt,
        Target,
        ExportTarget,
        LayerExpr,
        LayerTerm,
        ConditionExpr,
        ConditionAtom,
        Comparison,
        ComputeItem,
        OrderItem,
        ParamRef,
        SpecialPredicate,
    )
    DSL_AVAILABLE = True
except ImportError:
    DSL_AVAILABLE = False
    pytest.skip("DSL module not available", allow_module_level=True)


# ============================================================================
# Property Tests: AST Node Creation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(
    layer_name=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
    )
)
def test_layer_term_creation(layer_name):
    """
    Property: LayerTerm can be created with any valid string name.
    
    LayerTerm should accept any non-empty string as a layer name.
    """
    term = LayerTerm(name=layer_name)
    
    assert term.name == layer_name
    assert isinstance(term.name, str)


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(
    param_name=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
    )
)
def test_param_ref_creation(param_name):
    """
    Property: ParamRef can be created with any valid parameter name.
    
    ParamRef should store the parameter name correctly.
    """
    param = ParamRef(name=param_name)
    
    assert param.name == param_name
    assert isinstance(param.name, str)
    
    # String representation should include colon
    assert f":{param_name}" in str(param)


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(
    attr=st.text(min_size=1, max_size=15, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    op=st.sampled_from(['>', '>=', '<', '<=', '=', '!=']),
    value=st.one_of(
        st.integers(min_value=0, max_value=100),
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
    )
)
def test_comparison_creation(attr, op, value):
    """
    Property: Comparison nodes can be created with various types.
    
    Comparison should accept different value types (int, float, string).
    """
    comp = Comparison(left=attr, op=op, right=value)
    
    assert comp.left == attr
    assert comp.op == op
    assert comp.right == value


# ============================================================================
# Property Tests: AST Structure Invariants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    num_terms=st.integers(min_value=1, max_value=5)
)
def test_layer_expr_ops_consistent_with_terms(num_terms):
    """
    Property: LayerExpr ops list has length = len(terms) - 1.
    
    For N layer terms, there should be N-1 operators.
    """
    terms = [LayerTerm(name=f'layer{i}') for i in range(num_terms)]
    
    if num_terms > 1:
        ops = ['+'] * (num_terms - 1)
    else:
        ops = []
    
    layer_expr = LayerExpr(terms=terms, ops=ops)
    
    # Invariant: len(ops) == len(terms) - 1
    assert len(layer_expr.ops) == len(layer_expr.terms) - 1


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    num_atoms=st.integers(min_value=1, max_value=5)
)
def test_condition_expr_ops_consistent_with_atoms(num_atoms):
    """
    Property: ConditionExpr ops list has length = len(atoms) - 1.
    
    For N condition atoms, there should be N-1 logical operators.
    """
    atoms = []
    for i in range(num_atoms):
        comp = Comparison(left='degree', op='>', right=i)
        atoms.append(ConditionAtom(comparison=comp))
    
    if num_atoms > 1:
        ops = ['AND'] * (num_atoms - 1)
    else:
        ops = []
    
    cond_expr = ConditionExpr(atoms=atoms, ops=ops)
    
    # Invariant: len(ops) == len(atoms) - 1
    assert len(cond_expr.ops) == len(cond_expr.atoms) - 1


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    target=st.sampled_from([Target.NODES, Target.EDGES])
)
def test_select_stmt_target_preservation(target):
    """
    Property: SelectStmt preserves the target value.
    
    Creating a SelectStmt with target X should store target X.
    """
    stmt = SelectStmt(target=target)
    
    assert stmt.target == target
    assert isinstance(stmt.target, Target)


# ============================================================================
# Property Tests: AST Composition
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    measure_name=st.text(min_size=1, max_size=15, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    alias=st.text(min_size=1, max_size=15, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_compute_item_with_alias(measure_name, alias):
    """
    Property: ComputeItem stores both measure name and alias.
    
    COMPUTE measure AS alias should preserve both values.
    """
    assume(measure_name != alias)
    
    item = ComputeItem(name=measure_name, alias=alias)
    
    assert item.name == measure_name
    assert item.alias == alias


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    key=st.text(min_size=1, max_size=15, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    desc=st.booleans()
)
def test_order_item_preserves_direction(key, desc):
    """
    Property: OrderItem preserves sort direction.
    
    ORDER BY key [DESC] should store the desc flag correctly.
    """
    item = OrderItem(key=key, desc=desc)
    
    assert item.key == key
    assert item.desc == desc


# ============================================================================
# Property Tests: Special Predicates
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    kind=st.sampled_from(['intralayer', 'interlayer', 'motif'])
)
def test_special_predicate_kind(kind):
    """
    Property: SpecialPredicate stores the predicate kind.
    
    Different predicate kinds should be stored correctly.
    """
    pred = SpecialPredicate(kind=kind, params={})
    
    assert pred.kind == kind
    assert isinstance(pred.params, dict)


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    src_layer=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    dst_layer=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_interlayer_predicate_params(src_layer, dst_layer):
    """
    Property: Interlayer predicate stores source and target layers.
    
    interlayer(src, dst) should preserve both layer names.
    """
    pred = SpecialPredicate(
        kind='interlayer',
        params={'src': src_layer, 'dst': dst_layer}
    )
    
    assert pred.kind == 'interlayer'
    assert pred.params['src'] == src_layer
    assert pred.params['dst'] == dst_layer


# ============================================================================
# Property Tests: Query AST
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    explain=st.booleans()
)
def test_query_explain_flag(explain):
    """
    Property: Query preserves the explain flag.
    
    Creating a Query with explain=X should store explain=X.
    """
    select_stmt = SelectStmt(target=Target.NODES)
    query = Query(select=select_stmt, explain=explain)
    
    assert query.explain == explain


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    limit=st.integers(min_value=1, max_value=1000)
)
def test_select_stmt_limit(limit):
    """
    Property: SelectStmt stores the limit value correctly.
    
    LIMIT n should preserve the numeric value.
    """
    stmt = SelectStmt(target=Target.NODES, limit=limit)
    
    assert stmt.limit == limit
    assert isinstance(stmt.limit, int)


# ============================================================================
# Property Tests: Condition Atom Types
# ============================================================================

@pytest.mark.property
def test_condition_atom_exactly_one_type():
    """
    Property: ConditionAtom has exactly one of comparison/special/function.
    
    A condition atom should have only one type set, not multiple.
    """
    # Test with comparison
    comp = Comparison(left='degree', op='>', right=5)
    atom = ConditionAtom(comparison=comp)
    
    assert atom.comparison is not None
    assert atom.special is None
    assert atom.function is None
    
    # Test with special predicate
    pred = SpecialPredicate(kind='intralayer', params={})
    atom2 = ConditionAtom(special=pred)
    
    assert atom2.comparison is None
    assert atom2.special is not None
    assert atom2.function is None


# ============================================================================
# Property Tests: AST Immutability (Dataclass Behavior)
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    name1=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    name2=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_layer_term_equality(name1, name2):
    """
    Property: LayerTerm equality is based on name.
    
    Two LayerTerms with the same name should be equal.
    """
    term1 = LayerTerm(name=name1)
    term2 = LayerTerm(name=name1)
    term3 = LayerTerm(name=name2)
    
    # Same name -> equal
    assert term1 == term2
    
    # Different names -> not equal (unless names happen to be equal)
    if name1 != name2:
        assert term1 != term3


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    left=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    op=st.sampled_from(['>', '<', '=']),
    value=st.integers(min_value=0, max_value=100)
)
def test_comparison_equality(left, op, value):
    """
    Property: Comparison equality is based on all fields.
    
    Two Comparisons with same fields should be equal.
    """
    comp1 = Comparison(left=left, op=op, right=value)
    comp2 = Comparison(left=left, op=op, right=value)
    
    assert comp1 == comp2


# ============================================================================
# Property Tests: Layer Expression Operations
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    num_layers=st.integers(min_value=1, max_value=5)
)
def test_layer_expr_get_layer_names(num_layers):
    """
    Property: get_layer_names() returns all layer names in the expression.
    
    The method should extract all layer names from terms.
    """
    layer_names = [f'layer{i}' for i in range(num_layers)]
    terms = [LayerTerm(name=name) for name in layer_names]
    
    ops = ['+'] * (num_layers - 1) if num_layers > 1 else []
    layer_expr = LayerExpr(terms=terms, ops=ops)
    
    result = layer_expr.get_layer_names()
    
    # Should return all layer names
    assert len(result) == num_layers
    assert result == layer_names


# ============================================================================
# Property Tests: Export Targets
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(
    export_target=st.sampled_from([ExportTarget.PANDAS, ExportTarget.NETWORKX, ExportTarget.ARROW])
)
def test_export_target_enum(export_target):
    """
    Property: ExportTarget enum values are valid.
    
    All ExportTarget enum values should have string values.
    """
    assert isinstance(export_target, ExportTarget)
    assert isinstance(export_target.value, str)
    assert len(export_target.value) > 0
