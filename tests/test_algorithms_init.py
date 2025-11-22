"""
Tests for py3plex.algorithms module initialization and exports.

This tests that the algorithms module properly exports its public API.
"""
import pytest


def test_algorithms_module_imports():
    """Test that algorithms module can be imported."""
    from py3plex import algorithms
    assert algorithms is not None


def test_multiplex_participation_coefficient_available():
    """Test that multiplex_participation_coefficient is available."""
    from py3plex.algorithms import multiplex_participation_coefficient
    assert callable(multiplex_participation_coefficient)


def test_meta_flow_report_available():
    """Test that MetaFlowReport is available."""
    from py3plex.algorithms import MetaFlowReport
    assert MetaFlowReport is not None


def test_run_meta_analysis_available():
    """Test that run_meta_analysis is available."""
    from py3plex.algorithms import run_meta_analysis
    assert callable(run_meta_analysis)


def test_sir_functions_available():
    """Test that SIR functions are available (may be placeholders)."""
    from py3plex.algorithms import (
        simulate_sir_multiplex_discrete,
        simulate_sir_multiplex_gillespie,
        basic_reproduction_number,
        summarize,
    )
    
    # These should be available, either as real functions or placeholders
    assert simulate_sir_multiplex_discrete is not None
    assert simulate_sir_multiplex_gillespie is not None
    assert basic_reproduction_number is not None
    assert summarize is not None


def test_algorithms_all_exports():
    """Test that __all__ is properly defined in algorithms module."""
    from py3plex import algorithms
    
    assert hasattr(algorithms, "__all__")
    assert isinstance(algorithms.__all__, list)
    assert len(algorithms.__all__) > 0
    
    # Check that all exported names are actually available
    for name in algorithms.__all__:
        assert hasattr(algorithms, name), f"{name} not found in algorithms module"


def test_sir_available_flag():
    """Test that SIR_AVAILABLE flag indicates if SIR is properly loaded."""
    from py3plex.algorithms import SIR_AVAILABLE
    
    # Should be a boolean
    assert isinstance(SIR_AVAILABLE, bool)


def test_sir_not_available_raises_import_error():
    """Test that SIR placeholder functions raise ImportError when not available."""
    from py3plex.algorithms import SIR_AVAILABLE
    
    if not SIR_AVAILABLE:
        from py3plex.algorithms import simulate_sir_multiplex_discrete
        
        with pytest.raises(ImportError, match="SIR epidemic simulator requires"):
            simulate_sir_multiplex_discrete()


def test_algorithms_no_import_errors():
    """Test that importing algorithms module doesn't raise unexpected errors."""
    # This should not raise any exceptions
    import py3plex.algorithms
    assert True  # If we got here, no errors were raised
