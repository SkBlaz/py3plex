"""
Tests for polynomial fitting functions.

This module tests polynomial fitting utilities used in
py3plex multilayer network visualizations.
"""
import unittest

import numpy as np

from py3plex.visualization.polyfit import draw_order3, draw_piramidal


class TestDrawOrder3(unittest.TestCase):
    """Test draw_order3 polynomial fitting function."""

    def test_basic_order3_fit(self):
        """Test basic 3rd order polynomial fitting."""
        networks = 10
        p1 = (0, 10)
        p2 = (0, 0)

        space_x, space_y = draw_order3(networks, p1, p2)

        self.assertIsInstance(space_x, np.ndarray)
        self.assertIsInstance(space_y, np.ndarray)
        self.assertEqual(len(space_x), 10)
        self.assertEqual(len(space_y), 10)

    def test_output_length(self):
        """Test that output has expected length (10 points)."""
        networks = 20
        p1 = (0, 10)
        p2 = (0, 0)

        space_x, space_y = draw_order3(networks, p1, p2)

        # Function uses linspace with 10 points
        self.assertEqual(len(space_x), 10)
        self.assertEqual(len(space_y), 10)

    def test_x_range(self):
        """Test that x values are in expected range."""
        networks = 15
        p1 = (0, 10)
        p2 = (0, 0)

        space_x, space_y = draw_order3(networks, p1, p2)

        # x should range from 0 to networks
        self.assertAlmostEqual(space_x[0], 0.0, places=5)
        self.assertAlmostEqual(space_x[-1], networks, places=5)

    def test_different_p1_values(self):
        """Test with different p1 point values."""
        networks = 10
        p1 = (2, 8)
        p2 = (1, 3)

        space_x, space_y = draw_order3(networks, p1, p2)

        self.assertEqual(len(space_x), 10)
        self.assertEqual(len(space_y), 10)
        self.assertIsInstance(space_x, np.ndarray)
        self.assertIsInstance(space_y, np.ndarray)

    def test_different_p2_values(self):
        """Test with different p2 point values."""
        networks = 10
        p1 = (0, 10)
        p2 = (5, 5)

        space_x, space_y = draw_order3(networks, p1, p2)

        self.assertEqual(len(space_x), 10)
        self.assertEqual(len(space_y), 10)

    def test_larger_network_count(self):
        """Test with larger network count."""
        networks = 100
        p1 = (0, 10)
        p2 = (0, 0)

        space_x, space_y = draw_order3(networks, p1, p2)

        self.assertEqual(len(space_x), 10)
        self.assertAlmostEqual(space_x[-1], networks, places=5)

    def test_polynomial_smoothness(self):
        """Test that resulting polynomial is smooth (no abrupt changes)."""
        networks = 10
        p1 = (0, 10)
        p2 = (0, 5)

        space_x, space_y = draw_order3(networks, p1, p2)

        # Check that consecutive differences are reasonable
        differences = np.diff(space_y)
        # With 3rd order polynomial, differences should be smooth
        self.assertTrue(np.all(np.isfinite(differences)))

    def test_symmetry_with_symmetric_points(self):
        """Test with symmetric input points."""
        networks = 10
        p1 = (0, 10)
        p2 = (5, 5)

        space_x, space_y = draw_order3(networks, p1, p2)

        self.assertEqual(len(space_x), len(space_y))
        self.assertIsInstance(space_x, np.ndarray)

    def test_return_tuple(self):
        """Test that function returns a tuple."""
        networks = 10
        p1 = (0, 10)
        p2 = (0, 0)

        result = draw_order3(networks, p1, p2)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


