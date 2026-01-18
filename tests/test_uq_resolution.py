"""Tests for UQ resolution order and schema validation.

This test module verifies the UQ compliance checklist requirements:
- Resolution order enforcement
- Schema validation
- Fail-fast error handling
- Determinism guarantees
"""

import pytest
import numpy as np

from py3plex.dsl.ast import UQConfig, ComputeItem
from py3plex.dsl.uq_resolution import (
    resolve_uq_config,
    validate_uq_result_schema,
    create_degenerate_uq_result,
    wrap_deterministic_as_uq,
    set_global_uq_defaults,
    get_global_uq_defaults,
    reset_global_uq_defaults,
    ResolvedUQConfig,
    UQResolutionError,
    UQSchemaValidationError,
    CANONICAL_UQ_SCHEMA,
    LIBRARY_UQ_DEFAULTS,
)


@pytest.fixture(autouse=True)
def reset_global_defaults():
    """Reset global UQ defaults before and after each test."""
    reset_global_uq_defaults()
    yield
    reset_global_uq_defaults()


class TestUQResolutionOrder:
    """Test UQ configuration resolution priority order."""
    
    def test_library_defaults_only(self):
        """Test resolution with only library defaults."""
        compute_item = ComputeItem(name="degree", uncertainty=True)
        
        resolved = resolve_uq_config(compute_item, None, "degree")
        
        assert resolved is not None
        assert resolved.method == LIBRARY_UQ_DEFAULTS["method"]
        assert resolved.n_samples == LIBRARY_UQ_DEFAULTS["n_samples"]
        assert resolved.ci == LIBRARY_UQ_DEFAULTS["ci"]
        assert resolved.provenance["method"] == "library_default"
    
    def test_global_defaults_override_library(self):
        """Test that global defaults override library defaults."""
        set_global_uq_defaults(method="bootstrap", n_samples=100, seed=42)
        
        compute_item = ComputeItem(name="degree", uncertainty=True)
        resolved = resolve_uq_config(compute_item, None, "degree")
        
        assert resolved.method == "bootstrap"
        assert resolved.n_samples == 100
        assert resolved.seed == 42
        assert resolved.provenance["method"] == "global_default"
        assert resolved.provenance["n_samples"] == "global_default"
    
    def test_query_level_overrides_global(self):
        """Test that query-level config overrides global defaults."""
        set_global_uq_defaults(method="bootstrap", n_samples=100)
        
        query_uq = UQConfig(method="perturbation", n_samples=50, ci=0.90, seed=123)
        compute_item = ComputeItem(name="degree", uncertainty=True)
        
        resolved = resolve_uq_config(compute_item, query_uq, "degree")
        
        assert resolved.method == "perturbation"
        assert resolved.n_samples == 50
        assert resolved.ci == 0.90
        assert resolved.seed == 123
        assert resolved.provenance["method"] == "query_level"
    
    def test_metric_level_overrides_query(self):
        """Test that metric-level config has highest priority."""
        query_uq = UQConfig(method="perturbation", n_samples=50, seed=100)
        compute_item = ComputeItem(
            name="degree",
            uncertainty=True,
            method="bootstrap",
            n_samples=200,
            random_state=999,
        )
        
        resolved = resolve_uq_config(compute_item, query_uq, "degree")
        
        assert resolved.method == "bootstrap"
        assert resolved.n_samples == 200
        assert resolved.seed == 999
        assert resolved.provenance["method"] == "metric_level"
        assert resolved.provenance["n_samples"] == "metric_level"
        assert resolved.provenance["seed"] == "metric_level"
    
    def test_explicit_disable_at_metric_level(self):
        """Test that uncertainty=False at metric level can be overridden by query-level UQ.
        
        Note: The new resolution logic allows query-level UQ to enable uncertainty
        even if the compute item has uncertainty=False (which is just the default).
        """
        query_uq = UQConfig(method="bootstrap", n_samples=100)
        compute_item = ComputeItem(name="degree", uncertainty=False)
        
        # With query-level UQ set, uncertainty should be enabled
        resolved = resolve_uq_config(compute_item, query_uq, "degree")
        
        # Query-level UQ enables uncertainty
        assert resolved is not None
        assert resolved.method == "bootstrap"
        assert resolved.n_samples == 100
    
    def test_partial_override_preserves_lower_priority(self):
        """Test that partial overrides preserve values from lower priorities."""
        set_global_uq_defaults(method="bootstrap", n_samples=100, ci=0.95, seed=42)
        
        # Query only overrides method
        query_uq = UQConfig(method="perturbation")
        compute_item = ComputeItem(name="degree", uncertainty=True)
        
        resolved = resolve_uq_config(compute_item, query_uq, "degree")
        
        assert resolved.method == "perturbation"  # From query
        assert resolved.n_samples == 100  # From global
        assert resolved.ci == 0.95  # From global
        assert resolved.seed == 42  # From global
        assert resolved.provenance["method"] == "query_level"
        assert resolved.provenance["n_samples"] == "global_default"
    
    def test_bootstrap_specific_params(self):
        """Test resolution of bootstrap-specific parameters."""
        compute_item = ComputeItem(
            name="degree",
            uncertainty=True,
            method="bootstrap",
            bootstrap_unit="nodes",
            bootstrap_mode="permute",
        )
        
        resolved = resolve_uq_config(compute_item, None, "degree")
        
        assert resolved.kwargs["bootstrap_unit"] == "nodes"
        assert resolved.kwargs["bootstrap_mode"] == "permute"
        assert resolved.provenance["bootstrap_unit"] == "metric_level"
    
    def test_null_model_specific_params(self):
        """Test resolution of null model specific parameters."""
        compute_item = ComputeItem(
            name="betweenness",
            uncertainty=True,
            method="null_model",
            n_null=50,
            null_model="configuration",
        )
        
        resolved = resolve_uq_config(compute_item, None, "betweenness")
        
        assert resolved.kwargs["n_null"] == 50
        assert resolved.kwargs["null_model"] == "configuration"
        assert resolved.provenance["null_model"] == "metric_level"


