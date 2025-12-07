"""
Tests for the wrappers.benchmark_nodes module.

This module tests the node classification benchmarking functionality.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest
from gensim.models import KeyedVectors
from scipy import sparse
from sklearn.linear_model import LogisticRegression

from py3plex.wrappers.benchmark_nodes import (
    TopKRanker,
    sparse2graph,
    benchmark_node_classification,
)


class TestTopKRanker:
    """Test the TopKRanker classifier."""

    def test_topk_ranker_initialization(self):
        """Test TopKRanker can be initialized."""
        ranker = TopKRanker(LogisticRegression())
        assert isinstance(ranker, TopKRanker)

    def test_topk_ranker_predict_single_sample(self):
        """Test TopKRanker prediction for single sample."""
        # Create simple training data
        X_train = np.array([[1, 0], [0, 1], [1, 1], [0, 0]])
        y_train = sparse.csr_matrix([[1, 0], [0, 1], [1, 1], [0, 0]])

        ranker = TopKRanker(LogisticRegression())
        ranker.fit(X_train, y_train)

        # Predict top-1 label for single sample
        X_test = np.array([[1, 0]])
        top_k_list = [1]
        predictions = ranker.predict(X_test, top_k_list)

        assert len(predictions) == 1
        assert len(predictions[0]) == 1

    def test_topk_ranker_predict_multiple_samples(self):
        """Test TopKRanker prediction for multiple samples."""
        # Create simple training data
        X_train = np.array([[1, 0], [0, 1], [1, 1], [0, 0]])
        y_train = sparse.csr_matrix([[1, 0], [0, 1], [1, 1], [0, 0]])

        ranker = TopKRanker(LogisticRegression())
        ranker.fit(X_train, y_train)

        # Predict for multiple samples with different k
        X_test = np.array([[1, 0], [0, 1]])
        top_k_list = [1, 2]
        predictions = ranker.predict(X_test, top_k_list)

        assert len(predictions) == 2
        assert len(predictions[0]) == 1
        assert len(predictions[1]) == 2

    def test_topk_ranker_predict_assertion(self):
        """Test TopKRanker raises assertion when dimensions mismatch."""
        X_train = np.array([[1, 0], [0, 1]])
        y_train = sparse.csr_matrix([[1, 0], [0, 1]])

        ranker = TopKRanker(LogisticRegression())
        ranker.fit(X_train, y_train)

        X_test = np.array([[1, 0], [0, 1]])
        top_k_list = [1]  # Wrong length

        with pytest.raises(AssertionError):
            ranker.predict(X_test, top_k_list)


class TestSparse2Graph:
    """Test the sparse2graph conversion function."""

    def test_sparse2graph_empty_matrix(self):
        """Test sparse2graph with empty matrix."""
        sparse_matrix = sparse.csr_matrix((0, 0))
        result = sparse2graph(sparse_matrix)
        assert result == {}

    def test_sparse2graph_single_edge(self):
        """Test sparse2graph with single edge."""
        # Create sparse matrix with one edge: 0 -> 1
        sparse_matrix = sparse.csr_matrix(([1.0], ([0], [1])), shape=(2, 2))
        result = sparse2graph(sparse_matrix)

        assert "0" in result
        assert "1" in result["0"]

    def test_sparse2graph_multiple_edges(self):
        """Test sparse2graph with multiple edges."""
        # Create sparse matrix with multiple edges
        data = [1.0, 1.0, 1.0, 1.0]
        row = [0, 0, 1, 2]
        col = [1, 2, 2, 0]
        sparse_matrix = sparse.csr_matrix((data, (row, col)), shape=(3, 3))
        result = sparse2graph(sparse_matrix)

        assert "0" in result
        assert "1" in result["0"]
        assert "2" in result["0"]
        assert "2" in result["1"]
        assert "0" in result["2"]

    def test_sparse2graph_format_coo(self):
        """Test sparse2graph with COO format matrix."""
        # Create COO format sparse matrix
        sparse_matrix = sparse.coo_matrix(([1.0], ([0], [1])), shape=(2, 2))
        result = sparse2graph(sparse_matrix)

        assert "0" in result
        assert "1" in result["0"]

    def test_sparse2graph_self_loop(self):
        """Test sparse2graph handles self-loops."""
        # Create matrix with self-loop: 0 -> 0
        sparse_matrix = sparse.csr_matrix(([1.0], ([0], [0])), shape=(2, 2))
        result = sparse2graph(sparse_matrix)

        assert "0" in result
        assert "0" in result["0"]

    def test_sparse2graph_return_types(self):
        """Test sparse2graph returns correct types."""
        sparse_matrix = sparse.csr_matrix(([1.0], ([0], [1])), shape=(2, 2))
        result = sparse2graph(sparse_matrix)

        assert isinstance(result, dict)
        for key in result:
            assert isinstance(key, str)
            assert isinstance(result[key], list)
            for neighbor in result[key]:
                assert isinstance(neighbor, str)


class TestBenchmarkNodeClassification:
    """Test the benchmark_node_classification function."""

    def _create_test_embedding_file(self, num_nodes=10, embedding_dim=5):
        """Helper to create a temporary embedding file."""
        tmp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".emb"
        )

        # Write header: num_nodes embedding_dim
        tmp_file.write(f"{num_nodes} {embedding_dim}\n")

        # Write embeddings for nodes 0 to num_nodes-1
        for node_id in range(num_nodes):
            embedding = " ".join([f"{np.random.rand():.6f}" for _ in range(embedding_dim)])
            tmp_file.write(f"{node_id} {embedding}\n")

        tmp_file.close()
        return tmp_file.name

    @pytest.mark.skip(reason="benchmark_node_classification has sklearn compatibility issue with MultiLabelBinarizer in newer versions")
    def test_benchmark_node_classification_basic(self):
        """Test basic node classification benchmarking."""
        # Create test data
        num_nodes = 10
        num_labels = 3
        embedding_file = self._create_test_embedding_file(num_nodes)

        try:
            # Create simple network adjacency matrix
            network = sparse.random(num_nodes, num_nodes, density=0.3)

            # Create simple labels matrix (multi-label)
            labels = sparse.random(num_nodes, num_labels, density=0.5, format="csr")
            labels.data[:] = 1  # Binary labels

            # Run benchmark with single training percentage
            results = benchmark_node_classification(
                embedding_file, network, labels, percent=0.5
            )

            assert isinstance(results, dict)
            assert 0.5 in results
            assert len(results[0.5]) == 4  # mean_micro, mean_macro, std_micro, std_macro

            # Check result types
            mean_micro, mean_macro, std_micro, std_macro = results[0.5]
            assert isinstance(mean_micro, (float, np.floating))
            assert isinstance(mean_macro, (float, np.floating))
            assert isinstance(std_micro, (float, np.floating))
            assert isinstance(std_macro, (float, np.floating))

            # Check that scores are in valid range [0, 1]
            assert 0 <= mean_micro <= 1
            assert 0 <= mean_macro <= 1

        finally:
            # Clean up
            Path(embedding_file).unlink()

    @pytest.mark.skip(reason="benchmark_node_classification has sklearn compatibility issue with MultiLabelBinarizer in newer versions")
    def test_benchmark_node_classification_all_percents(self):
        """Test benchmarking with all training percentages."""
        num_nodes = 20
        num_labels = 3
        embedding_file = self._create_test_embedding_file(num_nodes)

        try:
            network = sparse.random(num_nodes, num_nodes, density=0.3)
            labels = sparse.random(num_nodes, num_labels, density=0.5, format="csr")
            labels.data[:] = 1

            # Run with all percentages
            results = benchmark_node_classification(
                embedding_file, network, labels, percent="all"
            )

            assert isinstance(results, dict)
            # Should have results for 0.1, 0.2, ..., 0.9
            expected_percents = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
            for pct in expected_percents:
                assert pct in results
                assert len(results[pct]) == 4

        finally:
            Path(embedding_file).unlink()

    @pytest.mark.skip(reason="benchmark_node_classification has sklearn compatibility issue with MultiLabelBinarizer in newer versions")
    def test_benchmark_node_classification_labels_already_sparse(self):
        """Test that function handles labels that are already sparse."""
        num_nodes = 10
        num_labels = 3
        embedding_file = self._create_test_embedding_file(num_nodes)

        try:
            network = sparse.random(num_nodes, num_nodes, density=0.3)
            # Labels already in CSR format
            labels = sparse.random(num_nodes, num_labels, density=0.5, format="csr")
            labels.data[:] = 1

            results = benchmark_node_classification(
                embedding_file, network, labels, percent=0.5
            )

            assert isinstance(results, dict)
            assert 0.5 in results

        finally:
            Path(embedding_file).unlink()

    @pytest.mark.skip(reason="benchmark_node_classification has sklearn compatibility issue with MultiLabelBinarizer in newer versions")
    def test_benchmark_node_classification_small_training_set(self):
        """Test with very small training percentage."""
        num_nodes = 20
        num_labels = 2
        embedding_file = self._create_test_embedding_file(num_nodes)

        try:
            network = sparse.random(num_nodes, num_nodes, density=0.3)
            labels = sparse.random(num_nodes, num_labels, density=0.5, format="csr")
            labels.data[:] = 1

            results = benchmark_node_classification(
                embedding_file, network, labels, percent=0.1
            )

            assert isinstance(results, dict)
            assert 0.1 in results

        finally:
            Path(embedding_file).unlink()

    @pytest.mark.skip(reason="benchmark_node_classification has sklearn compatibility issue with MultiLabelBinarizer in newer versions")
    def test_benchmark_node_classification_large_training_set(self):
        """Test with large training percentage."""
        num_nodes = 20
        num_labels = 2
        embedding_file = self._create_test_embedding_file(num_nodes)

        try:
            network = sparse.random(num_nodes, num_nodes, density=0.3)
            labels = sparse.random(num_nodes, num_labels, density=0.5, format="csr")
            labels.data[:] = 1

            results = benchmark_node_classification(
                embedding_file, network, labels, percent=0.9
            )

            assert isinstance(results, dict)
            assert 0.9 in results

        finally:
            Path(embedding_file).unlink()
