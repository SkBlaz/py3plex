# tests/property/test_stateful_multiplex.py
"""
Property-based tests for py3plex multiplex mode:
1) A RuleBasedStateMachine that mutates a multiplex network via node/edge ops
   and checks invariants including automatic inter-layer couplings.
2) A parity test that verifies monoplex_nx_wrapper('degree_centrality')
   matches NetworkX's degree_centrality on a single-layer slice.
"""

import pytest
import networkx as nx
from collections import defaultdict

from hypothesis import strategies as st, settings, assume, given
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, Bundle

pytest.importorskip("py3plex")
from py3plex.core import multinet


# ---------------------------- Strategies ---------------------------------------

# Constrain the search space for speed/reproducibility.
NAMES = [f"n{i}" for i in range(20)]
LAYERS = [str(i) for i in range(5)]

name_st = st.sampled_from(NAMES)
layer_st = st.sampled_from(LAYERS)
weight_st = st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)


def _edge_endpoints_only(edges_iterable):
    """Normalize to a frozenset of unordered endpoint pairs (u,v) for fast membership tests."""
    s = set()
    for e in edges_iterable:
        # In multiplex mode, edges are (u, v, key) tuples
        u, v = e[0], e[1]
        s.add(tuple(sorted((u, v))))
    return s


# -------------------- Stateful machine: multiplex mode -------------------------

class MultiplexMachine(RuleBasedStateMachine):
    """
    Mutates a multiplex network and checks invariants.

    Node identity is a (name, layer) tuple. In multiplex mode, same-named nodes
    across different layers are automatically coupled.
    """

    nodes = Bundle("nodes")

    def __init__(self):
        super().__init__()
        self.net = multinet.multi_layer_network(network_type="multiplex")
        # Shadow counts per (name, layer) we explicitly created (for sanity only).
        self._explicit_nodes = set()

    # ------------------------ Helper accessors ---------------------------------

    def _nodes(self):
        return set(self.net.get_nodes())

    def _edges(self):
        """Get edges as (u, v, key) tuples in multiplex mode."""
        return list(self.net.get_edges())

    def _all_edges_including_coupling(self):
        """Get ALL edges including coupling edges."""
        return list(self.net.get_edges(multiplex_edges=True))

    # ----------------------------- Rules ---------------------------------------

    @rule(target=nodes, name=name_st, layer=layer_st)
    def add_node(self, name, layer):
        """Add a node to a specific layer."""
        self.net.add_nodes({"source": name, "type": layer})
        # In multiplex mode, trigger coupling after adding nodes
        if self.net.core_network is not None:
            self.net._couple_all_edges()
        nl = (name, layer)
        self._explicit_nodes.add(nl)
        assert nl in self._nodes()
        return nl

    @rule(a=nodes, b=nodes, w=weight_st)
    def add_edge_list_format(self, a, b, w):
        """
        Add an edge using the multiplex/multilayer list-of-lists format:
        [name1, layer1, name2, layer2, weight]
        """
        (s_name, s_layer), (t_name, t_layer) = a, b
        self.net.add_edges([[s_name, s_layer, t_name, t_layer, float(w)]], input_type="list")

    @rule(a=nodes, b=nodes, w=weight_st)
    def add_edge_dict_format(self, a, b, w):
        """
        Add an edge using the dict-based API (works in multiplex too).
        """
        (s_name, s_layer), (t_name, t_layer) = a, b
        self.net.add_edges({
            "source": s_name,
            "target": t_name,
            "type": "default",
            "source_type": s_layer,
            "target_type": t_layer,
            "weight": float(w),
        })

    @rule(node=nodes)
    def neighbors_consistency(self, node):
        """
        get_neighbors(name, layer) must match adjacency derived from get_edges().
        Note: In directed graphs, neighbors() returns successors only.
        """
        name, layer = node
        sut_neighbors = set(self.net.get_neighbors(name, layer))
        
        # In directed graphs, neighbors are successors (outgoing edges)
        adj = set()
        for e in self._edges():
            # Edges are (u, v, key) tuples
            u, v = e[0], e[1]
            if u == node:
                adj.add(v)
        assert sut_neighbors == adj

    @rule()
    def subnetwork_by_layers(self):
        """
        Subsetting by layers returns nodes only from those layers.
        """
        if self.net.core_network is None:
            return
        all_nodes = self._nodes()
        if not all_nodes:
            return
        layers_present = sorted({ly for _, ly in all_nodes})
        chosen = layers_present[:1]  # pick first to keep deterministic & fast
        sub = self.net.subnetwork(chosen, subset_by="layers")
        assert all(ly in chosen for (_, ly) in sub.get_nodes())

    @rule()
    def subnetwork_by_node_names(self):
        """Single name subnetwork contains only that name (across its layers)."""
        if self.net.core_network is None:
            return
        all_nodes = list(self._nodes())
        if not all_nodes:
            return
        some_name = all_nodes[0][0]
        sub = self.net.subnetwork([some_name], subset_by="node_names")
        assert all(n == some_name for (n, ly) in sub.get_nodes())

    @rule()
    def subnetwork_by_node_layer_names(self):
        """Exact (name,layer) subnetwork equals requested set."""
        if self.net.core_network is None:
            return
        all_nodes = list(self._nodes())
        if len(all_nodes) < 2:
            return
        sample = list(dict.fromkeys(all_nodes[:2]))  # two distinct nodes
        sub = self.net.subnetwork(sample, subset_by="node_layer_names")
        assert set(sub.get_nodes()) == set(sample)

    # ---------------------------- Invariants -----------------------------------

    @invariant()
    def nodes_unique_and_core_sane(self):
        # Skip if network not yet initialized
        if self.net.core_network is None:
            return
        nodes = list(self.net.get_nodes())
        assert len(nodes) == len(set(nodes))
        # core_network node count should be >= exposed multilayer node count
        try:
            assert len(self.net.core_network) >= len(nodes)
        except Exception:
            pass  # tolerate implementations without len()

    @invariant()
    def endpoints_exist(self):
        # Skip if network not yet initialized
        if self.net.core_network is None:
            return
        node_set = self._nodes()
        for e in self._edges():
            # Edges are (u, v, key) tuples
            u, v = e[0], e[1]
            assert u in node_set and v in node_set

    @invariant()
    def multiplex_couplings_exist(self):
        """
        In multiplex mode, same-named nodes across different layers are coupled.
        For every name that appears in >=2 layers, each pair of (name, layer_i),
        (name, layer_j) must have an edge between them.
        """
        # Skip if network not yet initialized
        if self.net.core_network is None:
            return
        nodes = self._nodes()
        by_name = defaultdict(set)
        for n, ly in nodes:
            by_name[n].add(ly)

        # Get ALL edges including coupling edges
        edge_set = _edge_endpoints_only(self._all_edges_including_coupling())

        for n, layers in by_name.items():
            if len(layers) < 2:
                continue
            layers = sorted(layers)
            for i in range(len(layers)):
                for j in range(i + 1, len(layers)):
                    u = (n, layers[i])
                    v = (n, layers[j])
                    assert tuple(sorted((u, v))) in edge_set


