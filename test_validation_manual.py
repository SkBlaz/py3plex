#!/usr/bin/env python3
"""Manual verification of AST validation system.

This script demonstrates the validation system in action.
"""

import sys

# Test 1: Import all validation components
print("Test 1: Importing validation components...")
try:
    from py3plex.dsl.validation import (
        ValidationIssue,
        ValidationResult,
        DSLValidationError,
        NetworkSchema,
        EngineCapabilities,
        validate_ast,
        infer_schema,
        format_validation_report,
        DSLVAL_FIELD_UNKNOWN,
        DSLVAL_UQ_INVALID_PARAMS,
    )
    print("✓ All imports successful\n")
except Exception as e:
    print(f"✗ Import failed: {e}\n")
    sys.exit(1)

# Test 2: Create ValidationIssue
print("Test 2: Creating ValidationIssue...")
try:
    issue = ValidationIssue(
        code="TEST001",
        severity="error",
        message="Test error",
        path="where",
        hint="Fix this",
    )
    assert issue.code == "TEST001"
    assert issue.severity == "error"
    print(f"✓ ValidationIssue created: {issue.code}\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    sys.exit(1)

# Test 3: Create ValidationResult
print("Test 3: Creating ValidationResult...")
try:
    result = ValidationResult()
    assert result.ok
    result.add_error(issue)
    assert not result.ok
    assert len(result.errors) == 1
    print(f"✓ ValidationResult working: ok={result.ok}, errors={len(result.errors)}\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    sys.exit(1)

# Test 4: Format validation report
print("Test 4: Formatting validation report...")
try:
    report = format_validation_report(result)
    assert "TEST001" in report
    assert "Test error" in report
    print(f"✓ Report formatted:\n{report}\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    sys.exit(1)

# Test 5: DSLValidationError
print("Test 5: Testing DSLValidationError...")
try:
    error = DSLValidationError(issues=[issue])
    error_str = str(error)
    assert "TEST001" in error_str
    print(f"✓ DSLValidationError formatted:\n{error_str}\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    sys.exit(1)

# Test 6: NetworkSchema
print("Test 6: Creating NetworkSchema...")
try:
    schema = NetworkSchema()
    node_fields = schema.get_all_node_fields()
    assert 'degree' in node_fields
    assert 'layer' in node_fields
    print(f"✓ NetworkSchema created with {len(node_fields)} node fields\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    sys.exit(1)

# Test 7: EngineCapabilities
print("Test 7: Creating EngineCapabilities...")
try:
    caps = EngineCapabilities()
    assert 'degree' in caps.supported_measures
    assert 'mean' in caps.supported_aggregations
    print(f"✓ EngineCapabilities created with {len(caps.supported_measures)} measures\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    sys.exit(1)

# Test 8: Test Q.validate() method exists
print("Test 8: Checking Q.validate() method...")
try:
    from py3plex.dsl import Q
    q = Q.nodes()
    assert hasattr(q, 'validate')
    assert callable(q.validate)
    print("✓ Q.validate() method exists\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    sys.exit(1)

# Test 9: Test error codes are defined
print("Test 9: Checking error codes...")
try:
    assert DSLVAL_FIELD_UNKNOWN is not None
    assert DSLVAL_UQ_INVALID_PARAMS is not None
    print(f"✓ Error codes defined: {DSLVAL_FIELD_UNKNOWN}, {DSLVAL_UQ_INVALID_PARAMS}\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    sys.exit(1)

# Test 10: Test ValidationResult.to_dict()
print("Test 10: Testing ValidationResult.to_dict()...")
try:
    result2 = ValidationResult()
    result2.add_error(ValidationIssue(
        code="TEST002",
        severity="error",
        message="Another test",
    ))
    d = result2.to_dict()
    assert d["ok"] is False
    assert len(d["errors"]) == 1
    assert d["errors"][0]["code"] == "TEST002"
    print(f"✓ ValidationResult.to_dict() works\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    sys.exit(1)

print("="*60)
print("✅ ALL MANUAL TESTS PASSED!")
print("="*60)
print("\nValidation system is working correctly.")
print("Ready for integration testing with actual networks.")
