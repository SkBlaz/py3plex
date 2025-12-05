"""
Tests for visualization module imports and API.

This module tests that visualization imports work correctly,
including both the convenience imports from py3plex.visualization
and the traditional submodule imports.
"""
import unittest


class TestVisualizationConvenienceImports(unittest.TestCase):
    """Test convenience imports from py3plex.visualization."""

    def test_hairball_plot_import(self):
        """Test that hairball_plot can be imported from py3plex.visualization."""
        from py3plex.visualization import hairball_plot
        self.assertTrue(callable(hairball_plot))

    def test_draw_multilayer_default_import(self):
        """Test that draw_multilayer_default can be imported from py3plex.visualization."""
        from py3plex.visualization import draw_multilayer_default
        self.assertTrue(callable(draw_multilayer_default))

    def test_draw_multiedges_import(self):
        """Test that draw_multiedges can be imported from py3plex.visualization."""
        from py3plex.visualization import draw_multiedges
        self.assertTrue(callable(draw_multiedges))

    def test_interactive_diagonal_plot_import(self):
        """Test that interactive_diagonal_plot can be imported from py3plex.visualization."""
        from py3plex.visualization import interactive_diagonal_plot
        self.assertTrue(callable(interactive_diagonal_plot))

    def test_colors_default_import(self):
        """Test that colors_default can be imported from py3plex.visualization."""
        from py3plex.visualization import colors_default
        self.assertIsInstance(colors_default, list)
        self.assertGreater(len(colors_default), 0)

    def test_plt_import(self):
        """Test that plt can be imported from py3plex.visualization."""
        from py3plex.visualization import plt
        # plt should be matplotlib.pyplot
        self.assertTrue(hasattr(plt, 'figure'))
        self.assertTrue(hasattr(plt, 'plot'))

    def test_color_utilities_import(self):
        """Test that color utilities can be imported from py3plex.visualization."""
        from py3plex.visualization import hex_to_RGB, RGB_to_hex
        self.assertTrue(callable(hex_to_RGB))
        self.assertTrue(callable(RGB_to_hex))

    def test_multiple_imports(self):
        """Test importing multiple items at once from py3plex.visualization."""
        from py3plex.visualization import (
            hairball_plot,
            colors_default,
            draw_multilayer_default,
            plt,
        )
        self.assertTrue(callable(hairball_plot))
        self.assertIsInstance(colors_default, list)
        self.assertTrue(callable(draw_multilayer_default))
        self.assertTrue(hasattr(plt, 'figure'))


class TestVisualizationSubmoduleImports(unittest.TestCase):
    """Test traditional submodule imports remain functional."""

    def test_multilayer_submodule_import(self):
        """Test importing from py3plex.visualization.multilayer."""
        from py3plex.visualization.multilayer import hairball_plot, plt
        self.assertTrue(callable(hairball_plot))
        self.assertTrue(hasattr(plt, 'figure'))

    def test_colors_submodule_import(self):
        """Test importing from py3plex.visualization.colors."""
        from py3plex.visualization.colors import colors_default
        self.assertIsInstance(colors_default, list)

    def test_embedding_visualization_import(self):
        """Test importing from py3plex.visualization.embedding_visualization."""
        from py3plex.visualization.embedding_visualization import embedding_tools
        # Should be a module
        self.assertTrue(hasattr(embedding_tools, '__name__'))


class TestVisualizationModuleStructure(unittest.TestCase):
    """Test the structure of the visualization module."""

    def test_module_has_docstring(self):
        """Test that the visualization module has a docstring."""
        import py3plex.visualization
        self.assertIsNotNone(py3plex.visualization.__doc__)
        self.assertIn("Visualization module", py3plex.visualization.__doc__)

    def test_module_has_all(self):
        """Test that the visualization module defines __all__."""
        import py3plex.visualization
        self.assertTrue(hasattr(py3plex.visualization, '__all__'))
        self.assertIsInstance(py3plex.visualization.__all__, list)
        self.assertGreater(len(py3plex.visualization.__all__), 0)

    def test_all_exported_items_importable(self):
        """Test that all items in __all__ can be imported."""
        import py3plex.visualization
        for item in py3plex.visualization.__all__:
            with self.subTest(item=item):
                self.assertTrue(
                    hasattr(py3plex.visualization, item),
                    f"{item} is in __all__ but not accessible"
                )

    def test_embedding_visualization_has_all(self):
        """Test that embedding_visualization defines __all__."""
        from py3plex.visualization import embedding_visualization
        self.assertTrue(hasattr(embedding_visualization, '__all__'))
        self.assertIsInstance(embedding_visualization.__all__, list)


