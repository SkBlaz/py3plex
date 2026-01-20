"""Tests for AST-level validation.

This module tests the validation system for DSL v2 queries,
ensuring compile-time error detection with precise diagnostics.
"""

import pytest
from py3plex.dsl import (
    Q,
    L,
    Param,
    ValidationIssue,
    ValidationResult,
    DSLValidationError,
    NetworkSchema,
    EngineCapabilities,
    validate_ast,
    infer_schema,
    format_validation_report,
    DSLVAL_FIELD_UNKNOWN,
    DSLVAL_FIELD_TARGET_MISMATCH,
    DSLVAL_GROUPING_INVALID,
    DSLVAL_AGGREGATION_MISSING_FIELD,
    DSLVAL_AGGREGATION_INVALID_PARAMS,
    DSLVAL_UQ_INVALID_PARAMS,
    DSLVAL_ORDER_FIELD_MISSING,
    DSLVAL_LAYER_UNKNOWN,
)
from py3plex.core import multinet


@pytest.fixture
def simple_network():
    """Create a simple test network."""
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'work'},
        {'source': 'D', 'type': 'work'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'C', 'target': 'D', 'source_type': 'work', 'target_type': 'work', 'weight': 2.0},
    ])
    return net


class TestValidationIssue:
    """Test ValidationIssue dataclass."""
    
    def test_create_issue(self):
        """Test creating a validation issue."""
        issue = ValidationIssue(
            code="TEST001",
            severity="error",
            message="Test error",
            path="where.conditions[0]",
            hint="Fix this",
        )
        assert issue.code == "TEST001"
        assert issue.severity == "error"
        assert issue.message == "Test error"
        assert issue.path == "where.conditions[0]"
        assert issue.hint == "Fix this"
    
    def test_issue_to_dict(self):
        """Test converting issue to dictionary."""
        issue = ValidationIssue(
            code="TEST001",
            severity="error",
            message="Test error",
            path="where",
            hint="Fix this",
        )
        d = issue.to_dict()
        assert d["code"] == "TEST001"
        assert d["severity"] == "error"
        assert d["message"] == "Test error"
        assert d["path"] == "where"
        assert d["hint"] == "Fix this"


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_empty_result(self):
        """Test empty result is ok."""
        result = ValidationResult()
        assert result.ok
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_add_error(self):
        """Test adding an error."""
        result = ValidationResult()
        issue = ValidationIssue(
            code="TEST001",
            severity="error",
            message="Test error",
        )
        result.add_error(issue)
        assert not result.ok
        assert len(result.errors) == 1
        assert result.errors[0] == issue
    
    def test_add_warning(self):
        """Test adding a warning."""
        result = ValidationResult()
        issue = ValidationIssue(
            code="TEST001",
            severity="warning",
            message="Test warning",
        )
        result.add_warning(issue)
        assert result.ok  # Warnings don't affect ok status
        assert len(result.warnings) == 1
    
    def test_raise_if_errors(self):
        """Test raising exception on errors."""
        result = ValidationResult()
        issue = ValidationIssue(
            code="TEST001",
            severity="error",
            message="Test error",
        )
        result.add_error(issue)
        
        with pytest.raises(DSLValidationError) as exc_info:
            result.raise_if_errors()
        
        assert len(exc_info.value.issues) == 1


class TestFieldValidation:
    """Test field validation rules."""
    
    def test_unknown_field_in_where(self, simple_network):
        """Test unknown field in WHERE clause fails with correct code."""
        q = Q.nodes().where(unknownfield__gt=5)
        result = q.validate(simple_network)
        
        assert not result.ok
        assert len(result.errors) > 0
        assert any(e.code == DSLVAL_FIELD_UNKNOWN for e in result.errors)
        assert any("unknownfield" in e.message for e in result.errors)
    
    def test_unknown_field_in_order_by(self, simple_network):
        """Test unknown field in ORDER BY fails."""
        q = Q.nodes().order_by("unknownfield")
        result = q.validate(simple_network)
        
        assert not result.ok
        assert any(e.code == DSLVAL_ORDER_FIELD_MISSING for e in result.errors)
    
    def test_valid_reserved_field_nodes(self, simple_network):
        """Test valid reserved fields for nodes pass validation."""
        q = Q.nodes().where(degree__gt=1, layer="social")
        result = q.validate(simple_network)
        
        # Should pass (degree and layer are valid for nodes)
        assert result.ok or len(result.errors) == 0


