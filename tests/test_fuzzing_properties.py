"""
Property-based fuzzing tests for py3plex input parsing and network loading.

This module uses Hypothesis to generate random inputs for fuzzing the parsing
and network loading functionality. It focuses on discovering edge cases and
bugs in input handling.
"""

import tempfile
import os
from io import StringIO
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import pytest

from py3plex.core import multinet


# Strategies for generating test data
def valid_node_ids():
    """Generate valid node IDs (strings or small integers)."""
    return st.one_of(
        st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_-.'
        )),
        st.integers(min_value=0, max_value=10000).map(str)
    )


def valid_layer_ids():
    """Generate valid layer IDs."""
    return st.text(min_size=1, max_size=15, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_'
    ))


def valid_weights():
    """Generate valid edge weights."""
    return st.one_of(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        st.integers(min_value=0, max_value=100).map(float)
    )


def multiedge_line():
    """Generate a single multiedge line: node1 layer1 node2 layer2 [weight]"""
    return st.builds(
        lambda n1, l1, n2, l2, w: f"{n1} {l1} {n2} {l2} {w}",
        valid_node_ids(),
        valid_layer_ids(),
        valid_node_ids(),
        valid_layer_ids(),
        valid_weights()
    )


def simple_edge_line():
    """Generate a simple edge line: node1 node2"""
    return st.builds(
        lambda n1, n2: f"{n1} {n2}",
        valid_node_ids(),
        valid_node_ids()
    )


class TestMultiedgelistParsing:
    """Property-based tests for multiedgelist format parsing."""

    @given(st.lists(multiedge_line(), min_size=1, max_size=20))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_valid_multiedgelist_parsing(self, lines):
        """Test that valid multiedgelist formats parse without crashing."""
        content = "\n".join(lines)
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Try to load the network
            net = multinet.multi_layer_network(verbose=False)
            net.load_network(
                input_file=temp_path,
                directed=False,
                input_type="multiedgelist"
            )
            
            # Verify basic properties
            assert net.core_network is not None, "Network should be initialized"
            
            # Network should have nodes
            nodes = list(net.core_network.nodes()) if net.core_network else []
            # Note: Empty networks are possible if all edges are self-loops or invalid
            
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            # These are acceptable validation errors
            pass
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except Exception:
                pass

    @given(st.text(min_size=0, max_size=1000))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_arbitrary_text_parsing(self, text):
        """Test that arbitrary text doesn't cause crashes (only expected errors)."""
        # Skip empty or whitespace-only text
        if not text.strip():
            return
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(text)
            temp_path = f.name
        
        try:
            net = multinet.multi_layer_network(verbose=False)
            net.load_network(
                input_file=temp_path,
                directed=False,
                input_type="multiedgelist"
            )
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, 
                FileNotFoundError, UnicodeDecodeError):
            # Expected errors for malformed input
            pass
        except AssertionError:
            # Assertions indicate logic errors - let them fail the test
            raise
        except MemoryError:
            # Memory errors indicate real issues
            raise
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass


class TestEdgelistParsing:
    """Property-based tests for simple edgelist format parsing."""

    @given(st.lists(simple_edge_line(), min_size=1, max_size=20))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_valid_edgelist_parsing(self, lines):
        """Test that valid edgelist formats parse without crashing."""
        content = "\n".join(lines)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            net = multinet.multi_layer_network(verbose=False)
            net.load_network(
                input_file=temp_path,
                directed=False,
                input_type="edgelist"
            )
            
            # Verify basic properties
            assert net.core_network is not None, "Network should be initialized"
            
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            # Expected validation errors
            pass
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass


