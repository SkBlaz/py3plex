#!/usr/bin/env python3
"""
Property-based tests for pipeline module.

Tests Pipeline class and PipelineStep composition.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import pipeline module
try:
    from py3plex.pipeline import (
        Pipeline,
        PipelineStep,
        ComputeStats,
    )
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    pytest.skip("pipeline module not available", allow_module_level=True)


# ============================================================================
# Mock pipeline steps for testing
# ============================================================================

class IdentityStep(PipelineStep):
    """A simple step that returns its input unchanged."""
    
    def transform(self, data):
        return data


class MultiplyStep(PipelineStep):
    """A step that multiplies numeric input by a factor."""
    
    def __init__(self, factor=2):
        self.factor = factor
    
    def transform(self, data):
        if data is None:
            return 0
        return data * self.factor


class AddStep(PipelineStep):
    """A step that adds a value to numeric input."""
    
    def __init__(self, value=1):
        self.value = value
    
    def transform(self, data):
        if data is None:
            return self.value
        return data + self.value


# ============================================================================
# Property Tests: PipelineStep base class
# ============================================================================

@pytest.mark.property
def test_pipeline_step_is_abstract():
    """Test that PipelineStep is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        PipelineStep()


@pytest.mark.property
def test_pipeline_step_get_params():
    """Test that PipelineStep subclass can get params."""
    step = MultiplyStep(factor=5)
    params = step.get_params()
    
    assert isinstance(params, dict), \
        "get_params should return a dictionary"
    assert 'factor' in params, \
        "Params should include step attributes"
    assert params['factor'] == 5, \
        "Param value should match attribute value"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(factor=st.integers(min_value=1, max_value=100))
def test_pipeline_step_set_params(factor):
    """Test that PipelineStep subclass can set params."""
    step = MultiplyStep(factor=2)
    step.set_params(factor=factor)
    
    assert step.factor == factor, \
        "set_params should update attribute value"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(factor=st.integers(min_value=1, max_value=100))
def test_pipeline_step_set_params_returns_self(factor):
    """Test that set_params returns self for chaining."""
    step = MultiplyStep(factor=2)
    result = step.set_params(factor=factor)
    
    assert result is step, \
        "set_params should return self for method chaining"


# ============================================================================
# Property Tests: Pipeline class
# ============================================================================

@pytest.mark.property
def test_pipeline_creation_with_empty_steps():
    """Test that Pipeline can be created with empty steps list."""
    pipeline = Pipeline([])
    
    assert len(pipeline.steps) == 0, \
        "Pipeline should accept empty steps list"
    assert len(pipeline.named_steps) == 0, \
        "named_steps should be empty"


@pytest.mark.property
def test_pipeline_creation_with_single_step():
    """Test that Pipeline can be created with a single step."""
    step = IdentityStep()
    pipeline = Pipeline([("identity", step)])
    
    assert len(pipeline.steps) == 1, \
        "Pipeline should have one step"
    assert "identity" in pipeline.named_steps, \
        "named_steps should contain step name"
    assert pipeline.named_steps["identity"] is step, \
        "named_steps should reference the step"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(num_steps=st.integers(min_value=1, max_value=10))
def test_pipeline_creation_with_multiple_steps(num_steps):
    """Test that Pipeline can be created with multiple steps."""
    steps = [(f"step_{i}", IdentityStep()) for i in range(num_steps)]
    pipeline = Pipeline(steps)
    
    assert len(pipeline.steps) == num_steps, \
        f"Pipeline should have {num_steps} steps"
    assert len(pipeline.named_steps) == num_steps, \
        "named_steps should have all steps"


@pytest.mark.property
def test_pipeline_validates_steps():
    """Test that Pipeline validates that steps are PipelineStep instances."""
    with pytest.raises(TypeError, match="must be a PipelineStep instance"):
        Pipeline([("invalid", "not a step")])


@pytest.mark.property
def test_pipeline_run_with_empty_steps():
    """Test that running empty pipeline returns None."""
    pipeline = Pipeline([])
    result = pipeline.run()
    
    assert result is None, \
        "Empty pipeline should return None"