class TestUQValidation:
    """Test UQ configuration validation."""
    
    def test_valid_bootstrap_config(self):
        """Test validation of valid bootstrap configuration."""
        resolved = ResolvedUQConfig(
            method="bootstrap",
            n_samples=100,
            ci=0.95,
            seed=42,
            kwargs={"bootstrap_unit": "edges", "bootstrap_mode": "resample"},
            context="metric:degree",
        )
        
        # Should not raise
        resolved.validate()
    
    def test_invalid_method_raises_error(self):
        """Test that invalid method raises UQResolutionError."""
        resolved = ResolvedUQConfig(
            method="invalid_method",
            n_samples=100,
            ci=0.95,
            seed=42,
            context="metric:degree",
        )
        
        with pytest.raises(UQResolutionError) as exc_info:
            resolved.validate()
        
        assert "Invalid UQ method" in str(exc_info.value)
        assert "invalid_method" in str(exc_info.value)
    
    def test_invalid_n_samples_raises_error(self):
        """Test that non-positive n_samples raises error."""
        resolved = ResolvedUQConfig(
            method="bootstrap",
            n_samples=0,
            ci=0.95,
            seed=42,
            context="metric:degree",
        )
        
        with pytest.raises(UQResolutionError) as exc_info:
            resolved.validate()
        
        assert "n_samples must be positive" in str(exc_info.value)
    
    def test_invalid_ci_raises_error(self):
        """Test that invalid ci level raises error."""
        for invalid_ci in [0.0, 1.0, -0.5, 1.5]:
            resolved = ResolvedUQConfig(
                method="bootstrap",
                n_samples=100,
                ci=invalid_ci,
                seed=42,
                context="metric:degree",
            )
            
            with pytest.raises(UQResolutionError):
                resolved.validate()
    
    def test_bootstrap_without_unit_uses_default(self):
        """Test that bootstrap without unit uses default."""
        resolved = ResolvedUQConfig(
            method="bootstrap",
            n_samples=100,
            ci=0.95,
            seed=42,
            kwargs={},  # No bootstrap_unit specified
            context="metric:degree",
        )
        
        # Should not raise - default "edges" is used
        resolved.validate()
    
    def test_invalid_bootstrap_unit_raises_error(self):
        """Test that invalid bootstrap unit raises error."""
        resolved = ResolvedUQConfig(
            method="bootstrap",
            n_samples=100,
            ci=0.95,
            seed=42,
            kwargs={"bootstrap_unit": "invalid"},
            context="metric:degree",
        )
        
        with pytest.raises(UQResolutionError) as exc_info:
            resolved.validate()
        
        assert "Invalid bootstrap_unit" in str(exc_info.value)
    
    def test_null_model_without_model_type_raises_error(self):
        """Test that null_model method without model type raises error."""
        resolved = ResolvedUQConfig(
            method="null_model",
            n_samples=100,
            ci=0.95,
            seed=42,
            kwargs={},  # Missing null_model parameter
            context="metric:betweenness",
        )
        
        with pytest.raises(UQResolutionError) as exc_info:
            resolved.validate()
        
        assert "null_model method requires 'null_model' parameter" in str(exc_info.value)


