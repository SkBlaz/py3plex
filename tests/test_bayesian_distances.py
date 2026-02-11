"""
Tests for py3plex.algorithms.statistics.bayesian_distances module.

This module tests the Bayesian comparison diagram generation.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestGenerateBayesianDiagram:
    """Test generate_bayesian_diagram function."""

    def test_import_module(self):
        """Test that the module can be imported."""
        from py3plex.algorithms.statistics import bayesian_distances
        assert hasattr(bayesian_distances, 'generate_bayesian_diagram')

    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('matplotlib.pyplot.show')
    def test_basic_call_with_mocks(self, mock_show, mock_plot, mock_mc, mock_hier):
        """Test basic function call with mocked dependencies."""
        from py3plex.algorithms.statistics.bayesian_distances import (
            generate_bayesian_diagram
        )
        
        # Setup mock returns
        mock_hier.return_value = (0.1, 0.8, 0.1)
        mock_mc.return_value = np.array([0.0, 0.0, 0.0])
        
        # Create fake result matrices
        result_matrices = np.random.rand(2, 10, 10)
        
        # Call function
        pl, pe, pr = generate_bayesian_diagram(
            result_matrices,
            algo_names=['algo1', 'algo2'],
            rope=0.01,
            rho=0.2,
            show_diagram=False
        )
        
        # Check return values
        assert pl == 0.1
        assert pe == 0.8
        assert pr == 0.1
        
        # Check that dependencies were called
        assert mock_hier.called
        assert mock_mc.called
        assert mock_plot.called
        assert not mock_show.called  # show_diagram=False

    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('matplotlib.pyplot.show')
    def test_show_diagram_true(self, mock_show, mock_plot, mock_mc, mock_hier):
        """Test that plt.show() is called when show_diagram=True."""
        from py3plex.algorithms.statistics.bayesian_distances import (
            generate_bayesian_diagram
        )
        
        mock_hier.return_value = (0.2, 0.6, 0.2)
        mock_mc.return_value = np.array([0.0])
        
        result_matrices = np.random.rand(2, 5, 5)
        
        generate_bayesian_diagram(
            result_matrices,
            show_diagram=True
        )
        
        assert mock_show.called

    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    @patch('matplotlib.pyplot.savefig')
    def test_save_diagram(self, mock_savefig, mock_plot, mock_mc, mock_hier):
        """Test that diagram is saved when save_diagram path provided."""
        from py3plex.algorithms.statistics.bayesian_distances import (
            generate_bayesian_diagram
        )
        
        mock_hier.return_value = (0.3, 0.4, 0.3)
        mock_mc.return_value = np.array([0.0])
        
        result_matrices = np.random.rand(2, 5, 5)
        save_path = '/tmp/test_diagram.png'
        
        generate_bayesian_diagram(
            result_matrices,
            show_diagram=False,
            save_diagram=save_path
        )
        
        mock_savefig.assert_called_once_with(save_path)

    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    def test_default_algo_names(self, mock_plot, mock_mc, mock_hier):
        """Test that default algo names are used when none provided."""
        from py3plex.algorithms.statistics.bayesian_distances import (
            generate_bayesian_diagram
        )
        
        mock_hier.return_value = (0.3, 0.4, 0.3)
        mock_mc.return_value = np.array([0.0])
        
        result_matrices = np.random.rand(2, 5, 5)
        
        # Call without algo_names
        generate_bayesian_diagram(
            result_matrices,
            show_diagram=False
        )
        
        # Check that hierarchical was called with default names
        call_args = mock_hier.call_args
        assert 'names' in call_args[1]
        assert call_args[1]['names'] == ['algo1', 'algo2']

    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    def test_custom_rope_and_rho(self, mock_plot, mock_mc, mock_hier):
        """Test that custom rope and rho parameters are passed through."""
        from py3plex.algorithms.statistics.bayesian_distances import (
            generate_bayesian_diagram
        )
        
        mock_hier.return_value = (0.2, 0.6, 0.2)
        mock_mc.return_value = np.array([0.0])
        
        result_matrices = np.random.rand(2, 5, 5)
        custom_rope = 0.05
        custom_rho = 0.1
        
        generate_bayesian_diagram(
            result_matrices,
            rope=custom_rope,
            rho=custom_rho,
            show_diagram=False
        )
        
        # Check that hierarchical received custom parameters
        call_args = mock_hier.call_args
        assert call_args[0][1] == custom_rope  # rope
        assert call_args[0][2] == custom_rho   # rho

    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical')
    @patch('py3plex.algorithms.statistics.bayesian_distances.hierarchical_MC')
    @patch('py3plex.algorithms.statistics.bayesian_distances.plot_posterior')
    def test_returns_tuple_of_three_floats(self, mock_plot, mock_mc, mock_hier):
        """Test that function returns a tuple of three values."""
        from py3plex.algorithms.statistics.bayesian_distances import (
            generate_bayesian_diagram
        )
        
        mock_hier.return_value = (0.15, 0.70, 0.15)
        mock_mc.return_value = np.array([0.0])
        
        result_matrices = np.random.rand(2, 5, 5)
        
        result = generate_bayesian_diagram(
            result_matrices,
            show_diagram=False
        )
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        pl, pe, pr = result
        # Values should sum to approximately 1
        assert abs(pl + pe + pr - 1.0) < 0.01