@pytest.mark.property
def test_pipeline_run_with_identity_step():
    """Test that running pipeline with identity step works."""
    pipeline = Pipeline([("identity", IdentityStep())])
    result = pipeline.run()
    
    assert result is None, \
        "Identity step with None input should return None"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    factor=st.integers(min_value=1, max_value=10),
    value=st.integers(min_value=0, max_value=100)
)
def test_pipeline_run_with_multiple_steps(factor, value):
    """Test that pipeline executes steps in sequence."""
    # Pipeline: start with value -> multiply by factor
    pipeline = Pipeline([
        ("add", AddStep(value=value)),
        ("multiply", MultiplyStep(factor=factor)),
    ])
    
    result = pipeline.run()
    expected = value * factor
    
    assert result == expected, \
        "Pipeline should execute steps in sequence"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    value1=st.integers(min_value=1, max_value=50),
    value2=st.integers(min_value=1, max_value=50),
    factor=st.integers(min_value=1, max_value=10)
)
def test_pipeline_run_complex_sequence(value1, value2, factor):
    """Test that pipeline correctly chains multiple operations."""
    # Pipeline: value1 -> add value2 -> multiply by factor
    pipeline = Pipeline([
        ("add1", AddStep(value=value1)),
        ("add2", AddStep(value=value2)),
        ("multiply", MultiplyStep(factor=factor)),
    ])
    
    result = pipeline.run()
    expected = (value1 + value2) * factor
    
    assert result == expected, \
        "Pipeline should correctly chain operations"


@pytest.mark.property
def test_pipeline_repr():
    """Test that Pipeline has a string representation."""
    pipeline = Pipeline([
        ("step1", IdentityStep()),
        ("step2", IdentityStep()),
    ])
    
    repr_str = repr(pipeline)
    
    assert isinstance(repr_str, str), \
        "repr should return a string"
    assert "Pipeline" in repr_str, \
        "repr should mention Pipeline"
    assert "step1" in repr_str, \
        "repr should include step names"
    assert "step2" in repr_str, \
        "repr should include step names"


@pytest.mark.property
def test_pipeline_get_params_shallow():
    """Test that Pipeline.get_params(deep=False) returns steps."""
    steps = [("step1", IdentityStep())]
    pipeline = Pipeline(steps)
    
    params = pipeline.get_params(deep=False)
    
    assert isinstance(params, dict), \
        "get_params should return a dictionary"
    assert 'steps' in params, \
        "Shallow params should include 'steps'"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(factor=st.integers(min_value=1, max_value=100))
def test_pipeline_get_params_deep(factor):
    """Test that Pipeline.get_params(deep=True) returns nested params."""
    pipeline = Pipeline([
        ("multiply", MultiplyStep(factor=factor)),
    ])
    
    params = pipeline.get_params(deep=True)
    
    assert isinstance(params, dict), \
        "get_params should return a dictionary"
    assert 'multiply__factor' in params, \
        "Deep params should include nested step params"
    assert params['multiply__factor'] == factor, \
        "Nested param value should match"


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(
    factor1=st.integers(min_value=1, max_value=50),
    factor2=st.integers(min_value=1, max_value=50)
)
def test_pipeline_get_params_multiple_steps(factor1, factor2):
    """Test that get_params works with multiple steps."""
    pipeline = Pipeline([
        ("multiply1", MultiplyStep(factor=factor1)),
        ("multiply2", MultiplyStep(factor=factor2)),
    ])
    
    params = pipeline.get_params(deep=True)
    
    assert 'multiply1__factor' in params, \
        "Should have params for first step"
    assert 'multiply2__factor' in params, \
        "Should have params for second step"
    assert params['multiply1__factor'] == factor1, \
        "First step param should match"
    assert params['multiply2__factor'] == factor2, \
        "Second step param should match"


# ============================================================================
# Property Tests: Step composition properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(value=st.integers(min_value=0, max_value=1000))
def test_pipeline_identity_law(value):
    """Test that adding identity step doesn't change result."""
    # Pipeline with and without identity step should give same result
    pipeline_with_identity = Pipeline([
        ("add", AddStep(value=value)),
        ("identity", IdentityStep()),
    ])
    
    pipeline_without_identity = Pipeline([
        ("add", AddStep(value=value)),
    ])
    
    result_with = pipeline_with_identity.run()
    result_without = pipeline_without_identity.run()
    
    assert result_with == result_without, \
        "Identity step should not change result"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    value=st.integers(min_value=1, max_value=50),
    factor1=st.integers(min_value=1, max_value=10),
    factor2=st.integers(min_value=1, max_value=10)
)
def test_pipeline_associativity(value, factor1, factor2):
    """Test that multiplication steps are associative."""
    # (value * factor1) * factor2 == value * (factor1 * factor2)
    pipeline1 = Pipeline([
        ("add", AddStep(value=value)),
        ("multiply1", MultiplyStep(factor=factor1)),
        ("multiply2", MultiplyStep(factor=factor2)),
    ])
    
    pipeline2 = Pipeline([
        ("add", AddStep(value=value)),
        ("multiply", MultiplyStep(factor=factor1 * factor2)),
    ])
    
    result1 = pipeline1.run()
    result2 = pipeline2.run()
    
    assert result1 == result2, \
        "Pipeline operations should be associative"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