class TestUQSchemaValidation:
    """Test canonical UQ schema validation."""
    
    def test_valid_uq_result_schema(self):
        """Test validation of valid UQ result."""
        result = {
            "mean": 5.0,
            "std": 0.5,
            "ci_low": 4.0,
            "ci_high": 6.0,
            "quantiles": {0.025: 4.0, 0.975: 6.0},
            "n_samples": 100,
            "method": "bootstrap",
            "seed": 42,
        }
        
        # Should not raise
        validate_uq_result_schema(result, "degree")
    
    def test_missing_required_field_raises_error(self):
        """Test that missing required field raises error."""
        result = {
            "mean": 5.0,
            # Missing "std"
            "n_samples": 100,
            "method": "bootstrap",
        }
        
        with pytest.raises(UQSchemaValidationError) as exc_info:
            validate_uq_result_schema(result, "degree")
        
        assert "missing required fields" in str(exc_info.value)
        assert "std" in str(exc_info.value)
    
    def test_missing_point_estimate_raises_error(self):
        """Test that missing value/mean raises error."""
        result = {
            # Missing "value" or "mean"
            "std": 0.5,
            "n_samples": 100,
            "method": "bootstrap",
        }
        
        with pytest.raises(UQSchemaValidationError) as exc_info:
            validate_uq_result_schema(result, "degree")
        
        assert "missing point estimate" in str(exc_info.value)
    
    def test_accepts_value_or_mean(self):
        """Test that both 'value' and 'mean' are accepted as point estimate."""
        # Using "mean"
        result_mean = {
            "mean": 5.0,
            "std": 0.5,
            "ci_low": 4.0,
            "ci_high": 6.0,
            "quantiles": {},
            "n_samples": 100,
            "method": "bootstrap",
        }
        validate_uq_result_schema(result_mean, "degree")
        
        # Using "value"
        result_value = {
            "value": 5.0,
            "std": 0.5,
            "ci_low": 4.0,
            "ci_high": 6.0,
            "quantiles": {},
            "n_samples": 100,
            "method": "bootstrap",
        }
        validate_uq_result_schema(result_value, "degree")
    
    def test_requires_ci_bounds_or_quantiles(self):
        """Test that at least ci_low/ci_high or quantiles is required."""
        # Missing both
        result = {
            "mean": 5.0,
            "std": 0.5,
            "n_samples": 100,
            "method": "bootstrap",
        }
        
        with pytest.raises(UQSchemaValidationError) as exc_info:
            validate_uq_result_schema(result, "degree")
        
        assert "ci_low, ci_high" in str(exc_info.value) or "quantiles" in str(exc_info.value)
    
    def test_quantiles_structure_validation(self):
        """Test that quantiles dictionary is validated."""
        # Invalid quantile key (> 1)
        result = {
            "mean": 5.0,
            "std": 0.5,
            "quantiles": {1.5: 6.0},  # Invalid key
            "n_samples": 100,
            "method": "bootstrap",
        }
        
        with pytest.raises(UQSchemaValidationError) as exc_info:
            validate_uq_result_schema(result, "degree")
        
        assert "invalid quantile key" in str(exc_info.value)
    
    def test_invalid_n_samples_raises_error(self):
        """Test that invalid n_samples raises error."""
        result = {
            "mean": 5.0,
            "std": 0.5,
            "ci_low": 4.0,
            "ci_high": 6.0,
            "quantiles": {},
            "n_samples": 0,  # Invalid
            "method": "bootstrap",
        }
        
        with pytest.raises(UQSchemaValidationError) as exc_info:
            validate_uq_result_schema(result, "degree")
        
        assert "invalid 'n_samples'" in str(exc_info.value)
    
    def test_degenerate_uq_with_allow_flag(self):
        """Test that degenerate UQ (std=0) is allowed with flag."""
        result = {
            "mean": 5.0,
            "std": 0.0,  # Degenerate
            "n_samples": 1,
            "method": "deterministic",
        }
        
        # Should not raise with allow_degenerate=True
        validate_uq_result_schema(result, "degree", allow_degenerate=True)


