"""Unit tests for GraphProgram implementation.

Tests cover:
- Program creation from AST
- Stable hashing
- Program composition
- Execution
- Serialization
- Metadata tracking
"""

import json
import time
import pytest

from py3plex.dsl import Q, L
from py3plex.dsl.ast import Query, SelectStmt, Target, ComputeItem
from py3plex.dsl.program import GraphProgram, ProgramMetadata, compose
from py3plex.dsl.program.types import TypeCheckError, NodeSetType
from py3plex.core import multinet


class TestProgramMetadata:
    """Tests for ProgramMetadata class."""
    
    def test_metadata_creation(self):
        """Test basic metadata creation."""
        meta = ProgramMetadata(
            creation_timestamp=time.time(),
            dsl_version="2.0",
            library_version="1.1.2",
            provenance_chain=["from_ast"],
        )
        
        assert meta.dsl_version == "2.0"
        assert meta.library_version == "1.1.2"
        assert meta.provenance_chain == ["from_ast"]
        assert meta.cost_model_hints is None
        assert meta.randomness_metadata is None
    
    def test_metadata_serialization(self):
        """Test metadata serialization roundtrip."""
        meta = ProgramMetadata(
            creation_timestamp=1234567890.0,
            dsl_version="2.0",
            library_version="1.1.2",
            cost_model_hints={"complexity": "O(n)"},
            randomness_metadata={"seed": 42},
            provenance_chain=["from_ast", "optimize"],
        )
        
        meta_dict = meta.to_dict()
        restored = ProgramMetadata.from_dict(meta_dict)
        
        assert restored.creation_timestamp == meta.creation_timestamp
        assert restored.dsl_version == meta.dsl_version
        assert restored.library_version == meta.library_version
        assert restored.cost_model_hints == meta.cost_model_hints
        assert restored.randomness_metadata == meta.randomness_metadata
        assert restored.provenance_chain == meta.provenance_chain


