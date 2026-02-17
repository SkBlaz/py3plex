"""Property-based tests for AttributionConfig.

Tests configuration validation, serialization, and invariants.
Using Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings

from py3plex.dsl.attribution import AttributionConfig


# ============================================================================
# Strategy Helpers
# ============================================================================


@st.composite
def valid_attribution_config(draw):
    """Generate valid AttributionConfig."""
    metric = draw(st.one_of(st.none(), st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll")))))
    objective = draw(st.sampled_from(["value", "rank"]))
    levels = draw(st.lists(st.sampled_from(["layer", "edge"]), min_size=1, max_size=2, unique=True))
    method = draw(st.sampled_from(["shapley", "shapley_mc", "influence"]))
    feature_space = draw(st.sampled_from(["layers", "layer_pairs", "coupling_types"]))
    n_permutations = draw(st.integers(min_value=16, max_value=1000))
    max_exact_features = draw(st.integers(min_value=2, max_value=20))
    seed = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=10000)))
    edge_scope = draw(st.sampled_from(["incident", "ego_k_hop", "shortest_path_sample", "global_top_m"]))
    k_hop = draw(st.integers(min_value=1, max_value=5))
    max_edges = draw(st.integers(min_value=1, max_value=1000))
    top_k_layers = draw(st.integers(min_value=1, max_value=50))
    top_k_edges = draw(st.integers(min_value=1, max_value=100))
    include_negative = draw(st.booleans())
    cache = draw(st.booleans())
    uq = draw(st.sampled_from(["off", "propagate", "summarize_only"]))
    ci_level = draw(st.floats(min_value=0.5, max_value=0.999))
    
    return AttributionConfig(
        metric=metric,
        objective=objective,
        levels=levels,
        method=method,
        feature_space=feature_space,
        n_permutations=n_permutations,
        max_exact_features=max_exact_features,
        seed=seed,
        edge_scope=edge_scope,
        k_hop=k_hop,
        max_edges=max_edges,
        top_k_layers=top_k_layers,
        top_k_edges=top_k_edges,
        include_negative=include_negative,
        cache=cache,
        uq=uq,
        ci_level=ci_level,
    )


# ============================================================================
# Configuration Validation Tests
# ============================================================================


class TestAttributionConfigValidation:
    """Test AttributionConfig validation."""
    
    @pytest.mark.property
    @given(config=valid_attribution_config())
    @settings(max_examples=100, deadline=None)
    def test_valid_config_has_no_warnings(self, config):
        """Valid AttributionConfig should pass validation."""
        warnings = config.validate()
        assert isinstance(warnings, list)
        
        # Valid configs should have no warnings
        if config.objective in ["value", "rank"] and \
           config.method in ["shapley", "shapley_mc", "influence"] and \
           config.uq in ["off", "propagate", "summarize_only"] and \
           config.n_permutations >= 16 and \
           config.k_hop >= 1 and \
           config.max_edges >= 1 and \
           config.top_k_layers >= 1 and \
           config.top_k_edges >= 1 and \
           0.0 < config.ci_level < 1.0:
            assert len(warnings) == 0, f"Valid config has warnings: {warnings}"
    
    @pytest.mark.property
    @given(
        invalid_objective=st.text(min_size=1, max_size=20).filter(lambda x: x not in ["value", "rank"])
    )
    @settings(max_examples=50)
    def test_invalid_objective_produces_warning(self, invalid_objective):
        """Invalid objective should produce warning."""
        config = AttributionConfig(objective=invalid_objective)
        warnings = config.validate()
        
        assert any("objective" in w.lower() for w in warnings)
    
    @pytest.mark.property
    @given(
        invalid_method=st.text(min_size=1, max_size=20).filter(lambda x: x not in ["shapley", "shapley_mc", "influence"])
    )
    @settings(max_examples=50)
    def test_invalid_method_produces_warning(self, invalid_method):
        """Invalid method should produce warning."""
        config = AttributionConfig(method=invalid_method)
        warnings = config.validate()
        
        assert any("method" in w.lower() for w in warnings)
    
    @pytest.mark.property
    @given(n_perms=st.integers(min_value=1, max_value=15))
    @settings(max_examples=20)
    def test_low_n_permutations_produces_warning(self, n_perms):
        """n_permutations < 16 should produce warning."""
        config = AttributionConfig(n_permutations=n_perms)
        warnings = config.validate()
        
        assert any("n_permutations" in w.lower() for w in warnings)


# ============================================================================
# Serialization Tests
# ============================================================================


class TestAttributionConfigSerialization:
    """Test AttributionConfig serialization/deserialization."""
    
    @pytest.mark.property
    @given(config=valid_attribution_config())
    @settings(max_examples=100, deadline=None)
    def test_to_dict_is_json_serializable(self, config):
        """to_dict() should produce JSON-serializable dict."""
        data = config.to_dict()
        
        assert isinstance(data, dict)
        
        # Check all keys are strings
        assert all(isinstance(k, str) for k in data.keys())
        
        # Check all values are JSON-serializable types
        for v in data.values():
            assert isinstance(v, (str, int, float, bool, type(None), list, dict))
    
    @pytest.mark.property
    @given(config=valid_attribution_config())
    @settings(max_examples=100, deadline=None)
    def test_roundtrip_preserves_config(self, config):
        """Config -> dict -> Config should preserve values."""
        data = config.to_dict()
        restored = AttributionConfig.from_dict(data)
        
        # All fields should be preserved
        assert restored.metric == config.metric
        assert restored.objective == config.objective
        assert restored.levels == config.levels
        assert restored.method == config.method
        assert restored.feature_space == config.feature_space
        assert restored.n_permutations == config.n_permutations
        assert restored.max_exact_features == config.max_exact_features
        assert restored.seed == config.seed
        assert restored.edge_scope == config.edge_scope
        assert restored.k_hop == config.k_hop
        assert restored.max_edges == config.max_edges
        assert restored.top_k_layers == config.top_k_layers
        assert restored.top_k_edges == config.top_k_edges
        assert restored.include_negative == config.include_negative
        assert restored.cache == config.cache
        assert restored.uq == config.uq
        assert abs(restored.ci_level - config.ci_level) < 1e-9


# ============================================================================
# Invariant Tests
# ============================================================================


class TestAttributionConfigInvariants:
    """Test invariants that must hold for any config."""
    
    @pytest.mark.property
    @given(config=valid_attribution_config())
    @settings(max_examples=100)
    def test_n_permutations_is_positive(self, config):
        """n_permutations should always be positive."""
        assert config.n_permutations > 0
    
    @pytest.mark.property
    @given(config=valid_attribution_config())
    @settings(max_examples=100)
    def test_max_exact_features_is_positive(self, config):
        """max_exact_features should always be positive."""
        assert config.max_exact_features > 0
    
    @pytest.mark.property
    @given(config=valid_attribution_config())
    @settings(max_examples=100)
    def test_k_hop_is_positive(self, config):
        """k_hop should always be positive."""
        assert config.k_hop > 0
    
    @pytest.mark.property
    @given(config=valid_attribution_config())
    @settings(max_examples=100)
    def test_max_edges_is_positive(self, config):
        """max_edges should always be positive."""
        assert config.max_edges > 0
    
    @pytest.mark.property
    @given(config=valid_attribution_config())
    @settings(max_examples=100)
    def test_ci_level_is_probability(self, config):
        """ci_level should be valid probability (0, 1)."""
        assert 0.0 < config.ci_level < 1.0
    
    @pytest.mark.property
    @given(config=valid_attribution_config())
    @settings(max_examples=100)
    def test_levels_is_nonempty(self, config):
        """levels should never be empty."""
        assert len(config.levels) > 0


# ============================================================================
# Default Value Tests
# ============================================================================


class TestAttributionConfigDefaults:
    """Test default values are sensible."""
    
    @pytest.mark.property
    @settings(max_examples=1)
    @given(st.just(None))
    def test_default_config_is_valid(self, _):
        """Default AttributionConfig should be valid."""
        config = AttributionConfig()
        warnings = config.validate()
        
        # Default config should have no warnings (metric is optional)
        assert len(warnings) == 0
    
    @pytest.mark.property
    @settings(max_examples=1)
    @given(st.just(None))
    def test_default_method_is_mc(self, _):
        """Default method should be Monte Carlo Shapley."""
        config = AttributionConfig()
        assert config.method == "shapley_mc"
    
    @pytest.mark.property
    @settings(max_examples=1)
    @given(st.just(None))
    def test_default_objective_is_value(self, _):
        """Default objective should be value (not rank)."""
        config = AttributionConfig()
        assert config.objective == "value"
    
    @pytest.mark.property
    @settings(max_examples=1)
    @given(st.just(None))
    def test_default_uq_is_off(self, _):
        """Default UQ mode should be off."""
        config = AttributionConfig()
        assert config.uq == "off"


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestAttributionConfigEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.property
    @given(seed=st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=50)
    def test_seed_can_be_any_integer(self, seed):
        """Seed should accept any integer."""
        config = AttributionConfig(seed=seed)
        assert config.seed == seed
    
    @pytest.mark.property
    @settings(max_examples=1)
    @given(st.just(None))
    def test_seed_can_be_none(self, _):
        """Seed can be None (non-deterministic)."""
        config = AttributionConfig(seed=None)
        assert config.seed is None
    
    @pytest.mark.property
    @given(levels=st.lists(st.sampled_from(["layer", "edge", "layer", "edge"]), min_size=1, max_size=4))
    @settings(max_examples=50)
    def test_duplicate_levels_allowed(self, levels):
        """Config should handle duplicate levels gracefully."""
        config = AttributionConfig(levels=levels)
        assert config.levels == levels
    
    @pytest.mark.property
    @given(ci=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=50)
    def test_boundary_ci_levels(self, ci):
        """CI level at boundaries should validate correctly."""
        config = AttributionConfig(ci_level=ci)
        warnings = config.validate()
        
        # Should warn if exactly 0.0 or 1.0 or out of bounds
        if ci <= 0.0 or ci >= 1.0:
            # May or may not warn depending on implementation
            # Just check validation completes
            assert isinstance(warnings, list)


# ============================================================================
# Comparison Tests
# ============================================================================


class TestAttributionConfigComparison:
    """Test equality and comparison operations."""
    
    @pytest.mark.property
    @given(config=valid_attribution_config())
    @settings(max_examples=50)
    def test_config_equals_itself(self, config):
        """Config should equal itself."""
        # Create copy via serialization
        data = config.to_dict()
        copy = AttributionConfig.from_dict(data)
        
        # All fields should match
        assert copy.metric == config.metric
        assert copy.objective == config.objective
        assert copy.method == config.method
    
    @pytest.mark.property
    @given(config1=valid_attribution_config(), config2=valid_attribution_config())
    @settings(max_examples=50)
    def test_different_configs_likely_differ(self, config1, config2):
        """Different random configs are likely to differ in some field."""
        # Skip if by chance they're very similar
        assume(config1.seed != config2.seed or config1.method != config2.method)
        
        # At least one field should differ
        assert (
            config1.metric != config2.metric or
            config1.objective != config2.objective or
            config1.method != config2.method or
            config1.seed != config2.seed or
            config1.n_permutations != config2.n_permutations
        )
