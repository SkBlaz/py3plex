"""Seeded layer shuffles must be reproducible across Python hash seeds."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.nullmodels import layer_shuffle_model


PROGRAM = """
import json
import sys
from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import N
from py3plex.nullmodels import layer_shuffle_model
layers = json.loads(sys.argv[1])
seed = int(sys.argv[2])
network = multi_layer_network(directed=True, verbose=False)
network.add_nodes([{'source': str(i), 'type': layer} for i, layer in enumerate(layers)])
network.add_edges([{'source': str(i), 'source_type': layers[i], 'target': str(i+1), 'target_type': layers[i+1], 'weight': i+1} for i in range(len(layers)-1)])
if sys.argv[3] == 'dsl':
    shuffled = N.layer_shuffle().samples(1).seed(seed).execute(network)[0]
else:
    shuffled = layer_shuffle_model(network, seed=seed)
print(json.dumps({'nodes': sorted(shuffled.get_nodes()), 'edges': list(shuffled.core_network.edges(data=True))}, sort_keys=True))
"""


def snapshots_across_hash_seeds(layers, seed, frontend="function"):
    root = Path(__file__).resolve().parents[1]
    snapshots = []
    for hash_seed in ("0", "1", "42"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONPATH=str(root))
        output = subprocess.check_output(
            [sys.executable, "-c", PROGRAM, json.dumps(layers), str(seed), frontend],
            env=env,
            cwd=root,
            text=True,
            timeout=45,
        )
        snapshots.append(json.loads(output))
    return snapshots


@pytest.mark.parametrize(
    "layers",
    [
        ["social", "work", "transport", "hobby", "gene"],
        [0, "social", 7, "7", "work"],
    ],
)
@pytest.mark.parametrize("seed", [0, 42])
def test_layer_shuffle_matches_across_process_hash_seeds(layers, seed):
    snapshots = snapshots_across_hash_seeds(layers, seed)
    assert snapshots[0] == snapshots[1] == snapshots[2]


def test_layer_shuffle_dsl_matches_across_process_hash_seeds():
    snapshots = snapshots_across_hash_seeds([0, "social", 7, "7", "work"], 42, "dsl")
    assert snapshots[0] == snapshots[1] == snapshots[2]


@pytest.mark.parametrize("directed", [False, True])
def test_shuffle_preserves_mixed_layer_identities_and_weighted_structure(directed):
    layers = [0, "social", 7, "7", "work"]
    network = multi_layer_network(directed=directed, verbose=False)
    network.add_nodes(
        [{"source": str(i), "type": layer} for i, layer in enumerate(layers)]
    )
    network.add_edges(
        [
            {
                "source": str(i),
                "source_type": layers[i],
                "target": str(i + 1),
                "target_type": layers[i + 1],
                "weight": i + 1,
            }
            for i in range(len(layers) - 1)
        ]
    )
    original = network.core_network.copy()
    shuffled = layer_shuffle_model(network, seed=0).core_network
    assert shuffled.is_directed() == directed
    assert set(layer for _, layer in shuffled.nodes()) == set(layers)
    assert sorted(node for node, _ in shuffled.nodes()) == sorted(
        node for node, _ in original.nodes()
    )
    assert [
        (u[0], v[0], data["weight"]) for u, v, data in shuffled.edges(data=True)
    ] == [(u[0], v[0], data["weight"]) for u, v, data in original.edges(data=True)]
    assert list(network.core_network.edges(data=True)) == list(
        original.edges(data=True)
    )
    assert list(network.core_network.nodes()) == list(original.nodes())
