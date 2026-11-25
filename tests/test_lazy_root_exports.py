

def test_root_import_defers_dependencies_and_preserves_exports():
    import subprocess
    import sys

    code = """
import sys
import py3plex
assert not {'matplotlib.pyplot', 'numpy', 'pandas', 'sklearn'} & sys.modules.keys()
assert set(py3plex.__all__) <= set(dir(py3plex))
from py3plex import *
from py3plex.core.multinet import multi_layer_network as original
assert multi_layer_network is original
assert py3plex.dsl.execute_query is py3plex.execute_query
"""
    subprocess.run([sys.executable, "-c", code], check=True)
