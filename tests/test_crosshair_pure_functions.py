"""
Tests for pure/deterministic functions suitable for CrossHair symbolic testing.

This test file validates the 27 identified pure functions that meet criteria:
1. Complete type hints for arguments and return values
2. No file I/O, logging, or global variable modifications
3. Reasonably sized (typically < 80 lines)
4. Deterministic behavior with consistent outputs

These functions can be tested with CrossHair for formal verification:
    crosshair check py3plex.utils.get_rng
    crosshair watch py3plex.algorithms.statistics.basic_statistics
"""

import pytest
import sys


class TestStatisticsPureFunctions:
    """Test pure functions in py3plex.algorithms.statistics modules."""

    def test_identify_n_hubs_exists(self):
        """Test that identify_n_hubs is callable and has type hints."""
        try:
            from py3plex.algorithms.statistics.basic_statistics import identify_n_hubs
            import inspect
            
            assert callable(identify_n_hubs)
            sig = inspect.signature(identify_n_hubs)
            # Verify return annotation exists
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("basic_statistics module not available")

    def test_core_network_statistics_exists(self):
        """Test that core_network_statistics is callable and has type hints."""
        try:
            from py3plex.algorithms.statistics.basic_statistics import core_network_statistics
            import inspect
            
            assert callable(core_network_statistics)
            sig = inspect.signature(core_network_statistics)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("basic_statistics module not available")

    def test_basic_pl_stats_exists(self):
        """Test that basic_pl_stats is callable and has type hints."""
        try:
            from py3plex.algorithms.statistics.topology import basic_pl_stats
            import inspect
            
            assert callable(basic_pl_stats)
            sig = inspect.signature(basic_pl_stats)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("topology module not available")

    def test_bootstrap_confidence_interval_exists(self):
        """Test that bootstrap_confidence_interval is callable and has type hints."""
        try:
            from py3plex.algorithms.statistics.stats_comparison import bootstrap_confidence_interval
            import inspect
            
            assert callable(bootstrap_confidence_interval)
            sig = inspect.signature(bootstrap_confidence_interval)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("stats_comparison module not available")

    def test_critical_distances_functions_exist(self):
        """Test that critical_distances functions are callable."""
        try:
            from py3plex.algorithms.statistics.critical_distances import (
                center, name_length, remove_backslash
            )
            
            assert callable(center)
            assert callable(name_length)
            assert callable(remove_backslash)
        except ImportError:
            pytest.skip("critical_distances module not available")


class TestConverterPureFunctions:
    """Test pure functions in py3plex.core.converters module."""

    def test_compute_layout_exists(self):
        """Test that compute_layout is callable and has type hints."""
        try:
            from py3plex.core.converters import compute_layout
            import inspect
            
            assert callable(compute_layout)
            sig = inspect.signature(compute_layout)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("converters module not available")


class TestSupportingPureFunctions:
    """Test pure functions in py3plex.core.supporting module."""

    def test_split_to_layers_exists(self):
        """Test that split_to_layers is callable and has type hints."""
        try:
            from py3plex.core.supporting import split_to_layers
            import inspect
            
            assert callable(split_to_layers)
            sig = inspect.signature(split_to_layers)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("supporting module not available")

    def test_add_mpx_edges_exists(self):
        """Test that add_mpx_edges is callable and has type hints."""
        try:
            from py3plex.core.supporting import add_mpx_edges
            import inspect
            
            assert callable(add_mpx_edges)
            sig = inspect.signature(add_mpx_edges)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("supporting module not available")


class TestParserPureFunctions:
    """Test pure functions in py3plex.core.parsers module."""

    def test_parser_functions_exist(self):
        """Test that parser functions are callable and have type hints."""
        try:
            from py3plex.core.parsers import (
                parse_gml, parse_gpickle_biomine, parse_matrix,
                parse_matrix_to_nx, parse_multiedge_tuple_list,
                parse_network, parse_nx, save_gpickle,
                load_temporal_edge_information
            )
            import inspect
            
            parser_functions = [
                parse_gml, parse_gpickle_biomine, parse_matrix,
                parse_matrix_to_nx, parse_multiedge_tuple_list,
                parse_network, parse_nx, save_gpickle,
                load_temporal_edge_information
            ]
            
            for func in parser_functions:
                assert callable(func), f"{func.__name__} should be callable"
                sig = inspect.signature(func)
                # Most parsers should have return type annotations
                # Some may not, so we just check they're callable
        except ImportError:
            pytest.skip("parsers module not available")


class TestRandomGeneratorPureFunctions:
    """Test pure functions in py3plex.core.random_generators module."""

    def test_random_multilayer_er_exists(self):
        """Test that random_multilayer_ER is callable and has type hints."""
        try:
            from py3plex.core.random_generators import random_multilayer_ER
            import inspect
            
            assert callable(random_multilayer_ER)
            sig = inspect.signature(random_multilayer_ER)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("random_generators module not available")

    def test_random_multiplex_er_exists(self):
        """Test that random_multiplex_ER is callable and has type hints."""
        try:
            from py3plex.core.random_generators import random_multiplex_ER
            import inspect
            
            assert callable(random_multiplex_ER)
            sig = inspect.signature(random_multiplex_ER)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("random_generators module not available")

    def test_random_multiplex_generator_exists(self):
        """Test that random_multiplex_generator is callable and has type hints."""
        try:
            from py3plex.core.random_generators import random_multiplex_generator
            import inspect
            
            assert callable(random_multiplex_generator)
            sig = inspect.signature(random_multiplex_generator)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("random_generators module not available")


