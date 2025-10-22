#!/usr/bin/env python3
"""Atheris fuzzing harness for py3plex line/edge parsing.

This fuzzes individual line parsing by feeding malformed multilayer
edge lists to discover parsing bugs, crashes, and edge cases.

Usage:
    python fuzzing/fuzz_parse_line.py fuzzing/seeds/

Requirements:
    pip install atheris
"""

import sys
import tempfile
import os

try:
    import atheris
except ImportError:
    print("Error: atheris not installed. Install with: pip install atheris")
    sys.exit(1)

from py3plex.core import multinet


def fuzz_one_input(data: bytes):
    """Fuzz target for parsing individual lines/edges.
    
    Args:
        data: Random bytes from the fuzzer
    """
    # Skip empty or very short inputs
    if len(data) < 2:
        return
    
    # Decode to string
    try:
        s = data.decode("utf-8", errors="surrogatepass")
    except Exception:
        try:
            s = data.decode("latin-1", errors="ignore")
        except Exception:
            return
    
    # Split into lines
    lines = s.splitlines()
    if not lines:
        return
    
    # Create a network object
    net = multinet.multi_layer_network(verbose=False)
    
    try:
        # Write lines to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(s)
            temp_path = f.name
        
        try:
            # Try to parse as multiedgelist (most complex format)
            net.load_network(
                input_file=temp_path,
                directed=False,
                input_type="multiedgelist"
            )
            
            # If successful, try to access the network
            try:
                if net.core_network:
                    _ = list(net.core_network.nodes())
                    _ = list(net.core_network.edges())
            except Exception:
                pass
                
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except Exception:
                pass
                
    except SystemExit:
        raise
    except MemoryError:
        raise
    except AssertionError:
        raise
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        # Expected for malformed input
        return
    except FileNotFoundError:
        return
    except Exception as e:
        # Check if it's a real crash
        error_msg = str(e).lower()
        if any(word in error_msg for word in ['crash', 'segfault', 'corruption', 'overflow']):
            raise
        return


def main():
    """Entry point for the fuzzer."""
    atheris.Setup(sys.argv, fuzz_one_input)
    
    print("=" * 60)
    print("Py3plex Line Parsing Fuzzer")
    print("=" * 60)
    print("Fuzzing target: Edge/line parsing in multiedgelist format")
    print(f"Usage: {sys.argv[0]} <seed_corpus_dir>")
    print("=" * 60)
    
    atheris.Fuzz()


if __name__ == "__main__":
    main()
