"""
Tests for improved error messages with constructive suggestions.

This module verifies that errors now provide helpful suggestions,
"did you mean?" alternatives, and clear guidance to users.
"""
import pytest
from pathlib import Path
import tempfile

from py3plex.exceptions import (
    AlgorithmError, 
    Py3plexIOError, 
    Py3plexFormatError, 
    Py3plexException, 
    ParsingError,
    NetworkConstructionError
)
from py3plex.paths.algorithms import PathRegistry
from py3plex.centrality.robustness import robustness_centrality
from py3plex.workflows import WorkflowConfig
from py3plex.core import multinet
from py3plex.temporal_utils import extract_edge_time


class TestPathAlgorithmErrors:
    """Test improved error messages for path algorithm selection."""

    def test_unknown_algorithm_provides_suggestions(self):
        """Test that unknown algorithm errors provide 'did you mean' suggestions."""
        registry = PathRegistry()
        registry.register("shortest_path")(lambda: None)
        registry.register("all_paths")(lambda: None)
        
        with pytest.raises(AlgorithmError) as exc_info:
            registry.get("shortest_pth")  # typo
        
        error = exc_info.value
        # Should suggest similar algorithm
        assert error.did_you_mean == "shortest_path"
        # Should list valid algorithms
        assert len(error.suggestions) > 0
        assert any("available" in s.lower() for s in error.suggestions)

    def test_unknown_algorithm_lists_valid_options(self):
        """Test that error lists all valid algorithm options."""
        registry = PathRegistry()
        registry.register("alg1")(lambda: None)
        registry.register("alg2")(lambda: None)
        
        with pytest.raises(AlgorithmError) as exc_info:
            registry.get("unknown_algorithm")
        
        error = exc_info.value
        # Should list available algorithms
        suggestions_text = " ".join(error.suggestions)
        assert "alg1" in suggestions_text
        assert "alg2" in suggestions_text


class TestRobustnessCentralityErrors:
    """Test improved error messages for robustness centrality."""

    def test_invalid_target_provides_clear_guidance(self):
        """Test that invalid target parameter provides clear guidance."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([["a", "L0", "b", "L0", 1.0]], input_type="list")
        
        with pytest.raises(Py3plexException) as exc_info:
            robustness_centrality(net, target="nodes")  # should be "node"
        
        error = exc_info.value
        # Should provide suggestions
        assert len(error.suggestions) > 0
        assert any("node" in s.lower() for s in error.suggestions)
        # Should suggest the correct value
        assert error.did_you_mean == "node"

    def test_invalid_metric_provides_did_you_mean(self):
        """Test that invalid metric provides 'did you mean' suggestion."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([["a", "L0", "b", "L0", 1.0]], input_type="list")
        
        with pytest.raises(Py3plexException) as exc_info:
            robustness_centrality(net, target="node", metric="giant_componet")  # typo
        
        error = exc_info.value
        # Should suggest similar metric
        assert error.did_you_mean == "giant_component"
        # Should list valid metrics
        assert len(error.suggestions) > 0

    def test_invalid_metric_lists_all_options(self):
        """Test that error lists all valid metric options."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([["a", "L0", "b", "L0", 1.0]], input_type="list")
        
        with pytest.raises(Py3plexException) as exc_info:
            robustness_centrality(net, target="node", metric="invalid_metric")
        
        error = exc_info.value
        suggestions_text = " ".join(error.suggestions)
        # Should mention valid metrics
        assert "giant_component" in suggestions_text
        assert "avg_shortest_path" in suggestions_text


class TestWorkflowConfigErrors:
    """Test improved error messages for workflow configuration."""

    def test_missing_config_file_provides_helpful_message(self):
        """Test that missing config file error is helpful."""
        with pytest.raises(Py3plexIOError) as exc_info:
            WorkflowConfig.from_file("/nonexistent/config.yaml")
        
        error = exc_info.value
        # Should provide suggestions
        assert len(error.suggestions) > 0
        assert any("path is correct" in s.lower() for s in error.suggestions)

    def test_yaml_missing_dependency_provides_install_hint(self):
        """Test that YAML format error suggests installation."""
        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("name: test\n")
            temp_file = f.name
        
        try:
            # Mock YAML not available
            import py3plex.workflows as wf
            old_has_yaml = wf.HAS_YAML
            wf.HAS_YAML = False
            
            try:
                with pytest.raises(Py3plexFormatError) as exc_info:
                    WorkflowConfig.from_file(temp_file)
                
                error = exc_info.value
                # Should suggest installing PyYAML
                assert len(error.suggestions) > 0
                suggestions_text = " ".join(error.suggestions)
                assert "pyyaml" in suggestions_text.lower()
            finally:
                wf.HAS_YAML = old_has_yaml
        finally:
            Path(temp_file).unlink()

    def test_unsupported_format_provides_valid_formats(self):
        """Test that unsupported format error lists valid formats."""
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("some content\n")
            temp_file = f.name
        
        try:
            with pytest.raises(Py3plexFormatError) as exc_info:
                WorkflowConfig.from_file(temp_file)
            
            error = exc_info.value
            # Should provide suggestions about valid formats
            assert len(error.suggestions) > 0
            suggestions_text = " ".join(error.suggestions)
            # Should mention at least one valid format
            assert any(fmt in suggestions_text for fmt in [".yaml", ".yml", ".json"])
        finally:
            Path(temp_file).unlink()


class TestTemporalUtilsErrors:
    """Test improved error messages for temporal utilities."""

    def test_invalid_time_value_provides_format_hints(self):
        """Test that invalid time values provide format hints."""
        with pytest.raises(ParsingError) as exc_info:
            # Invalid time value in edge attributes
            extract_edge_time({"t": [1, 2, 3]})  # List is not a valid time type
        
        error = exc_info.value
        # Should provide suggestions about valid formats
        assert len(error.suggestions) > 0
        suggestions_text = " ".join(error.suggestions)
        assert "timestamp" in suggestions_text.lower() or "datetime" in suggestions_text.lower()


class TestAttributeCorrelationErrors:
    """Test improved error messages for attribute correlation."""

    def test_network_without_core_network_provides_helpful_message(self):
        """Test that missing core_network error is helpful."""
        # Create a mock network without core_network
        class MockNetwork:
            pass
        
        from py3plex.algorithms.attribute_correlation import correlate_attributes_with_centrality
        
        with pytest.raises(NetworkConstructionError) as exc_info:
            correlate_attributes_with_centrality(
                MockNetwork(), 
                "some_attribute", 
                centrality_type="degree"
            )
        
        error = exc_info.value
        # Should provide suggestions
        assert len(error.suggestions) > 0
        assert any("initialized" in s.lower() for s in error.suggestions)


class TestErrorMessageFormatting:
    """Test that improved errors format nicely."""

    def test_error_includes_did_you_mean_in_str(self):
        """Test that error string representation includes 'did you mean'."""
        registry = PathRegistry()
        registry.register("algorithm_a")(lambda: None)
        
        try:
            registry.get("algoritm_a")  # typo
        except AlgorithmError as e:
            error_str = str(e)
            # Should mention 'did you mean' or show the suggestion
            assert "algorithm_a" in error_str or "did you mean" in error_str.lower()

    def test_error_includes_suggestions_in_str(self):
        """Test that error string includes suggestions."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([["a", "L0", "b", "L0", 1.0]], input_type="list")
        
        try:
            robustness_centrality(net, target="invalid")
        except Py3plexException as e:
            error_str = str(e)
            # Should include helpful text
            assert "node" in error_str.lower() or "layer" in error_str.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

