"""Tests for algorithm requirements and compatibility checking.

This module tests the requirements system that makes multilayer/multiplex
algorithm assumptions explicit and enforceable.
"""

import pytest
import networkx as nx

from py3plex.core import multinet
from py3plex.requirements import (
    AlgoRequirements,
    NetworkCapabilities,
    check_compat,
    requires,
    AlgorithmCompatibilityError,
)
from py3plex.diagnostics.core import DiagnosticSeverity


class TestNetworkCapabilities:
    """Test network capabilities computation."""
    
    def test_single_layer_capabilities(self):
        """Test capabilities for a single-layer network."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        caps = net.capabilities()
        
        assert caps.mode == "single"
        assert caps.directed == False
        assert caps.layer_count == 1
        assert caps.replica_model == "none"
        assert caps.interlayer_coupling == "none"
    
    def test_multilayer_capabilities(self):
        """Test capabilities for a multilayer network."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'A', 'target': 'C', 'source_type': 'layer2', 'target_type': 'layer2'},
        ])
        
        caps = net.capabilities()
        
        assert caps.mode == "multilayer"
        assert caps.layer_count == 2
        assert caps.replica_model in ("partial", "strict")
        assert caps.interlayer_coupling == "none"
    
    def test_multiplex_with_identity_coupling(self):
        """Test capabilities for multiplex with identity coupling."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False)
        
        # Add nodes in both layers (same base nodes)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'A', 'type': 'layer2'},
            {'source': 'B', 'type': 'layer2'},
        ])
        
        # Add intralayer edges
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2'},
        ])
        
        # Add identity interlayer edges
        net.add_edges([
            {'source': 'A', 'target': 'A', 'source_type': 'layer1', 'target_type': 'layer2'},
            {'source': 'B', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer2'},
        ])
        
        caps = net.capabilities()
        
        assert caps.layer_count == 2
        assert caps.replica_model == "strict"
        assert caps.interlayer_coupling in ("identity", "both")
    
    def test_weighted_network_capabilities(self):
        """Test weight domain detection."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.5},
            {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 2.3},
        ])
        
        caps = net.capabilities()
        
        assert caps.weighted == True
        assert caps.weight_domain == "positive"
    
    def test_capabilities_caching(self):
        """Test that capabilities are cached."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        caps1 = net.capabilities()
        caps2 = net.capabilities()
        
        # Should be the same object (cached)
        assert caps1 is caps2
        
        # Force recompute
        caps3 = net.capabilities(force_recompute=True)
        assert caps3 is not caps1


class TestCompatibilityChecking:
    """Test compatibility checking logic."""
    
    def test_compatible_network(self):
        """Test that compatible networks produce no errors."""
        caps = NetworkCapabilities(
            mode="multilayer",
            replica_model="partial",
            interlayer_coupling="none",
            directed=False,
            weighted=False,
            layer_count=2,
            total_edges=10,
        )
        
        reqs = AlgoRequirements(
            allowed_modes=("multilayer", "multiplex"),
            replica_model=("partial", "strict"),
            supports_directed=True,
            supports_undirected=True,
        )
        
        diagnostics = check_compat(caps, reqs)
        
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.ERROR]
        assert len(errors) == 0
    
    def test_mode_incompatibility(self):
        """Test mode incompatibility detection."""
        caps = NetworkCapabilities(
            mode="single",
            replica_model="none",
            interlayer_coupling="none",
            directed=False,
            weighted=False,
            layer_count=1,
            total_edges=5,
        )
        
        reqs = AlgoRequirements(
            allowed_modes=("multiplex",),
            replica_model=("strict",),
        )
        
        diagnostics = check_compat(caps, reqs, algorithm_name="test_algo")
        
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.ERROR]
        assert len(errors) >= 1
        
        # Check for mode error
        mode_errors = [d for d in errors if d.code == "ALGO_REQ_001"]
        assert len(mode_errors) == 1
        assert "single" in mode_errors[0].message
        assert "multiplex" in mode_errors[0].message
    
    def test_replica_model_incompatibility(self):
        """Test replica model incompatibility detection."""
        caps = NetworkCapabilities(
            mode="multilayer",
            replica_model="partial",
            interlayer_coupling="none",
            directed=False,
            weighted=False,
            layer_count=2,
            total_edges=10,
        )
        
        reqs = AlgoRequirements(
            allowed_modes=("multilayer", "multiplex"),
            replica_model=("strict",),
        )
        
        diagnostics = check_compat(caps, reqs)
        
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.ERROR]
        replica_errors = [d for d in errors if d.code == "ALGO_REQ_002"]
        assert len(replica_errors) == 1
    
    def test_weight_requirement_check(self):
        """Test weight requirement checking."""
        caps = NetworkCapabilities(
            mode="multilayer",
            replica_model="partial",
            interlayer_coupling="none",
            directed=False,
            weighted=False,
            layer_count=2,
            total_edges=10,
        )
        
        reqs = AlgoRequirements(
            requires_edge_weights=True,
        )
        
        diagnostics = check_compat(caps, reqs)
        
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.ERROR]
        weight_errors = [d for d in errors if d.code == "ALGO_REQ_004"]
        assert len(weight_errors) == 1
    
    def test_seed_warning(self):
        """Test seed warning generation."""
        caps = NetworkCapabilities(
            mode="multilayer",
            replica_model="partial",
            interlayer_coupling="none",
            directed=False,
            weighted=False,
            layer_count=2,
            total_edges=10,
        )
        
        reqs = AlgoRequirements(
            uses_randomness=True,
            requires_seed_for_repro=False,
        )
        
        diagnostics = check_compat(caps, reqs, seed=None)
        
        warnings = [d for d in diagnostics if d.severity == DiagnosticSeverity.WARNING]
        seed_warnings = [d for d in warnings if d.code == "ALGO_REQ_007"]
        assert len(seed_warnings) == 1


class TestRequiresDecorator:
    """Test @requires decorator functionality."""
    
    def test_decorator_attaches_requirements(self):
        """Test that decorator attaches requirements attribute."""
        reqs = AlgoRequirements(
            allowed_modes=("multilayer",),
        )
        
        @requires(reqs)
        def my_algorithm(network):
            return {"result": "success"}
        
        assert hasattr(my_algorithm, 'requirements')
        assert my_algorithm.requirements is reqs
    
    def test_decorator_raises_on_incompatibility(self):
        """Test that decorator raises AlgorithmCompatibilityError."""
        reqs = AlgoRequirements(
            allowed_modes=("multiplex",),
            replica_model=("strict",),
        )
        
        @requires(reqs)
        def my_algorithm(network):
            return {"result": "success"}
        
        # Create a single-layer network (incompatible)
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        with pytest.raises(AlgorithmCompatibilityError) as exc_info:
            my_algorithm(net)
        
        assert exc_info.value.algo_name == "my_algorithm"
        assert len(exc_info.value.diagnostics) > 0
    
    def test_decorator_allows_compatible_network(self):
        """Test that decorator allows compatible networks."""
        reqs = AlgoRequirements(
            allowed_modes=("single", "multilayer"),
            replica_model=("none", "partial"),
        )
        
        @requires(reqs)
        def my_algorithm(network):
            return {"result": "success"}
        
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        # Should not raise
        result = my_algorithm(net)
        assert result["result"] == "success"
    
    def test_decorator_fallback_no_capabilities(self):
        """Test that decorator falls back gracefully for networks without capabilities()."""
        reqs = AlgoRequirements(
            allowed_modes=("single",),
        )
        
        @requires(reqs)
        def my_algorithm(network):
            return {"result": "success"}
        
        # Use a plain NetworkX graph (no capabilities method)
        G = nx.Graph()
        G.add_edge('A', 'B')
        
        # Should not raise, just run normally
        result = my_algorithm(G)
        assert result["result"] == "success"


class TestAlgorithmCompatibilityError:
    """Test AlgorithmCompatibilityError exception."""
    
    def test_error_message_format(self):
        """Test error message formatting."""
        from py3plex.diagnostics.core import Diagnostic, DiagnosticSeverity, DiagnosticContext, FixSuggestion
        
        diagnostics = [
            Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                code="ALGO_REQ_001",
                message="Network mode incompatible",
                context=DiagnosticContext(additional={"required": ["multiplex"], "got": "single"}),
                fixes=[FixSuggestion(description="Convert to multiplex")],
            ),
        ]
        
        error = AlgorithmCompatibilityError(diagnostics, algo_name="test_algo")
        
        assert "test_algo" in str(error)
        assert "incompatible" in str(error).lower()
    
    def test_error_to_dict(self):
        """Test JSON serialization."""
        from py3plex.diagnostics.core import Diagnostic, DiagnosticSeverity, DiagnosticContext
        
        diagnostics = [
            Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                code="ALGO_REQ_001",
                message="Test error",
                context=DiagnosticContext(additional={}),
            ),
        ]
        
        error = AlgorithmCompatibilityError(diagnostics, algo_name="test_algo")
        error_dict = error.to_dict()
        
        assert error_dict["algorithm"] == "test_algo"
        assert "diagnostics" in error_dict
        assert len(error_dict["diagnostics"]) == 1
        assert error_dict["summary"]["errors"] == 1


class TestCrossEntrypointParity:
    """Test that diagnostics are consistent across entry points."""
    
    def test_direct_call_vs_dsl_parity(self):
        """Test that direct algorithm call and DSL produce same diagnostic code."""
        # This is a placeholder for actual cross-entrypoint tests
        # In a full implementation, we would:
        # 1. Call leiden_multilayer() directly on an incompatible network
        # 2. Call via DSL: Q.communities(...).execute(net)
        # 3. Assert both raise errors with the same diagnostic codes
        pass


class TestDiagnosticJSONStability:
    """Test that diagnostic JSON format is stable."""
    
    def test_diagnostic_json_format(self):
        """Test stable JSON serialization."""
        caps = NetworkCapabilities(
            mode="single",
            replica_model="none",
            interlayer_coupling="none",
            directed=False,
            weighted=False,
            layer_count=1,
            total_edges=5,
        )
        
        reqs = AlgoRequirements(
            allowed_modes=("multiplex",),
        )
        
        diagnostics = check_compat(caps, reqs, algorithm_name="test_algo")
        
        # Convert to dict
        diag_dicts = [d.to_dict() for d in diagnostics]
        
        # Check structure
        assert len(diag_dicts) > 0
        first_diag = diag_dicts[0]
        
        assert "severity" in first_diag
        assert "code" in first_diag
        assert "message" in first_diag
        assert "context" in first_diag
        assert "fixes" in first_diag
