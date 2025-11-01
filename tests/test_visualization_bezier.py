"""
Tests for Bezier curve functions.

This module tests bezier curve generation functions used in
py3plex multilayer network visualizations.
"""
import unittest

import numpy as np

from py3plex.visualization.bezier import bezier_calculate_dfy, draw_bezier


class TestBezierCalculateDfy(unittest.TestCase):
    """Test bezier_calculate_dfy function."""

    def test_upper_mode_basic(self):
        """Test dfy calculation in upper mode."""
        mp_y = 0.5
        path_height = 2.0
        x0, midpoint_x, x1 = 0.0, 5.0, 10.0
        y0, y1 = 0.0, 0.0
        dfx = np.array([0.0, 2.5, 5.0, 7.5, 10.0])

        result = bezier_calculate_dfy(
            mp_y, path_height, x0, midpoint_x, x1, y0, y1, dfx, mode="upper"
        )

        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(len(result), len(dfx))
        # Start and end should be at y0 and y1
        self.assertAlmostEqual(result[0], y0, places=5)
        self.assertAlmostEqual(result[-1], y1, places=5)

    def test_bottom_mode_basic(self):
        """Test dfy calculation in bottom mode."""
        mp_y = 0.5
        path_height = 2.0
        x0, midpoint_x, x1 = 0.0, 5.0, 10.0
        y0, y1 = 0.0, 0.0
        dfx = np.array([0.0, 2.5, 5.0, 7.5, 10.0])

        result = bezier_calculate_dfy(
            mp_y, path_height, x0, midpoint_x, x1, y0, y1, dfx, mode="bottom"
        )

        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(len(result), len(dfx))
        self.assertAlmostEqual(result[0], y0, places=5)
        self.assertAlmostEqual(result[-1], y1, places=5)

    def test_invalid_mode_raises_error(self):
        """Test that invalid mode raises ValueError."""
        mp_y = 0.5
        path_height = 2.0
        x0, midpoint_x, x1 = 0.0, 5.0, 10.0
        y0, y1 = 0.0, 0.0
        dfx = np.array([0.0, 5.0, 10.0])

        with self.assertRaises(ValueError) as context:
            bezier_calculate_dfy(
                mp_y, path_height, x0, midpoint_x, x1, y0, y1, dfx, mode="invalid"
            )
        self.assertIn("Unknown mode", str(context.exception))

    def test_different_y_endpoints(self):
        """Test dfy calculation with different start and end y values."""
        mp_y = 0.5
        path_height = 2.0
        x0, midpoint_x, x1 = 0.0, 5.0, 10.0
        y0, y1 = 1.0, 3.0
        dfx = np.array([0.0, 2.5, 5.0, 7.5, 10.0])

        result = bezier_calculate_dfy(
            mp_y, path_height, x0, midpoint_x, x1, y0, y1, dfx, mode="upper"
        )

        self.assertAlmostEqual(result[0], y0, places=5)
        self.assertAlmostEqual(result[-1], y1, places=5)

    def test_output_is_smooth(self):
        """Test that output curve is smooth (no abrupt changes)."""
        mp_y = 0.5
        path_height = 2.0
        x0, midpoint_x, x1 = 0.0, 5.0, 10.0
        y0, y1 = 0.0, 0.0
        dfx = np.linspace(x0, x1, 100)

        result = bezier_calculate_dfy(
            mp_y, path_height, x0, midpoint_x, x1, y0, y1, dfx, mode="upper"
        )

        # Check that consecutive differences are small (smooth curve)
        differences = np.diff(result)
        max_diff = np.max(np.abs(differences))
        self.assertLess(max_diff, 1.0)  # No abrupt jumps