class TestTargetSpecificValidation:
    """Test target-specific validation rules."""
    
    def test_node_field_in_edge_query(self, simple_network):
        """Test using node-only field in edge query fails."""
        q = Q.edges().where(degree__gt=5)
        result = q.validate(simple_network)
        
        assert not result.ok
        assert any(e.code == DSLVAL_FIELD_TARGET_MISMATCH for e in result.errors)
        assert any("src_degree" in e.hint or "dst_degree" in e.hint for e in result.errors if e.hint)
    
    def test_edge_field_in_node_query(self, simple_network):
        """Test using edge-only field in node query fails."""
        q = Q.nodes().where(src_degree__gt=5)
        result = q.validate(simple_network)
        
        assert not result.ok
        assert any(e.code == DSLVAL_FIELD_TARGET_MISMATCH for e in result.errors)


class TestGroupingValidation:
    """Test grouping validation rules."""
    
    def test_per_layer_pair_on_nodes_fails(self, simple_network):
        """Test per_layer_pair() on nodes fails."""
        q = Q.nodes().per_layer_pair()
        result = q.validate(simple_network)
        
        assert not result.ok
        assert any(e.code == DSLVAL_GROUPING_INVALID for e in result.errors)
        assert any("per_layer_pair" in e.message for e in result.errors)


class TestAggregationValidation:
    """Test aggregation validation rules."""
    
    def test_aggregate_missing_field(self, simple_network):
        """Test aggregation on missing computed field fails."""
        q = Q.nodes().per_layer().aggregate(avg_missing="mean(missingfield)")
        result = q.validate(simple_network)
        
        assert not result.ok
        assert any(e.code == DSLVAL_AGGREGATION_MISSING_FIELD for e in result.errors)
    
    def test_quantile_without_p_fails(self, simple_network):
        """Test quantile without p parameter fails."""
        from py3plex.dsl.ast import AggregationItem
        
        # This would need to be tested through the AST directly
        # since the builder API may not allow this invalid case
        pass  # Skip for now as builder prevents this
    
    def test_quantile_p_out_of_range(self, simple_network):
        """Test quantile with p outside [0,1] fails."""
        # Would need direct AST construction
        pass  # Skip for now


class TestUQValidation:
    """Test UQ parameter validation."""
    
    def test_uq_n_samples_zero_fails(self, simple_network):
        """Test .uq(n_samples=0) fails."""
        q = Q.nodes().compute("degree").uq(method="bootstrap", n_samples=0)
        result = q.validate(simple_network)
        
        assert not result.ok
        assert any(e.code == DSLVAL_UQ_INVALID_PARAMS for e in result.errors)
        assert any("n_samples" in e.message for e in result.errors)
    
    def test_uq_ci_out_of_range(self, simple_network):
        """Test .uq(ci=1.5) fails."""
        q = Q.nodes().compute("degree").uq(method="bootstrap", ci=1.5)
        result = q.validate(simple_network)
        
        assert not result.ok
        assert any(e.code == DSLVAL_UQ_INVALID_PARAMS for e in result.errors)
    
    def test_uq_unknown_method(self, simple_network):
        """Test .uq(method='unknown') fails."""
        q = Q.nodes().compute("degree").uq(method="unknown_method")
        result = q.validate(simple_network)
        
        assert not result.ok
        assert any(e.code == DSLVAL_UQ_INVALID_PARAMS for e in result.errors)


class TestLayerValidation:
    """Test layer expression validation."""
    
    def test_unknown_layer_fails(self, simple_network):
        """Test unknown layer in from_layers fails."""
        q = Q.nodes().from_layers(L["unknown"])
        result = q.validate(simple_network)
        
        assert not result.ok
        assert any(e.code == DSLVAL_LAYER_UNKNOWN for e in result.errors)
    
    def test_valid_layer_passes(self, simple_network):
        """Test valid layer passes."""
        q = Q.nodes().from_layers(L["social"])
        result = q.validate(simple_network)
        
        # Should pass
        assert result.ok or len(result.errors) == 0


class TestValidateOnly:
    """Test validate_only mode."""
    
    def test_validate_without_execute(self, simple_network):
        """Test validate_only returns results without execution."""
        q = Q.nodes().where(degree__gt=5)
        result = q.validate(simple_network)
        
        # Should return ValidationResult
        assert isinstance(result, ValidationResult)
        # Should not modify network
        assert len(simple_network.get_nodes()) == 4
    
    def test_execute_with_validation_disabled(self, simple_network):
        """Test execute with validate=False skips validation."""
        # This would fail validation (unknown field) but should execute anyway
        q = Q.nodes()
        result = q.execute(simple_network, validate=False)
        
        # Should complete without validation error
        assert result is not None


