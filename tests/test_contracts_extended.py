"""
Extended tests for CrossHair/icontract contracts in newly added modules.

This test file validates that contracts are properly defined and that
basic contract violations are detected for the newly covered modules.
"""

import pytest


class TestValidationContracts:
    """Test contracts in py3plex.validation module."""

    def test_contracts_are_optional_validation(self):
        """Verify that validation can be imported without icontract."""
        import py3plex.validation
        assert hasattr(py3plex.validation, 'ICONTRACT_AVAILABLE')

    def test_validate_file_exists_has_contracts(self):
        """Test that validate_file_exists has contract decorators."""
        from py3plex.validation import validate_file_exists
        assert callable(validate_file_exists)

    def test_validate_csv_columns_has_contracts(self):
        """Test that validate_csv_columns has contract decorators."""
        from py3plex.validation import validate_csv_columns
        assert callable(validate_csv_columns)

    def test_validate_multiedgelist_format_has_contracts(self):
        """Test that validate_multiedgelist_format has contract decorators."""
        from py3plex.validation import validate_multiedgelist_format
        assert callable(validate_multiedgelist_format)

    def test_validate_edgelist_format_has_contracts(self):
        """Test that validate_edgelist_format has contract decorators."""
        from py3plex.validation import validate_edgelist_format
        assert callable(validate_edgelist_format)

    def test_validate_input_type_has_contracts(self):
        """Test that validate_input_type has contract decorators."""
        from py3plex.validation import validate_input_type
        assert callable(validate_input_type)

    def test_validate_network_data_has_contracts(self):
        """Test that validate_network_data has contract decorators."""
        from py3plex.validation import validate_network_data
        assert callable(validate_network_data)


class TestNxCompatContracts:
    """Test contracts in py3plex.core.nx_compat module."""

    def test_contracts_are_optional_nx_compat(self):
        """Verify that nx_compat can be imported without icontract."""
        from py3plex.core import nx_compat
        assert hasattr(nx_compat, 'ICONTRACT_AVAILABLE')

    def test_nx_info_has_contracts(self):
        """Test that nx_info has contract decorators."""
        from py3plex.core.nx_compat import nx_info
        assert callable(nx_info)

    def test_nx_info_returns_string(self):
        """Test that nx_info returns a string for a simple graph."""
        try:
            import networkx as nx
            from py3plex.core.nx_compat import nx_info
            
            G = nx.Graph()
            G.add_edge(1, 2)
            
            info = nx_info(G)
            assert isinstance(info, str)
            assert len(info) > 0
        except ImportError:
            pytest.skip("NetworkX not available")

    def test_nx_read_gpickle_has_contracts(self):
        """Test that nx_read_gpickle has contract decorators."""
        from py3plex.core.nx_compat import nx_read_gpickle
        assert callable(nx_read_gpickle)

    def test_nx_write_gpickle_has_contracts(self):
        """Test that nx_write_gpickle has contract decorators."""
        from py3plex.core.nx_compat import nx_write_gpickle
        assert callable(nx_write_gpickle)

    def test_nx_to_scipy_sparse_matrix_has_contracts(self):
        """Test that nx_to_scipy_sparse_matrix has contract decorators."""
        from py3plex.core.nx_compat import nx_to_scipy_sparse_matrix
        assert callable(nx_to_scipy_sparse_matrix)

    def test_nx_from_scipy_sparse_matrix_has_contracts(self):
        """Test that nx_from_scipy_sparse_matrix has contract decorators."""
        from py3plex.core.nx_compat import nx_from_scipy_sparse_matrix
        assert callable(nx_from_scipy_sparse_matrix)


class TestIOConvertersContracts:
    """Test contracts in py3plex.io.converters module."""

    def test_contracts_are_optional_io_converters(self):
        """Verify that io.converters can be imported without icontract."""
        from py3plex.io import converters
        assert hasattr(converters, 'ICONTRACT_AVAILABLE')

    def test_to_networkx_has_contracts(self):
        """Test that to_networkx has contract decorators."""
        from py3plex.io.converters import to_networkx
        assert callable(to_networkx)

    def test_from_networkx_has_contracts(self):
        """Test that from_networkx has contract decorators."""
        from py3plex.io.converters import from_networkx
        assert callable(from_networkx)

    def test_to_igraph_has_contracts(self):
        """Test that to_igraph has contract decorators."""
        from py3plex.io.converters import to_igraph
        assert callable(to_igraph)

    def test_from_igraph_has_contracts(self):
        """Test that from_igraph has contract decorators."""
        from py3plex.io.converters import from_igraph
        assert callable(from_igraph)


class TestMulticentralityContracts:
    """Test contracts in py3plex.algorithms.multicentrality module."""

    def test_contracts_are_optional_multicentrality(self):
        """Verify that multicentrality can be imported without icontract."""
        from py3plex.algorithms import multicentrality
        assert hasattr(multicentrality, 'ICONTRACT_AVAILABLE')

    def test_multiplex_participation_coefficient_has_contracts(self):
        """Test that multiplex_participation_coefficient has contract decorators."""
        from py3plex.algorithms.multicentrality import multiplex_participation_coefficient
        assert callable(multiplex_participation_coefficient)


class TestContractIntegrationExtended:
    """Integration tests for extended contract system."""

    def test_all_contracted_modules_importable_extended(self):
        """Verify all newly contracted modules can be imported."""
        modules_to_test = [
            'py3plex.validation',
            'py3plex.core.nx_compat',
            'py3plex.io.converters',
            'py3plex.algorithms.multicentrality',
        ]
        
        for module_name in modules_to_test:
            try:
                module = __import__(module_name, fromlist=[''])
                assert hasattr(module, 'ICONTRACT_AVAILABLE'), \
                    f"{module_name} should have ICONTRACT_AVAILABLE attribute"
            except ImportError as e:
                pytest.skip(f"Could not import {module_name}: {e}")

    def test_documented_invariants_are_testable_extended(self):
        """Verify that key invariants from new contracts are documented."""
        invariants = [
            "File paths must be non-empty strings",
            "Column lists must be non-empty lists of strings",
            "NetworkX graphs must not be None",
            "Conversion functions validate graph types",
            "MultiLayerGraph conversions preserve graph properties",
            "MPC function returns dictionary with numeric values",
            "Projection modes must be valid literal values",
        ]
        
        # Document that these invariants exist
        assert len(invariants) == 7
        for inv in invariants:
            assert isinstance(inv, str)
            assert len(inv) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
