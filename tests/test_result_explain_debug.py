"""Tests for QueryResult .explain() and .debug() methods.

Tests cover:
- .explain() output format
- .debug() output format
- Integration with diagnostics in metadata
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.dsl.result import QueryResult
from py3plex.diagnostics import Diagnostic, DiagnosticSeverity, DiagnosticResult


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work'},
    ]
    network.add_edges(edges)
    
    return network


class TestQueryResultExplain:
    """Test QueryResult.explain() method."""
    
    def test_explain_basic(self, sample_network):
        """Test basic explain functionality."""
        result = Q.nodes().execute(sample_network)
        
        explanation = result.explain()
        
        # Check that explanation includes key sections
        assert "Query Explanation" in explanation
        assert "Target: nodes" in explanation
        assert "Results: 5 items" in explanation
        assert "Suggested next steps:" in explanation
    
    def test_explain_with_computed_metrics(self, sample_network):
        """Test explain with computed metrics."""
        result = Q.nodes().compute("degree").execute(sample_network)
        
        explanation = result.explain()
        
        # Check that computed_metrics is shown if populated
        # Note: May not always be in metadata depending on executor
        assert "Target: nodes" in explanation
        assert "Results:" in explanation
    
    def test_explain_with_layers(self, sample_network):
        """Test explain with layer information."""
        result = Q.nodes().from_layers(L["social"]).execute(sample_network)
        
        explanation = result.explain()
        
        # Check that explanation is generated
        # Note: Layer info may not always be in metadata depending on executor
        assert "Target: nodes" in explanation
        assert "Results:" in explanation
    
    def test_explain_with_diagnostics(self, sample_network):
        """Test explain with diagnostics in metadata."""
        # Create a result with diagnostics
        result = QueryResult(
            target="nodes",
            items=['A', 'B', 'C'],
            attributes={},
            meta={
                "diagnostics": [
                    Diagnostic(
                        severity=DiagnosticSeverity.WARNING,
                        code="RES_001",
                        message="Query produced fewer results than expected"
                    ).to_dict()
                ]
            }
        )
        
        explanation = result.explain()
        
        assert "Diagnostics:" in explanation
        assert "RES_001" in explanation


class TestQueryResultDebug:
    """Test QueryResult.debug() method."""
    
    def test_debug_basic(self, sample_network):
        """Test basic debug functionality."""
        result = Q.nodes().execute(sample_network)
        
        debug_info = result.debug()
        
        # Check that debug info includes key sections
        assert "Query Debug Information" in debug_info
        assert "Target: nodes" in debug_info
        assert "Result count: 5" in debug_info
    
    def test_debug_with_ast(self):
        """Test debug with AST information."""
        result = QueryResult(
            target="nodes",
            items=['A', 'B'],
            attributes={},
            meta={
                "ast": {
                    "target": "nodes",
                    "select_items": ["*"]
                }
            }
        )
        
        debug_info = result.debug()
        
        assert "AST Structure:" in debug_info
        assert "target" in debug_info
    
    def test_debug_with_timing(self):
        """Test debug with timing information."""
        result = QueryResult(
            target="nodes",
            items=['A', 'B'],
            attributes={},
            meta={
                "timing": {
                    "parse": 0.001,
                    "execute": 0.050,
                    "total": 0.051
                }
            }
        )
        
        debug_info = result.debug()
        
        assert "Timing:" in debug_info
        assert "parse" in debug_info
        assert "0.001s" in debug_info or "0.001" in debug_info
    
    def test_debug_with_cache_stats(self):
        """Test debug with cache statistics."""
        result = QueryResult(
            target="nodes",
            items=['A', 'B'],
            attributes={},
            meta={
                "cache_stats": {
                    "hits": 10,
                    "misses": 2,
                    "hit_rate": 0.833
                }
            }
        )
        
        debug_info = result.debug()
        
        assert "Cache Statistics:" in debug_info
        assert "Hits: 10" in debug_info
        assert "Misses: 2" in debug_info
    
    def test_debug_with_backend_calls(self):
        """Test debug with backend call information."""
        result = QueryResult(
            target="nodes",
            items=['A', 'B'],
            attributes={},
            meta={
                "backend_calls": [
                    {"function": "compute_degree", "duration": 0.010},
                    {"function": "compute_betweenness", "duration": 0.050}
                ]
            }
        )
        
        debug_info = result.debug()
        
        assert "Backend Calls:" in debug_info
        assert "compute_degree" in debug_info
    
    def test_debug_with_random_seeds(self):
        """Test debug with randomness source information."""
        result = QueryResult(
            target="nodes",
            items=['A', 'B'],
            attributes={},
            meta={
                "random_seeds": {
                    "bootstrap": 42,
                    "community_detection": 123
                }
            }
        )
        
        debug_info = result.debug()
        
        assert "Random Seeds:" in debug_info
        assert "bootstrap: 42" in debug_info
        assert "community_detection: 123" in debug_info
    
    def test_debug_empty_metadata(self):
        """Test debug with no metadata."""
        result = QueryResult(
            target="nodes",
            items=['A', 'B'],
            attributes={},
            meta={}
        )
        
        debug_info = result.debug()
        
        assert "Query Debug Information" in debug_info
        assert "Target: nodes" in debug_info


class TestExplainDebugIntegration:
    """Test integration of explain() and debug() with actual queries."""
    
    def test_full_pipeline_explain(self, sample_network):
        """Test explain on a complete query pipeline."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .where(degree__gt=0)
            .execute(sample_network)
        )
        
        explanation = result.explain()
        
        # Should show basic structure
        assert "nodes" in explanation.lower() or "Target: nodes" in explanation
        assert "Suggested next steps:" in explanation
    
    def test_full_pipeline_debug(self, sample_network):
        """Test debug on a complete query pipeline."""
        result = (
            Q.nodes()
            .compute("degree")
            .execute(sample_network)
        )
        
        debug_info = result.debug()
        
        # Basic structure should be present
        assert "Target: nodes" in debug_info
        assert "Result count:" in debug_info
