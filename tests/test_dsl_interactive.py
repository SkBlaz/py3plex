import unittest
import networkx as nx
from py3plex.core import multinet
from py3plex.dsl import Q, L

class TestDSLInteractiveQuerying(unittest.TestCase):

    def setUp(self):
        # Create a sample multilayer network for testing
        self.net = multinet.multi_layer_network(directed=False)
        self.net.add_nodes([
            {'source': 'A', 'type': 'social'},
            {'source': 'B', 'type': 'social'},
            {'source': 'C', 'type': 'social'},
            {'source': 'A', 'type': 'work'},
            {'source': 'C', 'type': 'work'}
        ])
        self.net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
            {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
            {'source': 'A', 'target': 'C', 'source_type': 'work', 'target_type': 'work'},
        ])


    def test_query_builder_is_mutable_and_chainable(self):
        query = Q.nodes().from_layers(L["social"])
        query_id = id(query)
        query.where(source="A")

        # QueryBuilder mutates in place and preserves identity
        self.assertEqual(query_id, id(query))
        self.assertIsNotNone(query._select.where)

    def test_interactive_query_chain(self):
        # Build independent queries to avoid in-place mutations colliding
        social_nodes_query = Q.nodes().from_layers(L["social"])
        df1 = social_nodes_query.execute(self.net).to_pandas()
        self.assertEqual(len(df1), 3)
        assert set(df1["layer"]) == {"social"}
        assert set(df1["id"]) == {"A", "B", "C"}

        # Second query: compute degree in social layer and ensure column exists
        df2 = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .execute(self.net)
            .to_pandas()
        )
        self.assertIn("degree", df2.columns)
        self.assertEqual(len(df2), 3)

        # The original query should be unaffected
        df3 = Q.nodes().execute(self.net).to_pandas()
        self.assertEqual(len(df3), 5)

if __name__ == '__main__':
    unittest.main()