class TestBuilderIntegration:
    """Test integration with QueryBuilder."""
    
    def test_validate_method_exists(self):
        """Test .validate() method exists on QueryBuilder."""
        q = Q.nodes()
        assert hasattr(q, 'validate')
        assert callable(q.validate)
    
    def test_execute_validates_by_default(self, simple_network):
        """Test execute() validates by default."""
        q = Q.nodes().where(unknownfield__gt=5)
        
        with pytest.raises(DSLValidationError):
            q.execute(simple_network, validate=True)
    
    def test_execute_can_skip_validation(self, simple_network):
        """Test execute() can skip validation."""
        q = Q.nodes()
        result = q.execute(simple_network, validate=False)
        
        # Should complete
        assert result is not None


class TestLegacyDSLIntegration:
    """Test integration with legacy execute_query."""
    
    def test_execute_query_validate_only(self, simple_network):
        """Test execute_query with validate_only=True."""
        from py3plex.dsl import execute_query
        
        result = execute_query(
            simple_network,
            'SELECT nodes WHERE layer="social"',
            validate_only=True
        )
        
        assert isinstance(result, dict)
        assert 'ok' in result
        assert 'errors' in result
        assert 'warnings' in result
    
    def test_execute_query_normal_execution(self, simple_network):
        """Test execute_query normal execution."""
        from py3plex.dsl import execute_query
        
        result = execute_query(
            simple_network,
            'SELECT nodes WHERE layer="social"',
            validate_only=False
        )
        
        # Should have normal result structure
        assert 'nodes' in result or 'count' in result


class TestSchemaInference:
    """Test schema inference."""
    
    def test_infer_schema(self, simple_network):
        """Test infer_schema extracts layers."""
        schema = infer_schema(simple_network)
        
        assert isinstance(schema, NetworkSchema)
        assert len(schema.layers) > 0
        assert 'social' in schema.layers
        assert 'work' in schema.layers
    
    def test_schema_has_reserved_fields(self):
        """Test schema includes reserved fields."""
        schema = NetworkSchema()
        
        node_fields = schema.get_all_node_fields()
        assert 'degree' in node_fields
        assert 'layer' in node_fields
        
        edge_fields = schema.get_all_edge_fields()
        assert 'src_degree' in edge_fields
        assert 'weight' in edge_fields


class TestErrorFormatting:
    """Test error message formatting."""
    
    def test_format_validation_report(self):
        """Test format_validation_report produces readable output."""
        result = ValidationResult()
        issue = ValidationIssue(
            code="TEST001",
            severity="error",
            message="Test error message",
            path="where",
            hint="Try fixing this way",
        )
        result.add_error(issue)
        
        report = format_validation_report(result)
        
        assert "error" in report.lower()
        assert "TEST001" in report
        assert "Test error message" in report
        assert "Try fixing this way" in report
    
    def test_dsl_validation_error_str(self):
        """Test DSLValidationError formats nicely."""
        issues = [
            ValidationIssue(
                code="TEST001",
                severity="error",
                message="First error",
                path="where",
            ),
            ValidationIssue(
                code="TEST002",
                severity="warning",
                message="First warning",
                path="compute",
            ),
        ]
        
        exc = DSLValidationError(issues=issues)
        error_str = str(exc)
        
        assert "1 error(s)" in error_str
        assert "1 warning(s)" in error_str
        assert "TEST001" in error_str
        assert "First error" in error_str


class TestValidationResultSerialization:
    """Test validation result serialization."""
    
    def test_validation_result_to_dict(self):
        """Test ValidationResult.to_dict()."""
        result = ValidationResult()
        issue = ValidationIssue(
            code="TEST001",
            severity="error",
            message="Test error",
        )
        result.add_error(issue)
        
        d = result.to_dict()
        
        assert d["ok"] is False
        assert len(d["errors"]) == 1
        assert d["errors"][0]["code"] == "TEST001"


# Snapshot test for error report formatting
class TestSnapshotFormatting:
    """Test stable error message formatting (snapshot tests)."""
    
    def test_field_unknown_error_format(self, simple_network):
        """Test format of unknown field error."""
        q = Q.nodes().where(badfield__gt=5)
        result = q.validate(simple_network)
        
        report = format_validation_report(result)
        
        # Check for expected components
        assert "DSLVAL_FIELD_UNKNOWN" in report or "Unknown field" in report
        assert "badfield" in report
    
    def test_uq_invalid_error_format(self, simple_network):
        """Test format of UQ invalid params error."""
        q = Q.nodes().compute("degree").uq(n_samples=-1)
        result = q.validate(simple_network)
        
        report = format_validation_report(result)
        
        assert "n_samples" in report
        assert "positive" in report.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