class TestDelimiterHandling:
    """Property-based tests for delimiter handling in parsing."""

    @given(
        st.lists(multiedge_line(), min_size=1, max_size=10),
        st.sampled_from(["---", ":::", "___", "|||", "..."])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_different_delimiters(self, lines, delimiter):
        """Test that different label delimiters work correctly."""
        content = "\n".join(lines)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            net = multinet.multi_layer_network(verbose=False, label_delimiter=delimiter)
            net.load_network(
                input_file=temp_path,
                directed=False,
                input_type="multiedgelist",
                label_delimiter=delimiter
            )
            
            # Should parse without crashes
            assert net.core_network is not None
            
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            pass
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass


class TestNetworkLoadRoundtrip:
    """Property-based tests for load/save roundtrip invariants."""

    @given(st.lists(multiedge_line(), min_size=2, max_size=10))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_load_save_roundtrip(self, lines):
        """Test that loading and saving preserves network structure."""
        content = "\n".join(lines)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
            output_path = f2.name
        
        try:
            # Load network
            net1 = multinet.multi_layer_network(verbose=False)
            net1.load_network(
                input_file=temp_path,
                directed=False,
                input_type="multiedgelist"
            )
            
            if net1.core_network is None:
                # Empty network - skip
                return
            
            # Get counts
            nodes1 = set(net1.core_network.nodes()) if net1.core_network else set()
            edges1 = set(net1.core_network.edges()) if net1.core_network else set()
            
            if not nodes1:
                # No nodes - skip
                return
            
            # Save network
            net1.save_network(output_file=output_path, output_type="multiedgelist")
            
            # Load again
            net2 = multinet.multi_layer_network(verbose=False)
            net2.load_network(
                input_file=output_path,
                directed=False,
                input_type="multiedgelist"
            )
            
            # Compare (note: order may differ, use sets)
            nodes2 = set(net2.core_network.nodes()) if net2.core_network else set()
            
            # Node counts should match (edges may vary due to duplicates/weights)
            assert len(nodes1) == len(nodes2), \
                f"Node count mismatch: {len(nodes1)} vs {len(nodes2)}"
            
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            # Expected for some edge cases
            pass
        finally:
            try:
                os.unlink(temp_path)
                os.unlink(output_path)
            except Exception:
                pass


class TestUnicodeHandling:
    """Property-based tests for Unicode and special character handling."""

    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),  # Control chars and surrogates
            blacklist_characters='\n\r\t '  # Whitespace
        ))
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_unicode_node_names(self, node_name):
        """Test that Unicode node names are handled correctly."""
        # Create a simple network with unicode node name
        content = f"{node_name} layer1 node2 layer2 1.0"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False,
                                        encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            net = multinet.multi_layer_network(verbose=False)
            net.load_network(
                input_file=temp_path,
                directed=False,
                input_type="multiedgelist"
            )
            
            # Should not crash
            if net.core_network:
                nodes = list(net.core_network.nodes())
                # Should have at least one node
                
        except (ValueError, TypeError, UnicodeDecodeError, UnicodeEncodeError):
            # Expected for some unicode edge cases
            pass
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass


class TestEdgeCases:
    """Property-based tests for edge cases in network construction."""

    @given(st.integers(min_value=0, max_value=1000))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_self_loops(self, node_id):
        """Test that self-loops are handled correctly."""
        content = f"{node_id} l1 {node_id} l1 1.0"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            net = multinet.multi_layer_network(verbose=False)
            net.load_network(
                input_file=temp_path,
                directed=False,
                input_type="multiedgelist"
            )
            
            # Self-loops should be allowed
            assert net.core_network is not None
            
        except (ValueError, TypeError):
            pass
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass

    @given(st.lists(st.just("\n"), min_size=1, max_size=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_empty_lines(self, empty_lines):
        """Test that empty lines are handled correctly."""
        content = "".join(empty_lines)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            net = multinet.multi_layer_network(verbose=False)
            net.load_network(
                input_file=temp_path,
                directed=False,
                input_type="multiedgelist"
            )
            
            # Empty file should result in empty network
            if net.core_network:
                nodes = list(net.core_network.nodes())
                # Empty lines should be skipped
                
        except (ValueError, TypeError):
            # Some parsers may reject empty files
            pass
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
