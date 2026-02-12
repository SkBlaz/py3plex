"""
Tests for py3plex.algebra.backend module.

Tests the backend configuration and selection for algebra operations.
"""

import pytest
from py3plex.algebra.backend import (
    GraphBackend,
    MatrixBackend,
    get_backend,
    list_backends,
)
from py3plex.exceptions import Py3plexException


class TestGraphBackend:
    """Test the GraphBackend class."""

    def test_graph_backend_name(self):
        """Test GraphBackend has correct name."""
        assert GraphBackend.name == "graph"

    def test_graph_backend_has_sssp(self):
        """Test GraphBackend has sssp method."""
        assert hasattr(GraphBackend, "sssp")
        assert callable(GraphBackend.sssp)

    def test_graph_backend_has_closure(self):
        """Test GraphBackend has closure method."""
        assert hasattr(GraphBackend, "closure")
        assert callable(GraphBackend.closure)


class TestMatrixBackend:
    """Test the MatrixBackend class."""

    def test_matrix_backend_name(self):
        """Test MatrixBackend has correct name."""
        assert MatrixBackend.name == "matrix"

    def test_matrix_backend_has_sssp(self):
        """Test MatrixBackend has sssp method."""
        assert hasattr(MatrixBackend, "sssp")
        assert callable(MatrixBackend.sssp)

    def test_matrix_backend_has_closure(self):
        """Test MatrixBackend has closure method."""
        assert hasattr(MatrixBackend, "closure")
        assert callable(MatrixBackend.closure)

    def test_matrix_backend_sssp_not_implemented(self):
        """Test MatrixBackend sssp raises NotImplementedError."""
        with pytest.raises(Py3plexException, match="not yet implemented"):
            MatrixBackend.sssp()

    def test_matrix_backend_closure_not_implemented(self):
        """Test MatrixBackend closure raises NotImplementedError."""
        with pytest.raises(Py3plexException, match="not yet implemented"):
            MatrixBackend.closure()


class TestBackendManagement:
    """Test backend retrieval and listing."""

    def test_get_graph_backend(self):
        """Test retrieving graph backend."""
        backend = get_backend("graph")
        assert backend == GraphBackend

    def test_get_matrix_backend(self):
        """Test retrieving matrix backend."""
        backend = get_backend("matrix")
        assert backend == MatrixBackend

    def test_get_invalid_backend(self):
        """Test that invalid backend name raises exception."""
        with pytest.raises(Py3plexException, match="Unknown backend"):
            get_backend("invalid_backend")

    def test_list_backends(self):
        """Test listing available backends."""
        backends = list_backends()
        assert isinstance(backends, list)
        assert "graph" in backends
        assert "matrix" in backends
        # Should be sorted
        assert backends == sorted(backends)

    def test_list_backends_deterministic(self):
        """Test that list_backends returns consistent order."""
        backends1 = list_backends()
        backends2 = list_backends()
        assert backends1 == backends2

    def test_get_backend_returns_class(self):
        """Test that get_backend returns a class."""
        backend = get_backend("graph")
        assert hasattr(backend, "sssp")
        assert hasattr(backend, "closure")

    def test_backend_count(self):
        """Test expected number of backends."""
        backends = list_backends()
        assert len(backends) == 2  # graph and matrix
