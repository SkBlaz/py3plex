"""Example demonstrating compiler-quality error reporting in py3plex DSL v2.

This example shows:
1. Structured error messages with stages and suggestions
2. "Did you mean?" suggestions for typos
3. Invalid join key validation
4. Error message formatting and context
"""

from py3plex.core import multinet
from py3plex.dsl import (
    Q,
    DSLCompileError,
    InvalidJoinKeyError,
    ComputedFieldMisuseError,
    UnknownMeasureError,
)

# Create a sample network
network = multinet.multi_layer_network(directed=False)

nodes = [
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'social'},
]
network.add_nodes(nodes)

edges = [
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
]
network.add_edges(edges)

print("=" * 70)
print("Example 1: Invalid Join Keys with Helpful Error Message")
print("=" * 70)

try:
    result = (
        Q.nodes()
        .compute("degree")
        .join(Q.nodes(), on=["invalid_key", "layer"], how="inner")
        .execute(network)
    )
except InvalidJoinKeyError as e:
    print("✗ Error caught!")
    print(f"\nFormatted error message:")
    print("-" * 70)
    print(str(e))
    print("-" * 70)
    print(f"\nStructured error details:")
    print(f"  Stage: {e.stage}")
    print(f"  Missing keys: {e.missing_keys}")
    print(f"  Side: {e.side}")
    print(f"  Available fields: {e.available_fields}")
    print(f"\n✓ Error provides:")
    print(f"    - What went wrong (missing key)")
    print(f"    - Where it happened (join stage)")
    print(f"    - What's available (field list)")
    print(f"    - How to fix it (see suggestion)")

print("\n" + "=" * 70)
print("Example 2: Misspelled Measure with 'Did You Mean?' Suggestion")
print("=" * 70)

try:
    # Typo: "betweennes" instead of "betweenness_centrality"
    result = Q.nodes().compute("betweennes").execute(network)
except UnknownMeasureError as e:
    print("✗ Error caught!")
    print(f"\nError message:")
    print(f"  {str(e).split('Known measures:')[0].strip()}")
    print(f"\n✓ Error includes:")
    print(f"    - Unknown measure: {e.measure}")
    if e.suggestion:
        print(f"    - Suggestion: Did you mean '{e.suggestion}'?")
    print(f"    - List of valid measures available")

print("\n" + "=" * 70)
print("Example 3: DSLCompileError with Complete Diagnostics")
print("=" * 70)

# Create a structured compile error (simulated)
error = DSLCompileError(
    message="Field 'pagerank' is computed but not available at this stage",
    stage="where",
    field="pagerank",
    suggestion="Add .compute('pagerank') before .where()",
    ast_summary="Q.nodes().where(pagerank__gt=0.1)",
    expected="available field",
    actual="computed field"
)

print("Example of a fully-structured compile error:")
print("-" * 70)
print(str(error))
print("-" * 70)

print(f"\n✓ This error provides:")
print(f"    - Clear message about what's wrong")
print(f"    - Stage where the error occurred: {error.stage}")
print(f"    - Field that caused the issue: {error.field}")
print(f"    - Actionable suggestion: {error.suggestion}")
print(f"    - AST summary for context: {error.ast_summary}")
print(f"    - Expected vs actual: {error.expected} vs {error.actual}")

print("\n" + "=" * 70)
print("Example 4: Error Determinism")
print("=" * 70)

# Same error should be raised consistently
errors = []
for i in range(3):
    try:
        Q.nodes().join(Q.nodes(), on=["nonexistent"], how="inner").execute(network)
    except InvalidJoinKeyError as e:
        errors.append(str(e))

if len(set(errors)) == 1:
    print("✓ Error is deterministic - same message every time")
    print(f"  Executed {len(errors)} times, got identical error each time")
else:
    print("✗ Errors differ across executions (unexpected)")

print("\n" + "=" * 70)
print("Example 5: Error Context and Formatting")
print("=" * 70)

# Show how different errors follow consistent formatting
print("All DSL errors follow a consistent format with:")
print("  1. Clear error message")
print("  2. Stage identification")
print("  3. Contextual information")
print("  4. Actionable suggestions")
print("\nExample errors:")

errors_to_show = [
    DSLCompileError(
        message="Cannot filter after grouping without aggregation",
        stage="where",
        suggestion="Use aggregated form (e.g., degree__mean) or filter before grouping"
    ),
    DSLCompileError(
        message="Join key 'user_id' not found",
        stage="join",
        suggestion="Available keys: id, layer, degree"
    ),
    DSLCompileError(
        message="Unknown field 'degre' in filter",
        stage="where",
        suggestion="Did you mean 'degree'?"
    ),
]

for i, err in enumerate(errors_to_show, 1):
    print(f"\n{i}. {str(err).split('Suggestion:')[0].strip()}")
    if err.suggestion:
        print(f"   Suggestion: {err.suggestion}")

print("\n" + "=" * 70)
print("Example 6: Early Error Detection")
print("=" * 70)

print("Errors are detected as early as possible:")
print("  - Join type validation: at builder creation ✓")
print("  - Schema validation: at execution time ✓")
print("  - AST validation: during compilation ✓")

try:
    # Invalid join type caught immediately
    Q.nodes().join(Q.nodes(), on=["id"], how="invalid_type")
except ValueError as e:
    print(f"\n✓ Invalid join type caught early: {str(e)[:50]}...")

print("\n" + "=" * 70)
print("Example 7: Comparing Error Quality")
print("=" * 70)

print("Before (typical error):")
print("  KeyError: 'nonexistent_key'")
print("  ❌ No context, no suggestion, not actionable")

print("\nAfter (compiler-quality error):")
invalid_key_error = InvalidJoinKeyError(
    missing_keys=["nonexistent_key"],
    available_fields=["id", "layer", "degree"],
    side="left",
    ast_summary="Q.nodes().join(...)"
)
print(f"  {str(invalid_key_error)[:100]}...")
print("  ✓ Clear context, available options, actionable")

print("\n" + "=" * 70)
print("Key Takeaways")
print("=" * 70)
print("""
1. Errors are EARLY - caught at compile/plan time when possible
2. Errors are PRECISE - point to exact stage and field
3. Errors are ACTIONABLE - include suggestions and alternatives
4. Errors are DETERMINISTIC - same input = same error
5. Errors are COMPILER-QUALITY - feel like TypeScript/Rust errors

This makes py3plex DSL feel like a real language with a compiler,
not just a runtime wrapper around NetworkX.
""")

print("All error examples completed successfully!")