class TestBackwardsCompatibility(unittest.TestCase):
    """Test that old import patterns still work (backwards compatibility)."""

    def test_example_visualization_imports(self):
        """Test imports from example_visualization.py still work."""
        # These are the imports from the main visualization example
        from py3plex.visualization.multilayer import hairball_plot, plt
        from py3plex.visualization.colors import colors_default
        from py3plex.visualization.embedding_visualization import embedding_tools

        self.assertTrue(callable(hairball_plot))
        self.assertTrue(hasattr(plt, 'figure'))
        self.assertIsInstance(colors_default, list)
        self.assertTrue(hasattr(embedding_tools, '__name__'))

    def test_import_paths_equivalent(self):
        """Test that different import paths give the same objects."""
        # Import the same function via different paths
        from py3plex.visualization import hairball_plot as hp1
        from py3plex.visualization.multilayer import hairball_plot as hp2

        # They should be the exact same object
        self.assertIs(hp1, hp2)

        # Same for colors_default
        from py3plex.visualization import colors_default as cd1
        from py3plex.visualization.colors import colors_default as cd2
        self.assertIs(cd1, cd2)


class TestVisualizationAxesAPI(unittest.TestCase):
    """Test the improved visualization API with optional axes."""

    def test_draw_multilayer_default_returns_axes(self):
        """Test that draw_multilayer_default returns axes object."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import networkx as nx
        from py3plex.visualization import draw_multilayer_default
        
        # Create simple test graphs
        G1 = nx.Graph()
        G1.add_edge(1, 2)
        nx.set_node_attributes(G1, {1: (0, 0), 2: (1, 1)}, 'pos')
        
        fig, ax = plt.subplots()
        result = draw_multilayer_default([G1], ax=ax)
        
        self.assertIsNotNone(result)
        plt.close(fig)

    def test_draw_multilayer_default_display_false_by_default(self):
        """Test that display defaults to False."""
        import inspect
        from py3plex.visualization import draw_multilayer_default
        
        sig = inspect.signature(draw_multilayer_default)
        display_param = sig.parameters.get('display')
        self.assertIsNotNone(display_param)
        self.assertEqual(display_param.default, False)

    def test_hairball_plot_returns_axes(self):
        """Test that hairball_plot returns axes object when draw=True."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import networkx as nx
        from py3plex.visualization import hairball_plot
        
        # Create a multilayer-style graph with tuple nodes
        G = nx.Graph()
        G.add_edges_from([
            ((1, 'layer1'), (2, 'layer1')),
            ((2, 'layer1'), (3, 'layer1')),
        ])
        
        fig, ax = plt.subplots()
        result = hairball_plot(G, ax=ax, draw=True)
        
        self.assertIsNotNone(result)
        plt.close(fig)

    def test_supra_adjacency_matrix_plot_returns_axes(self):
        """Test that supra_adjacency_matrix_plot returns axes object."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        from py3plex.visualization import supra_adjacency_matrix_plot
        
        matrix = np.random.rand(10, 10)
        
        fig, ax = plt.subplots()
        result = supra_adjacency_matrix_plot(matrix, ax=ax)
        
        self.assertIsNotNone(result)
        plt.close(fig)

    def test_draw_multiedges_returns_axes(self):
        """Test that draw_multiedges returns axes object."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import networkx as nx
        from py3plex.visualization import draw_multiedges
        
        # Create simple test graphs with positions
        G1 = nx.Graph()
        G1.add_node(1)
        G1.add_node(2)
        nx.set_node_attributes(G1, {1: (0, 0), 2: (1, 1)}, 'pos')
        
        fig, ax = plt.subplots()
        result = draw_multiedges([G1], [(1, 2)], ax=ax)
        
        self.assertIsNotNone(result)
        plt.close(fig)

    def test_draw_multilayer_sankey_display_false_by_default(self):
        """Test that draw_multilayer_sankey display defaults to False."""
        import inspect
        from py3plex.visualization import draw_multilayer_sankey
        
        sig = inspect.signature(draw_multilayer_sankey)
        display_param = sig.parameters.get('display')
        self.assertIsNotNone(display_param)
        self.assertEqual(display_param.default, False)


if __name__ == "__main__":
    unittest.main()
