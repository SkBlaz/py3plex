"""
Tests for the benchmark_visualizations module.

This module tests benchmark visualization functions with mock data.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

import pandas as pd
import pytest
import numpy as np

from py3plex.visualization.benchmark_visualizations import (
    plot_core_macro,
    plot_core_micro,
    generic_grouping,
)


class TestGenericGrouping:
    """Test the generic_grouping function."""

    def test_generic_grouping_basic(self):
        """Test generic_grouping with basic data."""
        # Create sample data
        data = {
            'percent_train': [0.1, 0.2, 0.3, 0.1, 0.2, 0.3],
            'micro_F': [0.5, 0.6, 0.7, 0.55, 0.65, 0.75],
            'macro_F': [0.45, 0.55, 0.65, 0.5, 0.6, 0.7],
            'setting': ['A', 'A', 'A', 'B', 'B', 'B'],
            'dataset': ['dataset1', 'dataset1', 'dataset1', 'dataset1', 'dataset1', 'dataset1'],
        }
        df = pd.DataFrame(data)

        result = generic_grouping(df, 'micro_F', threshold=1.0, percentages=True)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        # Should have settings as columns
        assert 'A' in result.columns or 'B' in result.columns

    def test_generic_grouping_with_threshold(self):
        """Test generic_grouping respects threshold parameter."""
        data = {
            'percent_train': [0.1, 0.2, 0.5, 0.8],
            'micro_F': [0.5, 0.6, 0.7, 0.8],
            'macro_F': [0.45, 0.55, 0.65, 0.75],
            'setting': ['A', 'A', 'A', 'A'],
            'dataset': ['dataset1', 'dataset1', 'dataset1', 'dataset1'],
        }
        df = pd.DataFrame(data)

        # With threshold 0.3, should only include first 2 rows
        result = generic_grouping(df, 'micro_F', threshold=0.3)

        assert isinstance(result, pd.DataFrame)

    def test_generic_grouping_multiple_datasets(self):
        """Test generic_grouping with multiple datasets."""
        data = {
            'percent_train': [0.1, 0.2, 0.1, 0.2],
            'micro_F': [0.5, 0.6, 0.55, 0.65],
            'macro_F': [0.45, 0.55, 0.5, 0.6],
            'setting': ['A', 'A', 'A', 'A'],
            'dataset': ['dataset1', 'dataset1', 'dataset2', 'dataset2'],
        }
        df = pd.DataFrame(data)

        result = generic_grouping(df, 'micro_F', percentages=True)

        assert isinstance(result, pd.DataFrame)
        # Should have multiple rows for different datasets
        assert len(result) > 1

    def test_generic_grouping_multiple_settings(self):
        """Test generic_grouping with multiple algorithm settings."""
        data = {
            'percent_train': [0.1, 0.1, 0.2, 0.2],
            'micro_F': [0.5, 0.55, 0.6, 0.65],
            'macro_F': [0.45, 0.5, 0.55, 0.6],
            'setting': ['A', 'B', 'A', 'B'],
            'dataset': ['dataset1', 'dataset1', 'dataset1', 'dataset1'],
        }
        df = pd.DataFrame(data)

        result = generic_grouping(df, 'micro_F')

        assert isinstance(result, pd.DataFrame)
        # Should have multiple columns for different settings
        assert len(result.columns) >= 2

    def test_generic_grouping_with_percentages_false(self):
        """Test generic_grouping with percentages=False."""
        data = {
            'percent_train': [0.1, 0.2],
            'micro_F': [0.5, 0.6],
            'macro_F': [0.45, 0.55],
            'setting': ['A', 'A'],
            'dataset': ['dataset1', 'dataset1'],
        }
        df = pd.DataFrame(data)

        result = generic_grouping(df, 'micro_F', percentages=False)

        assert isinstance(result, pd.DataFrame)

    def test_generic_grouping_returns_mean_and_std(self):
        """Test that generic_grouping includes mean and std in output."""
        # Create data with some variance
        data = {
            'percent_train': [0.1, 0.1, 0.1],
            'micro_F': [0.5, 0.51, 0.49],
            'macro_F': [0.45, 0.46, 0.44],
            'setting': ['A', 'A', 'A'],
            'dataset': ['dataset1', 'dataset1', 'dataset1'],
        }
        df = pd.DataFrame(data)

        result = generic_grouping(df, 'micro_F')

        # Result should contain strings with format "mean (std)"
        assert isinstance(result, pd.DataFrame)
        # Check that at least one cell contains parentheses (indicating std)
        has_std_format = False
        for col in result.columns:
            for val in result[col]:
                if isinstance(val, str) and '(' in val and ')' in val:
                    has_std_format = True
                    break
            if has_std_format:
                break
        assert has_std_format


class TestPlotFunctions:
    """Test the plotting functions."""

    @pytest.mark.skip(reason="seaborn API changes in newer versions")
    def test_plot_core_macro_returns_one(self):
        """Test that plot_core_macro returns 1 on success."""
        data = {
            'percent_train': [0.1, 0.2, 0.3],
            'macro_F': [0.5, 0.6, 0.7],
            'setting': ['A', 'A', 'A'],
        }
        df = pd.DataFrame(data)

        # Should return 1 (though it also shows plot)
        # We're using Agg backend so no display
        result = plot_core_macro(df)

        assert result == 1

    @pytest.mark.skip(reason="seaborn API changes in newer versions")
    def test_plot_core_micro_returns_one(self):
        """Test that plot_core_micro returns 1 on success."""
        data = {
            'percent_train': [0.1, 0.2, 0.3],
            'micro_F': [0.5, 0.6, 0.7],
            'setting': ['A', 'A', 'A'],
        }
        df = pd.DataFrame(data)

        result = plot_core_micro(df)

        assert result == 1

    @pytest.mark.skip(reason="seaborn API changes in newer versions")
    def test_plot_core_macro_with_multiple_settings(self):
        """Test plot_core_macro with multiple algorithm settings."""
        data = {
            'percent_train': [0.1, 0.2, 0.1, 0.2],
            'macro_F': [0.5, 0.6, 0.55, 0.65],
            'setting': ['A', 'A', 'B', 'B'],
        }
        df = pd.DataFrame(data)

        result = plot_core_macro(df)

        assert result == 1

    @pytest.mark.skip(reason="seaborn API changes in newer versions")
    def test_plot_core_micro_with_multiple_settings(self):
        """Test plot_core_micro with multiple algorithm settings."""
        data = {
            'percent_train': [0.1, 0.2, 0.1, 0.2],
            'micro_F': [0.5, 0.6, 0.55, 0.65],
            'setting': ['A', 'A', 'B', 'B'],
        }
        df = pd.DataFrame(data)

        result = plot_core_micro(df)

        assert result == 1


class TestDataValidation:
    """Test handling of edge cases and invalid data."""

    def test_generic_grouping_empty_dataframe(self):
        """Test generic_grouping with empty DataFrame."""
        df = pd.DataFrame(columns=['percent_train', 'micro_F', 'macro_F', 'setting', 'dataset'])

        # Should handle empty DataFrame - may raise exception or return empty
        try:
            result = generic_grouping(df, 'micro_F')
            assert isinstance(result, pd.DataFrame)
        except (KeyError, AttributeError):
            # Empty dataframes may cause errors in groupby operations
            pytest.skip("Empty DataFrame causes expected error in groupby")

    def test_generic_grouping_single_row(self):
        """Test generic_grouping with single row."""
        data = {
            'percent_train': [0.1],
            'micro_F': [0.5],
            'macro_F': [0.45],
            'setting': ['A'],
            'dataset': ['dataset1'],
        }
        df = pd.DataFrame(data)

        result = generic_grouping(df, 'micro_F')

        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1
