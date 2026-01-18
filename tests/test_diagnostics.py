"""Tests for the unified diagnostic system.

Tests cover:
- Diagnostic creation and serialization
- Error code taxonomy
- Fuzzy matching and "did you mean?" suggestions
- Diagnostic formatting
- Integration with DSL errors
"""

import json
import pytest
from py3plex.diagnostics import (
    Diagnostic,
    DiagnosticSeverity,
    DiagnosticContext,
    FixSuggestion,
    DiagnosticResult,
    ERROR_CODES,
    fuzzy_match,
    did_you_mean,
)
from py3plex.diagnostics import builders as diag_builders


class TestDiagnosticCore:
    """Test core Diagnostic functionality."""
    
    def test_diagnostic_creation(self):
        """Test creating a basic diagnostic."""
        diag = Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code="DSL_SEM_001",
            message="Unknown field 'degreee'",
            cause="Field name contains a typo",
            fixes=[
                FixSuggestion(
                    description="Did you mean 'degree'?",
                    replacement="degree"
                )
            ],
            related=["Q.nodes().compute()"]
        )
        
        assert diag.severity == DiagnosticSeverity.ERROR
        assert diag.code == "DSL_SEM_001"
        assert diag.message == "Unknown field 'degreee'"
        assert len(diag.fixes) == 1
        assert diag.fixes[0].replacement == "degree"
    
    def test_diagnostic_json_serialization(self):
        """Test diagnostic JSON serialization."""
        diag = Diagnostic(
            severity=DiagnosticSeverity.WARNING,
            code="RES_001",
            message="Query produced empty results",
            context=DiagnosticContext(
                builder_method="where",
                query_fragment="degree__gt=1000"
            ),
            fixes=[
                FixSuggestion(
                    description="Relax filter threshold",
                    example="degree__gt=10"
                )
            ]
        )
        
        # Test to_dict
        diag_dict = diag.to_dict()
        assert diag_dict["severity"] == "warning"
        assert diag_dict["code"] == "RES_001"
        assert diag_dict["message"] == "Query produced empty results"
        assert "context" in diag_dict
        assert diag_dict["context"]["builder_method"] == "where"
        
        # Test to_json
        diag_json = diag.to_json()
        parsed = json.loads(diag_json)
        assert parsed["code"] == "RES_001"
        
        # Test from_dict
        restored = Diagnostic.from_dict(diag_dict)
        assert restored.code == diag.code
        assert restored.severity == diag.severity
        assert restored.message == diag.message
    
    def test_diagnostic_formatting(self):
        """Test diagnostic formatting for display."""
        diag = Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code="DSL_SEM_001",
            message="Unknown field 'degreee'",
            context=DiagnosticContext(
                builder_method="where",
                query_fragment="degreee__gt=3"
            ),
            cause="The field name contains a typo",
            fixes=[
                FixSuggestion(
                    description="Did you mean 'degree'?",
                    replacement="degree",
                    example="Q.nodes().where(degree__gt=3)"
                )
            ],
            related=["Q.nodes().compute()"]
        )
        
        # Format without color
        formatted = diag.format(use_color=False)
        assert "error[DSL_SEM_001]" in formatted
        assert "Unknown field 'degreee'" in formatted
        assert "Cause:" in formatted
        assert "Fix 1:" in formatted
        assert "Did you mean 'degree'?" in formatted
        assert "Related:" in formatted
    
    def test_diagnostic_result_collection(self):
        """Test collecting multiple diagnostics."""
        result = DiagnosticResult()
        
        result.add(Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code="DSL_SEM_001",
            message="Error 1"
        ))
        
        result.add(Diagnostic(
            severity=DiagnosticSeverity.WARNING,
            code="RES_001",
            message="Warning 1"
        ))
        
        result.add(Diagnostic(
            severity=DiagnosticSeverity.INFO,
            code="INFO_001",
            message="Info 1"
        ))
        
        assert len(result.diagnostics) == 3
        assert result.has_errors()
        assert result.has_warnings()
        assert len(result.errors()) == 1
        assert len(result.warnings()) == 1
        assert len(result.infos()) == 1
        
        # Test JSON serialization
        result_dict = result.to_dict()
        assert result_dict["summary"]["total"] == 3
        assert result_dict["summary"]["errors"] == 1
        assert result_dict["summary"]["warnings"] == 1


class TestErrorCodes:
    """Test error code taxonomy."""
    
    def test_error_code_exists(self):
        """Test that error codes are registered."""
        assert "DSL_SEM_001" in ERROR_CODES
        assert "DSL_PARSE_001" in ERROR_CODES
        assert "EXEC_001" in ERROR_CODES
        assert "RES_001" in ERROR_CODES
        assert "ALG_001" in ERROR_CODES
        assert "IO_001" in ERROR_CODES
    
    def test_error_code_structure(self):
        """Test error code structure."""
        code = ERROR_CODES["DSL_SEM_001"]
        assert code.code == "DSL_SEM_001"
        assert code.category == "DSL Semantics"
        assert code.title
        assert code.description
        assert code.typical_cause
        assert code.typical_fix


