"""
Tests for color utility functions.

This module tests color conversion and gradient generation functions
used in py3plex visualizations.
"""
import unittest

from py3plex.visualization.colors import (
    RGB_to_hex,
    all_color_names,
    color_dict,
    colors_default,
    hex_to_RGB,
    linear_gradient,
)


class TestHexToRGB(unittest.TestCase):
    """Test hex_to_RGB conversion function."""

    def test_white_conversion(self):
        """Test conversion of white (#FFFFFF)."""
        result = hex_to_RGB("#FFFFFF")
        self.assertEqual(result, [255, 255, 255])

    def test_black_conversion(self):
        """Test conversion of black (#000000)."""
        result = hex_to_RGB("#000000")
        self.assertEqual(result, [0, 0, 0])

    def test_red_conversion(self):
        """Test conversion of red (#FF0000)."""
        result = hex_to_RGB("#FF0000")
        self.assertEqual(result, [255, 0, 0])

    def test_green_conversion(self):
        """Test conversion of green (#00FF00)."""
        result = hex_to_RGB("#00FF00")
        self.assertEqual(result, [0, 255, 0])

    def test_blue_conversion(self):
        """Test conversion of blue (#0000FF)."""
        result = hex_to_RGB("#0000FF")
        self.assertEqual(result, [0, 0, 255])

    def test_gray_conversion(self):
        """Test conversion of gray (#808080)."""
        result = hex_to_RGB("#808080")
        self.assertEqual(result, [128, 128, 128])

    def test_custom_color_conversion(self):
        """Test conversion of a custom color."""
        result = hex_to_RGB("#A1B2C3")
        self.assertEqual(result, [161, 178, 195])


class TestRGBToHex(unittest.TestCase):
    """Test RGB_to_hex conversion function."""

    def test_white_conversion(self):
        """Test conversion of white RGB."""
        result = RGB_to_hex([255, 255, 255])
        self.assertEqual(result.upper(), "#FFFFFF")

    def test_black_conversion(self):
        """Test conversion of black RGB."""
        result = RGB_to_hex([0, 0, 0])
        self.assertEqual(result.upper(), "#000000")

    def test_red_conversion(self):
        """Test conversion of red RGB."""
        result = RGB_to_hex([255, 0, 0])
        self.assertEqual(result.upper(), "#FF0000")

    def test_green_conversion(self):
        """Test conversion of green RGB."""
        result = RGB_to_hex([0, 255, 0])
        self.assertEqual(result.upper(), "#00FF00")

    def test_blue_conversion(self):
        """Test conversion of blue RGB."""
        result = RGB_to_hex([0, 0, 255])
        self.assertEqual(result.upper(), "#0000FF")

    def test_single_digit_hex_values(self):
        """Test conversion with single-digit hex values (padded with 0)."""
        result = RGB_to_hex([15, 15, 15])
        self.assertEqual(result.upper(), "#0F0F0F")

    def test_float_rgb_values(self):
        """Test conversion with float RGB values (should convert to int)."""
        result = RGB_to_hex([255.7, 128.3, 64.9])
        self.assertEqual(result.upper(), "#FF8040")


class TestRoundTripConversion(unittest.TestCase):
    """Test round-trip conversion between hex and RGB."""

    def test_hex_to_rgb_to_hex(self):
        """Test hex -> RGB -> hex conversion."""
        original = "#A1B2C3"
        rgb = hex_to_RGB(original)
        result = RGB_to_hex(rgb)
        self.assertEqual(result.upper(), original.upper())

    def test_rgb_to_hex_to_rgb(self):
        """Test RGB -> hex -> RGB conversion."""
        original = [123, 45, 67]
        hex_color = RGB_to_hex(original)
        result = hex_to_RGB(hex_color)
        self.assertEqual(result, original)

    def test_multiple_colors(self):
        """Test round-trip conversion for multiple colors."""
        test_colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFFFF", "#000000", "#808080"]
        for color in test_colors:
            with self.subTest(color=color):
                rgb = hex_to_RGB(color)
                result = RGB_to_hex(rgb)
                self.assertEqual(result.upper(), color.upper())