class TestDegenerateUQResults:
    """Test creation of degenerate UQ results for deterministic metrics."""
    
    def test_create_degenerate_result(self):
        """Test creation of degenerate UQ result."""
        result = create_degenerate_uq_result(5.0, method="deterministic", seed=42)
        
        assert result["mean"] == 5.0
        assert result["value"] == 5.0
        assert result["std"] == 0.0
        assert result["ci_low"] == 5.0
        assert result["ci_high"] == 5.0
        assert result["certainty"] == 1.0
        assert result["seed"] == 42
        
        # Should pass schema validation with allow_degenerate
        validate_uq_result_schema(result, "degree", allow_degenerate=True)
    
    def test_wrap_scalar_as_uq(self):
        """Test wrapping a scalar value with UQ scaffolding."""
        resolved = ResolvedUQConfig(
            method="perturbation",
            n_samples=50,
            ci=0.95,
            seed=42,
            context="metric:degree",
        )
        
        result = wrap_deterministic_as_uq(5.0, resolved)
        
        assert result["mean"] == 5.0
        assert result["std"] == 0.0
        assert result["method"] == "perturbation"
        assert result["n_samples"] == 50
        assert result["seed"] == 42
    
    def test_wrap_dict_preserves_structure(self):
        """Test that wrapping an existing dict preserves it."""
        existing_uq = {
            "mean": 5.0,
            "std": 0.5,
            "quantiles": {},
            "n_samples": 100,
            "method": "bootstrap",
        }
        
        resolved = ResolvedUQConfig(
            method="perturbation",
            n_samples=50,
            ci=0.95,
            seed=42,
            context="metric:degree",
        )
        
        result = wrap_deterministic_as_uq(existing_uq, resolved)
        
        # Should return the existing dict unchanged
        assert result == existing_uq
    
    def test_wrap_non_numeric_value(self):
        """Test wrapping a non-numeric value."""
        resolved = ResolvedUQConfig(
            method="perturbation",
            n_samples=50,
            ci=0.95,
            seed=42,
            context="metric:label",
        )
        
        result = wrap_deterministic_as_uq("category_a", resolved)
        
        assert result["value"] == "category_a"
        assert result["std"] is None
        assert "_warning" in result


class TestGlobalDefaults:
    """Test global UQ defaults management."""
    
    def test_set_and_get_global_defaults(self):
        """Test setting and retrieving global defaults."""
        set_global_uq_defaults(method="bootstrap", n_samples=200, seed=999)
        
        defaults = get_global_uq_defaults()
        
        assert defaults["method"] == "bootstrap"
        assert defaults["n_samples"] == 200
        assert defaults["seed"] == 999
    
    def test_reset_global_defaults(self):
        """Test resetting global defaults."""
        set_global_uq_defaults(method="bootstrap", n_samples=200)
        
        reset_global_uq_defaults()
        
        defaults = get_global_uq_defaults()
        assert defaults == {}
    
    def test_partial_update_of_global_defaults(self):
        """Test partial update of global defaults."""
        set_global_uq_defaults(method="bootstrap", n_samples=100)
        set_global_uq_defaults(seed=42)  # Partial update
        
        defaults = get_global_uq_defaults()
        
        assert defaults["method"] == "bootstrap"  # Preserved
        assert defaults["n_samples"] == 100  # Preserved
        assert defaults["seed"] == 42  # Added


class TestProvenance:
    """Test provenance tracking in resolved UQ config."""
    
    def test_provenance_records_source(self):
        """Test that provenance records source of each setting."""
        set_global_uq_defaults(method="bootstrap", n_samples=100)
        query_uq = UQConfig(seed=42)
        compute_item = ComputeItem(name="degree", uncertainty=True, ci=0.90)
        
        resolved = resolve_uq_config(compute_item, query_uq, "degree")
        
        assert resolved.provenance["method"] == "global_default"
        assert resolved.provenance["n_samples"] == "global_default"
        assert resolved.provenance["seed"] == "query_level"
        assert resolved.provenance["ci"] == "metric_level"
    
    def test_to_dict_includes_provenance(self):
        """Test that to_dict() includes provenance."""
        resolved = ResolvedUQConfig(
            method="bootstrap",
            n_samples=100,
            ci=0.95,
            seed=42,
            provenance={"method": "query_level", "n_samples": "global_default"},
            context="metric:degree",
        )
        
        d = resolved.to_dict()
        
        assert "provenance" in d
        assert d["provenance"]["method"] == "query_level"
        assert d["context"] == "metric:degree"


class TestDeterminism:
    """Test determinism guarantees with seeds."""
    
    def test_same_seed_same_resolution(self):
        """Test that same seed produces same resolution."""
        compute_item = ComputeItem(
            name="degree",
            uncertainty=True,
            method="bootstrap",
            random_state=42,
        )
        
        resolved1 = resolve_uq_config(compute_item, None, "degree")
        resolved2 = resolve_uq_config(compute_item, None, "degree")
        
        assert resolved1.seed == resolved2.seed == 42
        assert resolved1.method == resolved2.method
        assert resolved1.n_samples == resolved2.n_samples


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
