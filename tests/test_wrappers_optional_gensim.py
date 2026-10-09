"""The external Node2Vec wrapper does not require gensim to run its binary."""

import subprocess
import sys

import pytest


@pytest.mark.parametrize('entrypoint', ['benchmark', 'cli'])
def test_wrapper_runs_without_gensim(entrypoint):
    pytest.importorskip('sklearn')
    script = r'''
import importlib.abc
import sys
from unittest.mock import patch

class BlockGensim(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'gensim' or fullname.startswith('gensim.'):
            raise ModuleNotFoundError('gensim intentionally unavailable', name='gensim')

sys.meta_path.insert(0, BlockGensim())
from py3plex.wrappers import train_node2vec_embedding as wrapper
from py3plex.wrappers import benchmark_nodes

with patch.object(wrapper.os.path, 'isfile', return_value=True), \
     patch.object(wrapper.subprocess, 'run') as run:
    wrapper.call_node2vec_binary('in.edges', 'out.emb', binary='node2vec')
    assert run.call_count == 1

try:
    if sys.argv[1] == 'benchmark':
        benchmark_nodes.benchmark_node_classification('out.emb', None, None)
    else:
        sys.argv = ['scoring', '--emb', 'out.emb', '--network', 'labels.mat']
        benchmark_nodes.main()
except ModuleNotFoundError as exc:
    assert exc.name == 'gensim'
else:
    raise AssertionError('Classification must still request gensim')
'''
    result = subprocess.run(
        [sys.executable, '-c', script, entrypoint],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