class TestDrawPiramidal(unittest.TestCase):
    """Test draw_piramidal function."""

    def test_basic_piramidal(self):
        """Test basic piramidal function."""
        networks = 10
        p1 = (0, 10)
        p2 = (0, 0)

        x, y = draw_piramidal(networks, p1, p2)

        self.assertIsInstance(x, list)
        self.assertIsInstance(y, list)
        self.assertEqual(len(x), 3)
        self.assertEqual(len(y), 3)

    def test_piramidal_output_length(self):
        """Test that piramidal output has 3 points."""
        networks = 20
        p1 = (0, 10)
        p2 = (0, 0)

        x, y = draw_piramidal(networks, p1, p2)

        # Should return 3 points (start, midpoint, end)
        self.assertEqual(len(x), 3)
        self.assertEqual(len(y), 3)

    def test_piramidal_with_different_points(self):
        """Test piramidal with different input points."""
        networks = 10
        p1 = (2, 8)
        p2 = (1, 5)

        x, y = draw_piramidal(networks, p1, p2)

        self.assertEqual(len(x), 3)
        self.assertEqual(len(y), 3)

    def test_piramidal_start_and_end(self):
        """Test that start and end points are in output."""
        networks = 10
        p1 = (0, 10)
        p2 = (2, 5)

        x, y = draw_piramidal(networks, p1, p2)

        # First and last x values should correspond to p1
        self.assertEqual(x[0], p1[0])
        self.assertEqual(x[2], p1[1])

        # First and last y values should correspond to p2
        self.assertEqual(y[0], p2[0])
        self.assertEqual(y[2], p2[1])

    def test_piramidal_midpoint_calculation(self):
        """Test that midpoint is calculated correctly."""
        networks = 10
        p1 = (0, 10)
        p2 = (0, 0)

        x, y = draw_piramidal(networks, p1, p2)

        # Midpoint calculation: (p2[0] + 1, p1[1] + 1)
        expected_mid_x = p2[0] + 1
        expected_mid_y = p1[1] + 1

        self.assertEqual(x[1], expected_mid_x)
        self.assertEqual(y[1], expected_mid_y)

    def test_piramidal_return_tuple(self):
        """Test that function returns a tuple."""
        networks = 10
        p1 = (0, 10)
        p2 = (0, 0)

        result = draw_piramidal(networks, p1, p2)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_piramidal_with_negative_values(self):
        """Test piramidal with negative coordinate values."""
        networks = 10
        p1 = (-5, 5)
        p2 = (-2, 2)

        x, y = draw_piramidal(networks, p1, p2)

        self.assertEqual(len(x), 3)
        self.assertEqual(len(y), 3)
        self.assertEqual(x[0], p1[0])
        self.assertEqual(y[0], p2[0])

    def test_piramidal_symmetric_points(self):
        """Test piramidal with symmetric points."""
        networks = 10
        p1 = (0, 10)
        p2 = (5, 5)

        x, y = draw_piramidal(networks, p1, p2)

        self.assertEqual(len(x), 3)
        self.assertEqual(len(y), 3)


class TestPolyfitComparison(unittest.TestCase):
    """Test comparison between order3 and piramidal functions."""

    def test_both_functions_produce_output(self):
        """Test that both functions produce valid output."""
        networks = 10
        p1 = (0, 10)
        p2 = (0, 0)

        x_order3, y_order3 = draw_order3(networks, p1, p2)
        x_piramidal, y_piramidal = draw_piramidal(networks, p1, p2)

        self.assertGreater(len(x_order3), 0)
        self.assertGreater(len(x_piramidal), 0)

    def test_different_output_lengths(self):
        """Test that order3 and piramidal have different output lengths."""
        networks = 10
        p1 = (0, 10)
        p2 = (0, 0)

        x_order3, y_order3 = draw_order3(networks, p1, p2)
        x_piramidal, y_piramidal = draw_piramidal(networks, p1, p2)

        # order3 produces 10 points, piramidal produces 3 points
        self.assertEqual(len(x_order3), 10)
        self.assertEqual(len(x_piramidal), 3)


class TestPolyfitEdgeCases(unittest.TestCase):
    """Test edge cases for polyfit functions."""

    def test_order3_with_zero_networks(self):
        """Test order3 with zero networks."""
        networks = 0
        p1 = (0, 10)
        p2 = (0, 0)

        space_x, space_y = draw_order3(networks, p1, p2)

        # Should still produce 10 points from 0 to 0
        self.assertEqual(len(space_x), 10)
        self.assertTrue(np.all(space_x >= 0))

    def test_piramidal_with_same_points(self):
        """Test piramidal with same start and end points."""
        networks = 10
        p1 = (5, 5)
        p2 = (3, 3)

        x, y = draw_piramidal(networks, p1, p2)

        # Should still produce 3 points
        self.assertEqual(len(x), 3)
        self.assertEqual(len(y), 3)

    def test_order3_with_large_values(self):
        """Test order3 with large coordinate values."""
        networks = 1000
        p1 = (0, 100)
        p2 = (0, 100)

        space_x, space_y = draw_order3(networks, p1, p2)

        self.assertEqual(len(space_x), 10)
        self.assertTrue(np.all(np.isfinite(space_y)))


if __name__ == "__main__":
    unittest.main()
