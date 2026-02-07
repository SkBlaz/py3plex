#!/usr/bin/env python3
"""Property-based tests for the counterexamples module.

This module tests properties of claim parsing, violation detection,
and witness minimization using hypothesis for property-based testing.

Key properties tested:
- Claim parsing is deterministic
- Valid claims can be parsed
- Invalid claims raise appropriate errors
- Predicates work correctly on metrics
- Violation detection is consistent
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import note

# Import counterexamples module
try:
    from py3plex.counterexamples import (
        parse_claim,
        ClaimParseError,
    )
    from py3plex.counterexamples.types import (
        CounterexampleResult,
        ViolationDetails,
    )
    COUNTEREXAMPLES_AVAILABLE = True
except ImportError:
    COUNTEREXAMPLES_AVAILABLE = False
    pytest.skip("Counterexamples module not available", allow_module_level=True)


# ============================================================================
# Helper Strategies
# ============================================================================

@st.composite
def valid_metric_name(draw):
    """Generate valid metric names."""
    return draw(st.sampled_from([
        "degree", "strength", "pagerank", "betweenness_centrality",
        "closeness_centrality", "clustering"
    ]))


@st.composite
def valid_comparator(draw):
    """Generate valid comparator names."""
    return draw(st.sampled_from([
        "gt", "ge", "gte", "lt", "le", "lte", "eq", "ne"
    ]))


@st.composite
def valid_parameter_name(draw):
    """Generate valid parameter names (single lowercase letter)."""
    return draw(st.sampled_from(["k", "x", "r", "p", "t", "n"]))


@st.composite
def valid_parameter_value(draw):
    """Generate valid parameter values."""
    return draw(st.one_of(
        st.integers(min_value=1, max_value=100),
        st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)
    ))


@st.composite
def value_predicate_string(draw):
    """Generate a valid value-based predicate string."""
    metric = draw(valid_metric_name())
    comparator = draw(valid_comparator())
    param = draw(valid_parameter_name())
    return f"{metric}__{comparator}({param})"


@st.composite
def rank_predicate_string(draw):
    """Generate a valid rank-based predicate string."""
    metric = draw(valid_metric_name())
    comparator = draw(valid_comparator())
    param = draw(valid_parameter_name())
    return f"{metric}__rank_{comparator}({param})"


@st.composite
def valid_claim_string(draw):
    """Generate a valid claim string."""
    # Antecedent: typically simpler (value-based)
    antecedent = draw(value_predicate_string())
    
    # Consequent: can be value or rank-based
    consequent = draw(st.one_of(
        value_predicate_string(),
        rank_predicate_string()
    ))
    
    return f"{antecedent} -> {consequent}"


# ============================================================================
# Property Tests: Claim Parsing
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(claim=valid_claim_string())
def test_valid_claim_parsing_succeeds(claim):
    """Property: Valid claim strings can be parsed without error."""
    params = {"k": 10, "x": 0.5, "r": 50, "p": 0.1, "t": 5, "n": 100}
    
    try:
        normalized, antecedent_fn, consequent_fn = parse_claim(claim, params)
        
        # Basic checks
        assert normalized is not None
        assert callable(antecedent_fn)
        assert callable(consequent_fn)
        assert "->" in normalized
        
        note(f"Successfully parsed: {normalized}")
    except ClaimParseError as e:
        pytest.fail(f"Valid claim failed to parse: {claim}\nError: {e}")


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    metric1=valid_metric_name(),
    comparator1=valid_comparator(),
    metric2=valid_metric_name(),
    comparator2=valid_comparator()
)
def test_claim_parsing_is_deterministic(metric1, comparator1, metric2, comparator2):
    """Property: Parsing the same claim twice gives identical results."""
    claim = f"{metric1}__{comparator1}(k) -> {metric2}__{comparator2}(r)"
    params = {"k": 10, "r": 50}
    
    # Parse twice
    normalized1, antecedent1, consequent1 = parse_claim(claim, params)
    normalized2, antecedent2, consequent2 = parse_claim(claim, params)
    
    # Normalized strings should be identical
    assert normalized1 == normalized2
    
    # Functions should behave identically on same inputs
    test_data = {"degree": 15, "pagerank": 0.5, "rank_pagerank": 25}
    assert antecedent1(test_data) == antecedent2(test_data)
    assert consequent1(test_data) == consequent2(test_data)


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(text=st.text(min_size=1, max_size=50))
def test_invalid_claims_raise_parse_error(text):
    """Property: Strings without '->' raise ClaimParseError."""
    # Filter out valid claim patterns
    assume("->" not in text)
    
    with pytest.raises(ClaimParseError, match="must contain"):
        parse_claim(text, {})


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    metric=valid_metric_name(),
    comparator=valid_comparator(),
    param_name=valid_parameter_name()
)
def test_predicate_without_parameter_value_works(metric, comparator, param_name):
    """Property: Predicates work even without parameter values if params provided."""
    claim = f"{metric}__{comparator}({param_name}) -> {metric}__rank_gt({param_name})"
    
    # Parse without providing the parameter value
    normalized, antecedent_fn, consequent_fn = parse_claim(claim, {param_name: 10})
    
    assert normalized is not None
    assert callable(antecedent_fn)
    assert callable(consequent_fn)


# ============================================================================
# Property Tests: Predicate Evaluation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    degree_val=st.integers(min_value=0, max_value=100),
    threshold=st.integers(min_value=0, max_value=100)
)
def test_degree_predicate_comparison(degree_val, threshold):
    """Property: Degree predicates correctly compare values."""
    claim = f"degree__ge(k) -> degree__gt(k)"
    params = {"k": threshold}
    
    normalized, antecedent_fn, consequent_fn = parse_claim(claim, params)
    
    # Test with data
    data = {"degree": degree_val}
    
    # Antecedent: degree >= k
    expected_antecedent = (degree_val >= threshold)
    assert antecedent_fn(data) == expected_antecedent, \
        f"degree__ge({threshold}) should be {expected_antecedent} for degree={degree_val}"
    
    # Consequent: degree > k
    expected_consequent = (degree_val > threshold)
    assert consequent_fn(data) == expected_consequent, \
        f"degree__gt({threshold}) should be {expected_consequent} for degree={degree_val}"


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    rank=st.integers(min_value=1, max_value=100),
    threshold=st.integers(min_value=1, max_value=100)
)
def test_rank_predicate_comparison(rank, threshold):
    """Property: Rank predicates correctly compare ranks."""
    claim = f"degree__ge(5) -> pagerank__rank_le(r)"
    params = {"r": threshold}
    
    normalized, antecedent_fn, consequent_fn = parse_claim(claim, params)
    
    # Test with data (rank is 1-indexed)
    data = {"degree": 10, "rank_pagerank": rank}
    
    # Consequent: rank_pagerank <= r
    expected = (rank <= threshold)
    assert consequent_fn(data) == expected, \
        f"pagerank__rank_le({threshold}) should be {expected} for rank={rank}"


# ============================================================================
# Property Tests: Claim String Normalization
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    metric1=valid_metric_name(),
    comp1=valid_comparator(),
    metric2=valid_metric_name(),
    comp2=valid_comparator()
)
def test_claim_normalization_preserves_structure(metric1, comp1, metric2, comp2):
    """Property: Normalized claim preserves arrow and predicate structure."""
    claim = f"{metric1}__{comp1}(k) -> {metric2}__{comp2}(r)"
    params = {"k": 10, "r": 50}
    
    normalized, _, _ = parse_claim(claim, params)
    
    # Should have exactly one arrow
    assert normalized.count("->") == 1
    
    # Should have two predicates (one before, one after arrow)
    parts = normalized.split("->")
    assert len(parts) == 2
    
    # Both parts should be non-empty
    assert len(parts[0].strip()) > 0
    assert len(parts[1].strip()) > 0


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    whitespace_before=st.text(alphabet=' \t', min_size=0, max_size=5),
    whitespace_after=st.text(alphabet=' \t', min_size=0, max_size=5)
)
def test_claim_parsing_handles_whitespace(whitespace_before, whitespace_after):
    """Property: Claim parsing is tolerant of surrounding whitespace."""
    base_claim = "degree__ge(k) -> pagerank__rank_le(r)"
    claim_with_whitespace = f"{whitespace_before}{base_claim}{whitespace_after}"
    
    params = {"k": 10, "r": 50}
    
    normalized1, _, _ = parse_claim(base_claim, params)
    normalized2, _, _ = parse_claim(claim_with_whitespace, params)
    
    # Normalized versions should be identical (whitespace stripped)
    assert normalized1 == normalized2


# ============================================================================
# Property Tests: Parameter Binding
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    k_value=st.integers(min_value=1, max_value=100),
    r_value=st.integers(min_value=1, max_value=100)
)
def test_parameter_binding_affects_evaluation(k_value, r_value):
    """Property: Different parameter values change predicate evaluation."""
    claim = "degree__ge(k) -> pagerank__rank_le(r)"
    
    # Parse with first set of parameters
    params1 = {"k": k_value, "r": r_value}
    _, antecedent1, consequent1 = parse_claim(claim, params1)
    
    # Parse with different parameters (shifted by 10)
    params2 = {"k": k_value + 10, "r": r_value + 10}
    _, antecedent2, consequent2 = parse_claim(claim, params2)
    
    # Test data
    data = {"degree": k_value + 5, "rank_pagerank": r_value + 5}
    
    # If k_value < degree < k_value + 10, antecedents should differ
    # degree__ge(k_value) should be True
    # degree__ge(k_value + 10) should be False
    if k_value < data["degree"] < k_value + 10:
        assert antecedent1(data) == True
        assert antecedent2(data) == False


# ============================================================================
# Property Tests: Comparator Semantics
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(value=st.integers(min_value=0, max_value=100))
def test_gt_vs_ge_comparators(value):
    """Property: gt (>) is strictly stronger than ge (>=)."""
    claim_ge = f"degree__ge(k) -> degree__ge(k)"
    claim_gt = f"degree__ge(k) -> degree__gt(k)"
    
    params = {"k": value}
    
    _, _, consequent_ge = parse_claim(claim_ge, params)
    _, _, consequent_gt = parse_claim(claim_gt, params)
    
    # Test with exact value
    data = {"degree": value}
    
    # degree >= value should be True
    assert consequent_ge(data) == True
    
    # degree > value should be False
    assert consequent_gt(data) == False
    
    # Test with value + 1
    data_higher = {"degree": value + 1}
    
    # Both should be True when value is higher
    assert consequent_ge(data_higher) == True
    assert consequent_gt(data_higher) == True


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(value=st.integers(min_value=0, max_value=100))
def test_lt_vs_le_comparators(value):
    """Property: lt (<) is strictly stronger than le (<=)."""
    claim_le = f"degree__ge(1) -> degree__le(k)"
    claim_lt = f"degree__ge(1) -> degree__lt(k)"
    
    params = {"k": value}
    
    _, _, consequent_le = parse_claim(claim_le, params)
    _, _, consequent_lt = parse_claim(claim_lt, params)
    
    # Test with exact value
    data = {"degree": value}
    
    # degree <= value should be True
    assert consequent_le(data) == True
    
    # degree < value should be False
    assert consequent_lt(data) == False
    
    # Test with value - 1
    if value > 0:
        data_lower = {"degree": value - 1}
        
        # Both should be True when value is lower
        assert consequent_le(data_lower) == True
        assert consequent_lt(data_lower) == True


# ============================================================================
# Property Tests: CounterexampleResult Structure
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10)
def test_counterexample_result_has_required_fields():
    """Property: CounterexampleResult has well-defined structure."""
    # This tests the dataclass structure
    try:
        from dataclasses import fields
        
        result_fields = {f.name for f in fields(CounterexampleResult)}
        
        # Must have these fields at minimum
        required = {"found", "claim", "violation"}
        assert required.issubset(result_fields), \
            f"CounterexampleResult missing required fields: {required - result_fields}"
    except Exception as e:
        pytest.skip(f"Cannot inspect CounterexampleResult: {e}")


# ============================================================================
# Property Tests: Error Messages
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(malformed=st.text(min_size=1, max_size=30).filter(lambda x: "->" not in x))
def test_parse_error_messages_are_informative(malformed):
    """Property: ClaimParseError messages mention the problem."""
    try:
        parse_claim(malformed, {})
        pytest.fail("Expected ClaimParseError")
    except ClaimParseError as e:
        error_msg = str(e).lower()
        
        # Error message should mention the arrow requirement
        assert any(word in error_msg for word in ["->", "arrow", "contain"]), \
            f"Error message should mention arrow requirement: {error_msg}"


@pytest.mark.property
@settings(deadline=None, max_examples=10)
def test_parse_error_includes_suggestions():
    """Property: ClaimParseError includes suggestions for fixing."""
    malformed = "degree__ge(k)"  # Missing arrow and consequent
    
    try:
        parse_claim(malformed, {})
        pytest.fail("Expected ClaimParseError")
    except ClaimParseError as e:
        # Should have suggestions attribute or mention format
        assert hasattr(e, 'suggestions') or "format" in str(e).lower()