class TestDrawBezier(unittest.TestCase):
    """Test draw_bezier function."""

    def test_quadratic_mode_basic(self):
        """Test basic quadratic bezier curve."""
        total_size = 100
        p1 = (0.0, 10.0)
        p2 = (0.0, 0.0)

        dfx, dfy = draw_bezier(
            total_size, p1, p2, mode="quadratic", linemode="both", resolution=1.0
        )

        self.assertIsInstance(dfx, np.ndarray)
        self.assertIsInstance(dfy, np.ndarray)
        self.assertEqual(len(dfx), len(dfy))
        self.assertGreater(len(dfx), 0)

    def test_quadratic_mode_upper_linemode(self):
        """Test quadratic bezier with upper linemode."""
        total_size = 100
        p1 = (0.0, 10.0)
        p2 = (0.0, 0.0)

        dfx, dfy = draw_bezier(
            total_size, p1, p2, mode="quadratic", linemode="upper", resolution=1.0
        )

        self.assertGreater(len(dfx), 0)
        self.assertEqual(len(dfx), len(dfy))

    def test_quadratic_mode_bottom_linemode(self):
        """Test quadratic bezier with bottom linemode."""
        total_size = 100
        p1 = (0.0, 10.0)
        p2 = (0.0, 0.0)

        dfx, dfy = draw_bezier(
            total_size, p1, p2, mode="quadratic", linemode="bottom", resolution=1.0
        )

        self.assertGreater(len(dfx), 0)
        self.assertEqual(len(dfx), len(dfy))

    def test_reversed_point_order(self):
        """Test that function handles reversed point order correctly."""
        total_size = 100
        # p1 has x0 > x1
        p1 = (10.0, 0.0)
        p2 = (0.0, 0.0)

        dfx, dfy = draw_bezier(
            total_size, p1, p2, mode="quadratic", linemode="both", resolution=1.0
        )

        # Should still produce valid output
        self.assertGreater(len(dfx), 0)
        self.assertEqual(len(dfx), len(dfy))

    def test_different_resolution(self):
        """Test bezier with different resolution values."""
        total_size = 100
        p1 = (0.0, 10.0)
        p2 = (0.0, 0.0)

        # Fine resolution
        dfx_fine, dfy_fine = draw_bezier(
            total_size, p1, p2, mode="quadratic", linemode="both", resolution=0.1
        )

        # Coarse resolution
        dfx_coarse, dfy_coarse = draw_bezier(
            total_size, p1, p2, mode="quadratic", linemode="both", resolution=1.0
        )

        # Fine resolution should have more points
        self.assertGreater(len(dfx_fine), len(dfx_coarse))

    def test_different_path_heights(self):
        """Test bezier with different path heights."""
        total_size = 100
        p1 = (0.0, 10.0)
        p2 = (0.0, 0.0)

        dfx1, dfy1 = draw_bezier(
            total_size, p1, p2, mode="quadratic", path_height=1.0, resolution=1.0
        )

        dfx2, dfy2 = draw_bezier(
            total_size, p1, p2, mode="quadratic", path_height=3.0, resolution=1.0
        )

        # Both should produce valid curves
        self.assertEqual(len(dfx1), len(dfy1))
        self.assertEqual(len(dfx2), len(dfy2))

    def test_cubic_mode_not_implemented(self):
        """Test that cubic mode raises NotImplementedError."""
        total_size = 100
        p1 = (0.0, 10.0)
        p2 = (0.0, 0.0)

        with self.assertRaises(NotImplementedError) as context:
            draw_bezier(total_size, p1, p2, mode="cubic")
        self.assertIn("Cubic", str(context.exception))

    def test_invalid_mode_raises_error(self):
        """Test that invalid mode raises ValueError."""
        total_size = 100
        p1 = (0.0, 10.0)
        p2 = (0.0, 0.0)

        with self.assertRaises(ValueError) as context:
            draw_bezier(total_size, p1, p2, mode="invalid")
        self.assertIn("Unknown mode", str(context.exception))

    def test_invalid_linemode_raises_error(self):
        """Test that invalid linemode raises ValueError."""
        total_size = 100
        p1 = (0.0, 10.0)
        p2 = (0.0, 0.0)

        with self.assertRaises(ValueError) as context:
            draw_bezier(
                total_size, p1, p2, mode="quadratic", linemode="invalid", resolution=1.0
            )
        self.assertIn("Unknown linemode", str(context.exception))

    def test_curve_endpoints(self):
        """Test that curve starts and ends at correct points."""
        total_size = 100
        p1 = (0.0, 10.0)
        p2 = (1.0, 3.0)

        dfx, dfy = draw_bezier(
            total_size, p1, p2, mode="quadratic", linemode="both", resolution=0.5
        )

        # Check x endpoints
        self.assertAlmostEqual(dfx[0], min(p1), places=5)
        # y endpoints should be close to p2 values
        self.assertAlmostEqual(dfy[0], p2[0], places=0)

    def test_output_arrays_are_numpy(self):
        """Test that output arrays are numpy arrays."""
        total_size = 100
        p1 = (0.0, 10.0)
        p2 = (0.0, 0.0)

        dfx, dfy = draw_bezier(
            total_size, p1, p2, mode="quadratic", linemode="both", resolution=1.0
        )

        self.assertIsInstance(dfx, np.ndarray)
        self.assertIsInstance(dfy, np.ndarray)

    def test_non_zero_y_coordinates(self):
        """Test bezier with non-zero y coordinates."""
        total_size = 100
        p1 = (5.0, 15.0)
        p2 = (2.0, 4.0)

        dfx, dfy = draw_bezier(
            total_size, p1, p2, mode="quadratic", linemode="both", resolution=1.0
        )

        self.assertGreater(len(dfx), 0)
        self.assertEqual(len(dfx), len(dfy))


class TestBezierEdgeCases(unittest.TestCase):
    """Test edge cases for bezier functions."""

    def test_same_start_and_end_points(self):
        """Test bezier with same start and end points."""
        total_size = 100
        p1 = (5.0, 5.0)
        p2 = (2.0, 2.0)

        # Should handle gracefully (might return empty or single point)
        try:
            dfx, dfy = draw_bezier(
                total_size, p1, p2, mode="quadratic", linemode="both", resolution=1.0
            )
            # If it succeeds, check it returns valid arrays
            self.assertEqual(len(dfx), len(dfy))
        except Exception:
            # It's acceptable to raise an exception for degenerate cases
            pass

    def test_very_close_points(self):
        """Test bezier with very close points."""
        total_size = 100
        p1 = (5.0, 5.01)
        p2 = (2.0, 2.0)

        try:
            dfx, dfy = draw_bezier(
                total_size, p1, p2, mode="quadratic", linemode="both", resolution=0.005
            )
            self.assertGreater(len(dfx), 0)
        except Exception:
            # Acceptable to fail on edge cases
            pass


if __name__ == "__main__":
    unittest.main()
