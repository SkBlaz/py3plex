#!/usr/bin/env python3
"""Atheris fuzzing harness for py3plex network loading.

This fuzzes the main network loading path (load_network) by feeding it
various input formats and malformed data to discover crashes, exceptions,
and memory errors.

Usage:
    python fuzzing/fuzz_load_network.py fuzzing/seeds/

Requirements:
    pip install atheris
"""

import sys
import io
import traceback

try:
    import atheris
except ImportError:
    print("Error: atheris not installed. Install with: pip install atheris")
    sys.exit(1)

# Import the target API from py3plex
from py3plex.core import multinet

# Input types to test - these are the various formats load_network supports
INPUT_TYPES = [
    "multiedgelist",
    "edgelist",
    "gpickle",
    "gml",
]


def fuzz_one_input(data: bytes):
    """Fuzz target function called by atheris.
    
    Args:
        data: Random bytes from the fuzzer
    """
    # Skip empty inputs
    if len(data) == 0:
        return
    
    # Decode bytes to string with error handling
    try:
        s = data.decode("utf-8", errors="surrogatepass")
    except Exception:
        try:
            s = data.decode("latin-1", errors="ignore")
        except Exception:
            return
    
    # Create lines from the input
    lines = s.splitlines()
    if not lines:
        return
    
    # Determine input type based on data content (deterministic mapping)
    # This allows the fuzzer to explore different parsing paths
    itype = INPUT_TYPES[sum(data[:1]) % len(INPUT_TYPES)] if data else "multiedgelist"
    
    # Determine label delimiter based on data
    label_delim = "---" if len(data) % 2 == 0 else ":::"
    
    # Create network container
    net = multinet.multi_layer_network(verbose=False)
    
    try:
        # For most input types, we need to write to a temporary file
        # since many parsers expect a file path rather than a stream
        import tempfile
        import os
        
        # Create a temporary file with the fuzzed data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(s)
            temp_path = f.name
        
        try:
            # Call load_network - this is the main fuzzing target
            net.load_network(
                input_file=temp_path,
                directed=False,
                input_type=itype,
                label_delimiter=label_delim
            )
            
            # If loading succeeded, try to exercise more code paths
            try:
                # Try to get basic statistics
                nodes = list(net.get_nodes()) if hasattr(net, 'get_nodes') else []
                edges = list(net.get_edges()) if hasattr(net, 'get_edges') else []
            except Exception:
                # Expected for malformed networks
                pass
            
            # Try to get layers
            try:
                layers = net.get_layers() if hasattr(net, 'get_layers') else []
            except Exception:
                # Expected for malformed networks
                pass
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception:
                pass
                
    except SystemExit:
        # Re-raise SystemExit to avoid catching it
        raise
    except MemoryError:
        # Re-raise memory errors as they indicate real issues
        raise
    except AssertionError:
        # Re-raise assertions as they indicate logic errors
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        # These are expected for malformed input - library should handle gracefully
        return
    except FileNotFoundError:
        # Expected for missing files
        return
    except Exception as e:
        # For unexpected exceptions, check if they're from library or critical
        # Re-raise if it looks like a crash (not a validation error)
        error_msg = str(e).lower()
        if any(word in error_msg for word in ['crash', 'segfault', 'corruption', 'overflow']):
            raise
        # Otherwise, it's likely a validation error - let it pass
        return


def main():
    """Entry point for the fuzzer."""
    # Setup atheris with command-line arguments
    atheris.Setup(sys.argv, fuzz_one_input)
    
    print("=" * 60)
    print("Py3plex Network Loading Fuzzer")
    print("=" * 60)
    print(f"Fuzzing target: multinet.load_network()")
    print(f"Input types: {', '.join(INPUT_TYPES)}")
    print(f"Usage: {sys.argv[0]} <seed_corpus_dir>")
    print("=" * 60)
    
    # Start fuzzing
    atheris.Fuzz()


if __name__ == "__main__":
    main()
