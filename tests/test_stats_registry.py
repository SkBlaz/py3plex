"""Tests for statistics registry."""

import pytest

from py3plex.stats import (
    StatisticSpec,
    StatisticsRegistry,
    register_statistic,
    get_statistic,
    list_statistics,
    Delta,
    Gaussian,
)


class TestStatisticsRegistry:
    """Tests for StatisticsRegistry."""
    
    def test_register_statistic_success(self):
        """Test successful registration."""
        registry = StatisticsRegistry()
        
        def compute_fn(x):
            return x * 2
        
        def uncertainty_fn(x):
            return Delta(0.0)
        
        spec = StatisticSpec(
            name="double",
            estimator=compute_fn,
            uncertainty_model=uncertainty_fn
        )
        
        registry.register_statistic(spec)
        assert registry.has_statistic("double")
    
    def test_register_missing_uncertainty(self):
        """Test that registration fails without uncertainty model."""
        registry = StatisticsRegistry()
        
        def compute_fn(x):
            return x * 2
        
        # This should fail
        with pytest.raises(ValueError, match="uncertainty_model is required"):
            spec = StatisticSpec(
                name="bad",
                estimator=compute_fn,
                uncertainty_model=None  # type: ignore
            )
            registry.register_statistic(spec)
    
    def test_register_duplicate(self):
        """Test that duplicate registration fails."""
        registry = StatisticsRegistry()
        
        spec = StatisticSpec(
            name="test",
            estimator=lambda x: x,
            uncertainty_model=lambda x: Delta(0.0)
        )
        
        registry.register_statistic(spec)
        
        # Second registration should fail
        with pytest.raises(ValueError, match="already registered"):
            registry.register_statistic(spec)
    
    def test_register_force_overwrite(self):
        """Test forced overwrite."""
        registry = StatisticsRegistry()
        
        spec1 = StatisticSpec(
            name="test",
            estimator=lambda x: x,
            uncertainty_model=lambda x: Delta(0.0)
        )
        
        spec2 = StatisticSpec(
            name="test",
            estimator=lambda x: x * 2,
            uncertainty_model=lambda x: Delta(0.01)
        )
        
        registry.register_statistic(spec1)
        registry.register_statistic_force(spec2)
        
        # Should have the second spec
        retrieved = registry.get_statistic("test")
        assert retrieved.estimator(5) == 10  # x * 2
    
    def test_get_statistic_not_found(self):
        """Test retrieval of non-existent statistic."""
        registry = StatisticsRegistry()
        
        with pytest.raises(KeyError, match="not found"):
            registry.get_statistic("nonexistent")
    
    def test_list_statistics(self):
        """Test listing all statistics."""
        registry = StatisticsRegistry()
        
        spec1 = StatisticSpec("a", lambda x: x, lambda x: Delta(0.0))
        spec2 = StatisticSpec("b", lambda x: x, lambda x: Delta(0.0))
        spec3 = StatisticSpec("c", lambda x: x, lambda x: Delta(0.0))
        
        registry.register_statistic(spec1)
        registry.register_statistic(spec2)
        registry.register_statistic(spec3)
        
        stats = registry.list_statistics()
        assert stats == ["a", "b", "c"]  # Sorted
    
    def test_compute_without_uncertainty(self):
        """Test computing raw value without uncertainty."""
        registry = StatisticsRegistry()
        
        spec = StatisticSpec(
            name="square",
            estimator=lambda x: x ** 2,
            uncertainty_model=lambda x: Delta(0.0)
        )
        
        registry.register_statistic(spec)
        
        result = registry.compute("square", 5, with_uncertainty=False)
        assert result == 25
        assert not hasattr(result, "uncertainty")
    
    def test_compute_with_uncertainty(self):
        """Test computing StatValue with uncertainty."""
        registry = StatisticsRegistry()
        
        spec = StatisticSpec(
            name="identity",
            estimator=lambda x: x,
            uncertainty_model=lambda x: Gaussian(0.0, 0.1)
        )
        
        registry.register_statistic(spec)
        
        result = registry.compute("identity", 5.0, with_uncertainty=True)
        
        # Should be a StatValue
        from py3plex.stats import StatValue
        assert isinstance(result, StatValue)
        assert float(result) == 5.0
        assert result.std() == 0.1


class TestGlobalRegistry:
    """Tests for global registry functions."""
    
    def test_global_register_and_get(self):
        """Test global register and get functions."""
        # Register a test statistic
        spec = StatisticSpec(
            name="test_global",
            estimator=lambda x: x * 3,
            uncertainty_model=lambda x: Delta(0.0)
        )
        
        register_statistic(spec, force=True)  # Use force to avoid conflicts
        
        # Retrieve it
        retrieved = get_statistic("test_global")
        assert retrieved.name == "test_global"
        assert retrieved.estimator(4) == 12
    
    def test_global_list(self):
        """Test global list function."""
        # Register a statistic
        spec = StatisticSpec(
            name="test_list",
            estimator=lambda x: x,
            uncertainty_model=lambda x: Delta(0.0)
        )
        
        register_statistic(spec, force=True)
        
        # List should include it
        stats = list_statistics()
        assert "test_list" in stats


class TestStatisticSpecValidation:
    """Tests for StatisticSpec validation."""
    
    def test_spec_with_assumptions(self):
        """Test spec with assumptions."""
        spec = StatisticSpec(
            name="test",
            estimator=lambda x: x,
            uncertainty_model=lambda x: Delta(0.0),
            assumptions=["independence", "normality"]
        )
        
        assert "independence" in spec.assumptions
        assert "normality" in spec.assumptions
    
    def test_spec_with_supports(self):
        """Test spec with supports metadata."""
        spec = StatisticSpec(
            name="test",
            estimator=lambda x: x,
            uncertainty_model=lambda x: Delta(0.0),
            supports={"directed": True, "weighted": True}
        )
        
        assert spec.supports["directed"] is True
        assert spec.supports["weighted"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
