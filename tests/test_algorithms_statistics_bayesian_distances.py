"""Tests for py3plex.algorithms.statistics.bayesian_distances module.

Tests the generate_bayesian_diagram function for Bayesian comparison.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from py3plex.algorithms.statistics.bayesian_distances import generate_bayesian_diagram


class TestGenerateBayesianDiagram:
    """Test generate_bayesian_diagram function."""
    
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plt')
    def test_basic_comparison(self, mock_plt, mock_plot, mock_mc, mock_hier):
        """Test basic Bayesian diagram generation."""
        # Setup mock returns
        mock_hier.return_value = (0.1, 0.7, 0.2)  # pl, pe, pr
        mock_mc.return_value = np.array([0.5, 0.6, 0.7])  # samples
        
        # Create sample data
        result_matrices = np.random.rand(10, 2)  # 10 folds, 2 algorithms
        
        # Run function
        pl, pe, pr = generate_bayesian_diagram(
            result_matrices=result_matrices,
            show_diagram=False
        )
        
        # Verify return values
        assert pl == 0.1
        assert pe == 0.7
        assert pr == 0.2
        
        # Verify hierarchical was called
        mock_hier.assert_called_once()
        
        # Verify MC sampling was called
        mock_mc.assert_called_once()
        
        # Verify plot was called
        mock_plot.assert_called_once()
        
        # Verify show was not called
        mock_plt.show.assert_not_called()
    
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plt')
    def test_with_custom_algo_names(self, mock_plt, mock_plot, mock_mc, mock_hier):
        """Test with custom algorithm names."""
        mock_hier.return_value = (0.3, 0.5, 0.2)
        mock_mc.return_value = np.array([0.1, 0.2, 0.3])
        
        result_matrices = np.random.rand(5, 2)
        algo_names = ["SVM", "RandomForest"]
        
        pl, pe, pr = generate_bayesian_diagram(
            result_matrices=result_matrices,
            algo_names=algo_names,
            show_diagram=False
        )
        
        # Verify algo names were passed
        call_args = mock_hier.call_args
        assert call_args[1]['names'] == algo_names
    
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plt')
    def test_with_custom_rope(self, mock_plt, mock_plot, mock_mc, mock_hier):
        """Test with custom ROPE parameter."""
        mock_hier.return_value = (0.2, 0.6, 0.2)
        mock_mc.return_value = np.array([0.4, 0.5, 0.6])
        
        result_matrices = np.random.rand(8, 2)
        custom_rope = 0.05
        
        pl, pe, pr = generate_bayesian_diagram(
            result_matrices=result_matrices,
            rope=custom_rope,
            show_diagram=False
        )
        
        # Verify rope was passed
        call_args = mock_hier.call_args
        assert call_args[0][1] == custom_rope
    
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plt')
    def test_with_custom_rho(self, mock_plt, mock_plot, mock_mc, mock_hier):
        """Test with custom rho correlation parameter."""
        mock_hier.return_value = (0.15, 0.7, 0.15)
        mock_mc.return_value = np.array([0.3, 0.4, 0.5])
        
        result_matrices = np.random.rand(10, 2)
        custom_rho = 0.3
        
        pl, pe, pr = generate_bayesian_diagram(
            result_matrices=result_matrices,
            rho=custom_rho,
            show_diagram=False
        )
        
        # Verify rho was passed
        call_args = mock_hier.call_args
        assert call_args[0][2] == custom_rho
    
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plt')
    def test_show_diagram(self, mock_plt, mock_plot, mock_mc, mock_hier):
        """Test with show_diagram=True."""
        mock_hier.return_value = (0.1, 0.8, 0.1)
        mock_mc.return_value = np.array([0.5])
        
        result_matrices = np.random.rand(5, 2)
        
        pl, pe, pr = generate_bayesian_diagram(
            result_matrices=result_matrices,
            show_diagram=True
        )
        
        # Verify show was called
        mock_plt.show.assert_called_once()
    
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plt')
    def test_save_diagram(self, mock_plt, mock_plot, mock_mc, mock_hier):
        """Test saving diagram to file."""
        mock_hier.return_value = (0.25, 0.5, 0.25)
        mock_mc.return_value = np.array([0.6])
        
        result_matrices = np.random.rand(7, 2)
        save_path = "/tmp/bayesian_test.png"
        
        pl, pe, pr = generate_bayesian_diagram(
            result_matrices=result_matrices,
            save_diagram=save_path,
            show_diagram=False
        )
        
        # Verify savefig was called
        mock_plt.savefig.assert_called_once_with(save_path)
    
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plt')
    def test_default_algo_names(self, mock_plt, mock_plot, mock_mc, mock_hier):
        """Test default algorithm names are used when not provided."""
        mock_hier.return_value = (0.2, 0.6, 0.2)
        mock_mc.return_value = np.array([0.5])
        
        result_matrices = np.random.rand(6, 2)
        
        pl, pe, pr = generate_bayesian_diagram(
            result_matrices=result_matrices,
            algo_names=None,  # Explicit None
            show_diagram=False
        )
        
        # Verify default names were used
        call_args = mock_hier.call_args
        assert call_args[1]['names'] == ["algo1", "algo2"]
    
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plt')
    def test_return_values_tuple(self, mock_plt, mock_plot, mock_mc, mock_hier):
        """Test that function returns a proper tuple."""
        mock_hier.return_value = (0.33, 0.34, 0.33)
        mock_mc.return_value = np.array([0.5])
        
        result_matrices = np.random.rand(4, 2)
        
        result = generate_bayesian_diagram(
            result_matrices=result_matrices,
            show_diagram=False
        )
        
        # Should be a tuple of 3 floats
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(isinstance(x, float) for x in result)
    
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plt')
    def test_probability_sum(self, mock_plt, mock_plot, mock_mc, mock_hier):
        """Test that probabilities should sum to approximately 1."""
        mock_hier.return_value = (0.1, 0.7, 0.2)
        mock_mc.return_value = np.array([0.5])
        
        result_matrices = np.random.rand(10, 2)
        
        pl, pe, pr = generate_bayesian_diagram(
            result_matrices=result_matrices,
            show_diagram=False
        )
        
        # Probabilities should sum to approximately 1
        total = pl + pe + pr
        assert abs(total - 1.0) < 0.01
    
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plt')
    def test_plot_posterior_receives_rounded_values(self, mock_plt, mock_plot, mock_mc, mock_hier):
        """Test that plot_posterior receives rounded probability values."""
        mock_hier.return_value = (0.123456, 0.654321, 0.222223)
        mock_mc.return_value = np.array([0.5])
        
        result_matrices = np.random.rand(5, 2)
        algo_names = ["A", "B"]
        
        pl, pe, pr = generate_bayesian_diagram(
            result_matrices=result_matrices,
            algo_names=algo_names,
            show_diagram=False
        )
        
        # Verify plot_posterior was called with rounded values
        call_args = mock_plot.call_args
        proba_triplet = call_args[1]['proba_triplet']
        
        # First and third should be rounded
        assert abs(proba_triplet[0] - 0.12) < 0.01
        assert proba_triplet[1] == 0.654321  # Middle not rounded
        assert abs(proba_triplet[2] - 0.22) < 0.01