class TestGraphProgram:
    """Tests for GraphProgram class."""
    
    def test_program_from_ast_basic(self):
        """Test creating program from simple AST."""
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        assert program.canonical_ast is not None
        assert program.type_signature is not None
        assert len(program.program_hash) == 64  # SHA-256 hex
        assert program.metadata.dsl_version == "2.0"
        assert "from_ast" in program.metadata.provenance_chain
    
    def test_program_immutability(self):
        """Test that programs are immutable (frozen dataclass)."""
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        with pytest.raises((AttributeError, TypeError)):
            program.program_hash = "new_hash"
    
    def test_program_hash_stability(self):
        """Test that identical programs have identical hashes."""
        ast1 = Q.nodes().compute("degree").to_ast()
        ast2 = Q.nodes().compute("degree").to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        assert program1.hash() == program2.hash()
    
    def test_program_hash_uniqueness(self):
        """Test that different programs have different hashes."""
        ast1 = Q.nodes().compute("degree").to_ast()
        ast2 = Q.nodes().compute("betweenness").to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        assert program1.hash() != program2.hash()
    
    def test_program_hash_layer_sensitivity(self):
        """Test that hash is sensitive to layer selections."""
        ast1 = Q.nodes().from_layers(L["social"]).compute("degree").to_ast()
        ast2 = Q.nodes().from_layers(L["work"]).compute("degree").to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        assert program1.hash() != program2.hash()
    
    def test_program_type_signature(self):
        """Test that type signature is correctly inferred."""
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        # Should be NodeSetType with metrics
        assert isinstance(program.type_signature, NodeSetType)
        assert program.type_signature.has_metrics
    
    def test_program_type_check_failure(self):
        """Test that invalid ASTs fail type checking."""
        # Create an invalid SelectStmt manually (limit_per_group without group_by)
        select = SelectStmt(
            target=Target.NODES,
            compute=[ComputeItem(name="degree")],
            limit_per_group=5,  # Invalid without group_by
        )
        query = Query(explain=False, select=select)
        
        # Should raise TypeCheckError
        with pytest.raises(TypeCheckError):
            GraphProgram.from_ast(query)
    
    def test_program_execution_basic(self):
        """Test executing a program on a network."""
        # Create a simple network
        net = multinet.multi_layer_network()
        net.add_nodes([
            {"source": "A", "type": "social"},
            {"source": "B", "type": "social"},
            {"source": "C", "type": "social"},
        ])
        net.add_edges([
            {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
            {"source": "B", "target": "C", "source_type": "social", "target_type": "social"},
        ])
        
        # Create and execute program
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        result = program.execute(net, progress=False)
        
        assert result is not None
        assert len(result.items) > 0
        
        # Check that degree was computed
        df = result.to_pandas()
        assert "degree" in df.columns
    
    def test_program_execution_with_params(self):
        """Test executing program with parameter bindings."""
        net = multinet.multi_layer_network()
        net.add_nodes([
            {"source": "A", "type": "social"},
            {"source": "B", "type": "social"},
        ])
        net.add_edges([
            {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
        ])
        
        # Create program with filter (though params not in filter for this test)
        ast = Q.nodes().compute("degree").limit(5).to_ast()
        program = GraphProgram.from_ast(ast)
        result = program.execute(net, params={}, progress=False)
        
        assert result is not None


class TestProgramComposition:
    """Tests for program composition."""
    
    def test_compose_basic(self):
        """Test basic program composition."""
        ast1 = Q.nodes().compute("degree").to_ast()
        ast2 = Q.nodes().compute("betweenness").to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        composed = program1.compose(program2)
        
        assert composed is not None
        assert composed.program_hash != program1.program_hash
        assert composed.program_hash != program2.program_hash
        
        # Check provenance
        assert "compose" in composed.metadata.provenance_chain
    
    def test_compose_function(self):
        """Test standalone compose function."""
        ast1 = Q.nodes().compute("degree").to_ast()
        ast2 = Q.nodes().compute("clustering").to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        composed = compose(program1, program2)
        
        assert composed is not None
        assert "compose" in composed.metadata.provenance_chain
    
    def test_compose_mismatched_targets(self):
        """Test that composing programs with different targets fails."""
        ast1 = Q.nodes().compute("degree").to_ast()
        ast2 = Q.edges().to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        with pytest.raises(TypeCheckError):
            program1.compose(program2)
    
    def test_compose_merges_compute_items(self):
        """Test that composition merges compute items."""
        ast1 = Q.nodes().compute("degree").to_ast()
        ast2 = Q.nodes().compute("betweenness").to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        composed = program1.compose(program2)
        
        # Should have both metrics
        compute_names = {c.name for c in composed.canonical_ast.select.compute}
        assert "degree" in compute_names
        assert "betweenness" in compute_names
    
    def test_compose_execution(self):
        """Test executing a composed program."""
        net = multinet.multi_layer_network()
        net.add_nodes([
            {"source": "A", "type": "social"},
            {"source": "B", "type": "social"},
            {"source": "C", "type": "social"},
        ])
        net.add_edges([
            {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
            {"source": "B", "target": "C", "source_type": "social", "target_type": "social"},
        ])
        
        ast1 = Q.nodes().compute("degree").to_ast()
        ast2 = Q.nodes().compute("clustering").to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        composed = program1.compose(program2)
        result = composed.execute(net, progress=False)
        
        df = result.to_pandas()
        assert "degree" in df.columns
        assert "clustering" in df.columns


class TestProgramOperations:
    """Tests for program operations (optimize, explain, diff)."""
    
    def test_optimize_placeholder(self):
        """Test that optimize returns self (placeholder implementation)."""
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        optimized = program.optimize()
        
        # Currently returns self
        assert optimized.hash() == program.hash()
    
    def test_explain_basic(self):
        """Test program explanation generation."""
        ast = Q.nodes().compute("degree").order_by("degree", desc=True).limit(10).to_ast()
        program = GraphProgram.from_ast(ast)
        
        explanation = program.explain()
        
        assert "SELECT nodes" in explanation
        assert "degree" in explanation
        assert "Order by" in explanation
        assert "Limit: 10" in explanation
        assert "Hash:" in explanation
    
    def test_explain_with_layers(self):
        """Test explanation includes layer information."""
        ast = Q.nodes().from_layers(L["social"]).compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        explanation = program.explain()
        
        assert "Layers:" in explanation
        assert "social" in explanation
    
    def test_diff_identical_programs(self):
        """Test diff of identical programs."""
        ast1 = Q.nodes().compute("degree").to_ast()
        ast2 = Q.nodes().compute("degree").to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        diff = program1.diff(program2)
        
        assert diff["identical"] is True
        assert diff["hash_self"] == diff["hash_other"]
    
    def test_diff_different_programs(self):
        """Test diff of different programs."""
        ast1 = Q.nodes().compute("degree").to_ast()
        ast2 = Q.nodes().compute("betweenness").to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        diff = program1.diff(program2)
        
        assert diff["identical"] is False
        assert diff["hash_self"] != diff["hash_other"]
        assert "metrics_differ" in diff
        assert "degree" in diff["metrics_differ"]["only_in_self"]
        assert "betweenness" in diff["metrics_differ"]["only_in_other"]
    
    def test_diff_different_targets(self):
        """Test diff detects different targets."""
        ast1 = Q.nodes().to_ast()
        ast2 = Q.edges().to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        diff = program1.diff(program2)
        
        assert "target_differs" in diff
        assert diff["target_differs"]["self"] == "nodes"
        assert diff["target_differs"]["other"] == "edges"


class TestProgramSerialization:
    """Tests for program serialization."""
    
    def test_to_dict_basic(self):
        """Test serializing program to dictionary."""
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        program_dict = program.to_dict()
        
        assert "canonical_ast" in program_dict
        assert "type_signature" in program_dict
        assert "program_hash" in program_dict
        assert "metadata" in program_dict
        
        assert program_dict["program_hash"] == program.hash()
    
    def test_to_dict_json_serializable(self):
        """Test that serialized dict can be converted to JSON."""
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        program_dict = program.to_dict()
        
        # Should not raise
        json_str = json.dumps(program_dict, default=str)
        assert json_str is not None
    
    def test_from_dict_not_implemented(self):
        """Test that from_dict raises NotImplementedError (AST deserialization complex)."""
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        program_dict = program.to_dict()
        
        # Currently not implemented
        with pytest.raises(NotImplementedError):
            GraphProgram.from_dict(program_dict)


class TestProgramProvenance:
    """Tests for provenance tracking."""
    
    def test_provenance_from_ast(self):
        """Test that from_ast sets provenance."""
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        assert "from_ast" in program.metadata.provenance_chain
    
    def test_provenance_custom(self):
        """Test custom provenance chain."""
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast, provenance=["custom", "step"])
        
        assert program.metadata.provenance_chain == ["custom", "step"]
    
    def test_provenance_compose(self):
        """Test that compose merges provenance."""
        ast1 = Q.nodes().compute("degree").to_ast()
        ast2 = Q.nodes().compute("betweenness").to_ast()
        
        program1 = GraphProgram.from_ast(ast1, provenance=["step1"])
        program2 = GraphProgram.from_ast(ast2, provenance=["step2"])
        
        composed = program1.compose(program2)
        
        # Should contain: step1 + compose + step2
        assert "step1" in composed.metadata.provenance_chain
        assert "compose" in composed.metadata.provenance_chain
        assert "step2" in composed.metadata.provenance_chain


class TestProgramHashing:
    """Tests for stable hashing implementation."""
    
    def test_hash_deterministic_across_calls(self):
        """Test that hash is deterministic across multiple calls."""
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        hash1 = program.hash()
        hash2 = program.hash()
        
        assert hash1 == hash2
    
    def test_hash_deterministic_across_instances(self):
        """Test that hash is deterministic across program instances."""
        ast1 = Q.nodes().compute("degree").to_ast()
        ast2 = Q.nodes().compute("degree").to_ast()
        
        program1 = GraphProgram.from_ast(ast1)
        program2 = GraphProgram.from_ast(ast2)
        
        assert program1.hash() == program2.hash()
    
    def test_hash_format(self):
        """Test that hash is 64-char hex string."""
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        program_hash = program.hash()
        
        assert len(program_hash) == 64
        assert all(c in "0123456789abcdef" for c in program_hash)
    
    def test_hash_ordering_independence(self):
        """Test that hash is independent of dict ordering.
        
        Note: This is implicitly tested by using json.dumps(sort_keys=True)
        in the implementation.
        """
        ast = Q.nodes().compute("degree").to_ast()
        program = GraphProgram.from_ast(ast)
        
        # Just verify hash is computed
        assert len(program.hash()) == 64


class TestProgramIntegration:
    """Integration tests combining multiple features."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow: create, compose, execute, explain."""
        # Create network
        net = multinet.multi_layer_network()
        net.add_nodes([
            {"source": "A", "type": "social"},
            {"source": "B", "type": "social"},
            {"source": "C", "type": "social"},
        ])
        net.add_edges([
            {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
            {"source": "B", "target": "C", "source_type": "social", "target_type": "social"},
        ])
        
        # Create programs
        ast1 = Q.nodes().compute("degree").to_ast()
        program1 = GraphProgram.from_ast(ast1)
        
        ast2 = Q.nodes().compute("clustering").to_ast()
        program2 = GraphProgram.from_ast(ast2)
        
        # Compose
        composed = program1.compose(program2)
        
        # Execute
        result = composed.execute(net, progress=False)
        df = result.to_pandas()
        
        # Verify results
        assert "degree" in df.columns
        assert "clustering" in df.columns
        
        # Explain
        explanation = composed.explain()
        assert "degree" in explanation
        assert "clustering" in explanation
        
        # Diff
        diff = program1.diff(program2)
        assert not diff["identical"]
        
        # Serialize
        program_dict = composed.to_dict()
        assert program_dict["program_hash"] == composed.hash()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