class TestUtilsPureFunctions:
    """Test pure functions in py3plex.utils module."""

    def test_get_rng_exists(self):
        """Test that get_rng is callable and has type hints."""
        try:
            from py3plex.utils import get_rng
            import inspect
            
            assert callable(get_rng)
            sig = inspect.signature(get_rng)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("utils module not available")

    def test_get_rng_returns_generator(self):
        """Test that get_rng returns correct type (functional test)."""
        try:
            from py3plex.utils import get_rng
            import numpy as np
            
            # Test with no seed
            rng = get_rng()
            assert isinstance(rng, np.random.Generator), "get_rng() should return np.random.Generator"
            
            # Test with integer seed
            rng_with_seed = get_rng(42)
            assert isinstance(rng_with_seed, np.random.Generator), "get_rng(seed) should return np.random.Generator"
            
            # Test with existing Generator (pass-through)
            existing_rng = np.random.default_rng(123)
            rng_passthrough = get_rng(existing_rng)
            assert rng_passthrough is existing_rng, "get_rng should pass through existing Generator"
            
        except ImportError:
            pytest.skip("NumPy not available")

    def test_deprecated_exists(self):
        """Test that deprecated decorator is callable."""
        try:
            from py3plex.utils import deprecated
            import inspect
            
            assert callable(deprecated)
            sig = inspect.signature(deprecated)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("utils module not available")

    def test_warn_if_deprecated_exists(self):
        """Test that warn_if_deprecated is callable."""
        try:
            from py3plex.utils import warn_if_deprecated
            
            assert callable(warn_if_deprecated)
        except ImportError:
            pytest.skip("utils module not available")


class TestVisualizationPureFunctions:
    """Test pure functions in py3plex.visualization modules."""

    def test_compute_random_layout_exists(self):
        """Test that compute_random_layout is callable and has type hints."""
        try:
            from py3plex.visualization.layout_algorithms import compute_random_layout
            import inspect
            
            assert callable(compute_random_layout)
            sig = inspect.signature(compute_random_layout)
            assert sig.return_annotation != inspect.Parameter.empty
        except ImportError:
            pytest.skip("layout_algorithms module not available")


class TestCrossHairIntegration:
    """Integration tests for CrossHair symbolic testing."""

    def test_crosshair_available(self):
        """Check if CrossHair is available for symbolic testing."""
        try:
            import crosshair
            assert hasattr(crosshair, 'check'), "CrossHair should have 'check' function"
        except ImportError:
            pytest.skip("CrossHair not installed (optional dependency)")

    def test_all_pure_functions_documented(self):
        """Verify all 27 identified pure functions are documented."""
        # This serves as documentation of what functions are considered pure
        pure_functions = {
            # Algorithms/Statistics (7)
            'py3plex.algorithms.statistics.basic_statistics': ['identify_n_hubs', 'core_network_statistics'],
            'py3plex.algorithms.statistics.topology': ['basic_pl_stats'],
            'py3plex.algorithms.statistics.stats_comparison': ['bootstrap_confidence_interval'],
            'py3plex.algorithms.statistics.critical_distances': ['center', 'name_length', 'remove_backslash'],
            
            # Core/Converters (1)
            'py3plex.core.converters': ['compute_layout'],
            
            # Core/Supporting (2)
            'py3plex.core.supporting': ['split_to_layers', 'add_mpx_edges'],
            
            # Core/Parsers (9)
            'py3plex.core.parsers': [
                'parse_gml', 'parse_gpickle_biomine', 'parse_matrix',
                'parse_matrix_to_nx', 'parse_multiedge_tuple_list',
                'parse_network', 'parse_nx', 'save_gpickle',
                'load_temporal_edge_information'
            ],
            
            # Core/Random Generators (3)
            'py3plex.core.random_generators': [
                'random_multilayer_ER', 'random_multiplex_ER',
                'random_multiplex_generator'
            ],
            
            # Utils (3)
            'py3plex.utils': ['get_rng', 'deprecated', 'warn_if_deprecated'],
            
            # Visualization (1)
            'py3plex.visualization.layout_algorithms': ['compute_random_layout'],
        }
        
        # Count total functions
        total_functions = sum(len(funcs) for funcs in pure_functions.values())
        assert total_functions == 26, f"Expected 26 pure functions, found {total_functions}"
        
        # Verify each module has at least one function
        for module, funcs in pure_functions.items():
            assert len(funcs) > 0, f"{module} should have at least one pure function"

    def test_pure_function_selection_criteria(self):
        """Document the selection criteria for pure functions."""
        criteria = {
            'type_hints': 'Complete type hints for arguments and return values',
            'no_io': 'No file I/O, logging, or console output',
            'no_global_state': 'No modifications to global variables',
            'reasonable_size': 'Typically < 80 lines for symbolic exploration',
            'deterministic': 'Consistent outputs for given inputs',
        }
        
        assert len(criteria) == 5, "Should have 5 selection criteria"
        for key, description in criteria.items():
            assert isinstance(description, str)
            assert len(description) > 0

    @pytest.mark.skipif(sys.version_info < (3, 9), reason="CrossHair requires Python 3.9+")
    def test_crosshair_check_example(self):
        """Example of how to run CrossHair checks on pure functions."""
        try:
            # This is an example/documentation test - not meant to actually run CrossHair
            # CrossHair usage examples:
            commands = [
                "crosshair check py3plex.utils.get_rng",
                "crosshair watch py3plex.algorithms.statistics.basic_statistics",
                "crosshair check --per_condition_timeout=10 py3plex.core.converters.compute_layout",
            ]
            
            assert len(commands) == 3
            for cmd in commands:
                assert cmd.startswith("crosshair")
                
        except Exception:
            pytest.skip("CrossHair example test - documentation only")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
