"""Fixed landmark seeds must survive process hash randomization."""

import json
import os
import subprocess
import sys
import textwrap


def test_seeded_closeness_is_identical_across_hash_seeds():
    script = textwrap.dedent('''
        import json
        import networkx as nx
        from py3plex.algorithms.centrality.approx_closeness import approximate_closeness_landmarks
        from py3plex.core import multinet
        from py3plex.dsl import Q

        output = {}
        for replicas in (False, True):
            nodes = [(f'node{i}', 'social') if replicas else f'node{i}' for i in range(12)]
            graph = nx.Graph()
            graph.add_nodes_from(nodes + ['isolated'])
            graph.add_edges_from(zip(nodes, nodes[1:]))
            graph.add_edge(nodes[1], nodes[4])
            values, errors = approximate_closeness_landmarks(
                graph, n_landmarks=5, seed=0, diagnostics=True
            )
            output[str(replicas)] = [[values[n], errors[n]] for n in graph]
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([[f'node{i}', 'social', f'node{i+1}', 'social', 1]
                           for i in range(11)], input_type='list')
        result = Q.nodes().compute('closeness_centrality', approx=True,
                                   n_landmarks=5, seed=0).execute(network)
        output['dsl'] = [result.attributes['closeness_centrality'][(f'node{i}', 'social')]
                         for i in range(12)]
        print(json.dumps(output, sort_keys=True))
    ''')
    outputs = []
    for hash_seed in ('1', '2', '99'):
        result = subprocess.run(
            [sys.executable, '-c', script],
            env={**os.environ, 'PYTHONHASHSEED': hash_seed},
            capture_output=True, text=True, check=True, timeout=40,
        )
        outputs.append(json.loads(result.stdout))
    assert outputs[0] == outputs[1] == outputs[2]