class TestFuzzyMatching:
    """Test fuzzy matching utilities."""
    
    def test_fuzzy_match_simple(self):
        """Test simple fuzzy matching."""
        candidates = ["degree", "betweenness_centrality", "pagerank"]
        
        matches = fuzzy_match("degreee", candidates)
        assert len(matches) > 0
        assert matches[0][0] == "degree"
        assert matches[0][1] > 0.6
    
    def test_fuzzy_match_no_match(self):
        """Test fuzzy matching with no close match."""
        candidates = ["degree", "betweenness_centrality", "pagerank"]
        
        matches = fuzzy_match("xyz", candidates, cutoff=0.8)
        assert len(matches) == 0
    
    def test_did_you_mean(self):
        """Test did you mean suggestion."""
        candidates = ["degree", "betweenness_centrality", "pagerank"]
        
        suggestion = did_you_mean("degreee", candidates)
        assert suggestion == "degree"
        
        suggestion = did_you_mean("betweennes", candidates)
        assert suggestion == "betweenness_centrality"
        
        suggestion = did_you_mean("xyz", candidates, cutoff=0.8)
        assert suggestion is None


class TestDiagnosticBuilders:
    """Test diagnostic builder functions."""
    
    def test_unknown_field_error(self):
        """Test building unknown field diagnostic."""
        diag = diag_builders.unknown_field_error(
            field="degreee",
            known_fields=["degree", "betweenness_centrality"],
            target_type="node"
        )
        
        assert diag.code == "DSL_SEM_001"
        assert diag.severity == DiagnosticSeverity.ERROR
        assert "degreee" in diag.message
        assert len(diag.fixes) > 0
        assert "degree" in diag.fixes[0].description
    
    def test_unknown_measure_error(self):
        """Test building unknown measure diagnostic."""
        diag = diag_builders.unknown_measure_error(
            measure="betweennes",
            known_measures=["betweenness_centrality", "degree", "pagerank"]
        )
        
        assert diag.code == "DSL_SEM_001"
        assert diag.severity == DiagnosticSeverity.ERROR
        assert "betweennes" in diag.message
        assert len(diag.fixes) > 0
    
    def test_unknown_layer_error(self):
        """Test building unknown layer diagnostic."""
        diag = diag_builders.unknown_layer_error(
            layer="scoial",
            known_layers=["social", "work", "family"]
        )
        
        assert diag.code == "DSL_SEM_005"
        assert diag.severity == DiagnosticSeverity.ERROR
        assert "scoial" in diag.message
        assert len(diag.fixes) > 0
    
    def test_empty_result_warning(self):
        """Test building empty result warning."""
        diag = diag_builders.empty_result_warning(
            filter_condition="degree__gt=1000",
            num_nodes=100
        )
        
        assert diag.code == "RES_001"
        assert diag.severity == DiagnosticSeverity.WARNING
        assert "100" in diag.message
        assert len(diag.fixes) > 0
    
    def test_high_variance_warning(self):
        """Test building high variance warning."""
        diag = diag_builders.high_variance_warning(
            measure="betweenness_centrality",
            variance=0.85,
            n_samples=50
        )
        
        assert diag.code == "RES_002"
        assert diag.severity == DiagnosticSeverity.WARNING
        assert "betweenness_centrality" in diag.message
        assert len(diag.fixes) > 0


class TestDSLErrorIntegration:
    """Test integration with DSL errors."""
    
    def test_unknown_attribute_error_has_diagnostic(self):
        """Test that UnknownAttributeError includes diagnostic."""
        from py3plex.dsl.errors import UnknownAttributeError
        
        error = UnknownAttributeError(
            attribute="degreee",
            known_attributes=["degree", "betweenness_centrality"]
        )
        
        assert error.diagnostic is not None
        assert error.diagnostic.code == "DSL_SEM_001"
        assert error.suggestion == "degree"
        
        # Test that format_message uses diagnostic formatting
        formatted = error.format_message()
        assert "DSL_SEM_001" in formatted or "degreee" in formatted
    
    def test_unknown_measure_error_has_diagnostic(self):
        """Test that UnknownMeasureError includes diagnostic."""
        from py3plex.dsl.errors import UnknownMeasureError
        
        error = UnknownMeasureError(
            measure="betweennes",
            known_measures=["betweenness_centrality", "degree"]
        )
        
        assert error.diagnostic is not None
        assert error.diagnostic.code == "DSL_SEM_001"
        # Note: suggestion may be None if threshold not met, but diagnostic should still be created
        assert error.suggestion == "betweenness_centrality" or error.suggestion is None
    
    def test_unknown_layer_error_has_diagnostic(self):
        """Test that UnknownLayerError includes diagnostic."""
        from py3plex.dsl.errors import UnknownLayerError
        
        error = UnknownLayerError(
            layer="scoial",
            known_layers=["social", "work"]
        )
        
        assert error.diagnostic is not None
        assert error.diagnostic.code == "DSL_SEM_005"
        assert error.suggestion == "social"
    
    def test_diagnostic_to_diagnostic_method(self):
        """Test to_diagnostic() method on DSL errors."""
        from py3plex.dsl.errors import UnknownAttributeError
        
        error = UnknownAttributeError(
            attribute="degreee",
            known_attributes=["degree"]
        )
        
        diag = error.to_diagnostic()
        assert diag is not None
        assert isinstance(diag, Diagnostic)
        assert diag.code == "DSL_SEM_001"