class TestColorDict(unittest.TestCase):
    """Test color_dict function."""

    def test_single_color(self):
        """Test color_dict with a single RGB color."""
        gradient = [[255, 0, 0]]
        result = color_dict(gradient)

        self.assertIn("hex", result)
        self.assertIn("r", result)
        self.assertIn("g", result)
        self.assertIn("b", result)

        self.assertEqual(len(result["hex"]), 1)
        self.assertEqual(len(result["r"]), 1)
        self.assertEqual(len(result["g"]), 1)
        self.assertEqual(len(result["b"]), 1)

        self.assertEqual(result["r"][0], 255)
        self.assertEqual(result["g"][0], 0)
        self.assertEqual(result["b"][0], 0)

    def test_multiple_colors(self):
        """Test color_dict with multiple RGB colors."""
        gradient = [[255, 0, 0], [0, 255, 0], [0, 0, 255]]
        result = color_dict(gradient)

        self.assertEqual(len(result["hex"]), 3)
        self.assertEqual(len(result["r"]), 3)
        self.assertEqual(len(result["g"]), 3)
        self.assertEqual(len(result["b"]), 3)

        self.assertEqual(result["r"], [255, 0, 0])
        self.assertEqual(result["g"], [0, 255, 0])
        self.assertEqual(result["b"], [0, 0, 255])

    def test_hex_values_in_dict(self):
        """Test that hex values are properly formatted in color_dict."""
        gradient = [[255, 0, 0]]
        result = color_dict(gradient)
        self.assertEqual(result["hex"][0].upper(), "#FF0000")


class TestLinearGradient(unittest.TestCase):
    """Test linear_gradient function."""

    def test_gradient_from_black_to_white(self):
        """Test gradient from black to white."""
        result = linear_gradient("#000000", "#FFFFFF", n=3)

        self.assertIn("hex", result)
        self.assertIn("r", result)
        self.assertIn("g", result)
        self.assertIn("b", result)

        self.assertEqual(len(result["hex"]), 3)
        # First should be black
        self.assertEqual(result["r"][0], 0)
        self.assertEqual(result["g"][0], 0)
        self.assertEqual(result["b"][0], 0)
        # Last should be white
        self.assertEqual(result["r"][-1], 255)
        self.assertEqual(result["g"][-1], 255)
        self.assertEqual(result["b"][-1], 255)

    def test_gradient_two_colors(self):
        """Test gradient with n=2 (just start and end)."""
        result = linear_gradient("#FF0000", "#0000FF", n=2)

        self.assertEqual(len(result["hex"]), 2)
        # First should be red
        self.assertEqual(result["r"][0], 255)
        self.assertEqual(result["b"][0], 0)
        # Second should be blue
        self.assertEqual(result["r"][1], 0)
        self.assertEqual(result["b"][1], 255)

    def test_gradient_default_finish(self):
        """Test gradient with default finish color (white)."""
        result = linear_gradient("#000000", n=5)

        self.assertEqual(len(result["hex"]), 5)
        # Should go from black to white
        self.assertEqual(result["r"][0], 0)
        self.assertEqual(result["r"][-1], 255)

    def test_gradient_increasing_values(self):
        """Test that gradient values increase monotonically."""
        result = linear_gradient("#000000", "#FFFFFF", n=10)

        # Check that RGB values generally increase
        for i in range(len(result["r"]) - 1):
            self.assertLessEqual(result["r"][i], result["r"][i + 1])
            self.assertLessEqual(result["g"][i], result["g"][i + 1])
            self.assertLessEqual(result["b"][i], result["b"][i + 1])

    def test_gradient_red_to_blue(self):
        """Test gradient from red to blue."""
        result = linear_gradient("#FF0000", "#0000FF", n=5)

        # Red should decrease, blue should increase
        self.assertGreater(result["r"][0], result["r"][-1])
        self.assertLess(result["b"][0], result["b"][-1])


class TestColorConstants(unittest.TestCase):
    """Test color constant definitions."""

    def test_colors_default_is_list(self):
        """Test that colors_default is a list."""
        self.assertIsInstance(colors_default, list)

    def test_colors_default_not_empty(self):
        """Test that colors_default is not empty."""
        self.assertGreater(len(colors_default), 0)

    def test_all_color_names_is_dict(self):
        """Test that all_color_names is a dictionary."""
        self.assertIsInstance(all_color_names, dict)

    def test_all_color_names_not_empty(self):
        """Test that all_color_names is not empty."""
        self.assertGreater(len(all_color_names), 0)

    def test_all_color_names_has_basic_colors(self):
        """Test that all_color_names includes basic colors."""
        basic_colors = ["red", "green", "blue", "white", "black"]
        for color in basic_colors:
            with self.subTest(color=color):
                self.assertIn(color, all_color_names)

    def test_all_color_names_hex_format(self):
        """Test that all color values in all_color_names are hex strings."""
        for color_name, hex_value in all_color_names.items():
            with self.subTest(color=color_name):
                self.assertIsInstance(hex_value, str)
                self.assertTrue(hex_value.startswith("#"))
                self.assertEqual(len(hex_value), 7)  # #RRGGBB format

    def test_sample_color_values(self):
        """Test that specific colors have correct hex values."""
        expected = {
            "red": "#FF0000",
            "green": "#008000",
            "blue": "#0000FF",
            "white": "#FFFFFF",
            "black": "#000000",
        }
        for color_name, expected_hex in expected.items():
            with self.subTest(color=color_name):
                self.assertEqual(all_color_names[color_name].upper(), expected_hex)


if __name__ == "__main__":
    unittest.main()