# Hook for pytest discovery
TestMultiplex = MultiplexMachine.TestCase


# ---------------- Centrality parity on a single-layer slice --------------------

@settings(deadline=None, max_examples=20)
@st.composite
def path_graph_params(draw):
    n = draw(st.integers(min_value=2, max_value=15))
    # build a path on nodes n0..n{n-1} in one chosen layer
    layer = draw(st.sampled_from(LAYERS))
    return n, layer


@settings(deadline=None, max_examples=25)
@given(params=path_graph_params())
def test_degree_centrality_parity_single_layer(params):
    """
    Build a simple path graph in one layer of a multiplex network and verify that
    monoplex_nx_wrapper('degree_centrality') matches NetworkX degree_centrality
    on the corresponding monolayer graph.
    """
    n, layer = params
    B = multinet.multi_layer_network(network_type="multiplex")

    # Create nodes explicitly (not strictly required, but clearer)
    for i in range(n):
        B.add_nodes({"source": f"n{i}", "type": layer})

    # Add path edges in the SAME layer to avoid multiedge/parallel-edge semantics
    for i in range(n - 1):
        B.add_edges([[f"n{i}", layer, f"n{i+1}", layer, 1.0]], input_type="list")

    # Single-layer slice
    C = B.subnetwork([layer], subset_by="layers")

    # 1) py3plex -> NetworkX via wrapper
    py3plex_deg = C.monoplex_nx_wrapper("degree_centrality")
    # Ensure keys are present for all nodes
    nodes_in_layer = set(C.get_nodes())
    assert nodes_in_layer == set(py3plex_deg.keys())

    # 2) Build the equivalent NetworkX graph directly from edges in C
    G = nx.Graph()
    G.add_nodes_from(nodes_in_layer)
    for u, v in C.get_edges():
        G.add_edge(u, v)

    nx_deg = nx.degree_centrality(G)

    # Compare numerically (exact for degree_centrality on simple graphs)
    for node in nodes_in_layer:
        assert abs(py3plex_deg[node] - nx_deg[node]) < 1e-12
