"""Example demonstrating the diagnostic system and error reporting in py3plex.

This example shows:
1. Diagnostic creation and formatting
2. Error recovery with "did you mean?" suggestions
3. QueryResult.explain() and .debug() methods
4. LLM-friendly error JSON export
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.dsl.errors import UnknownMeasureError, UnknownLayerError
from py3plex.diagnostics import Diagnostic, DiagnosticSeverity, FixSuggestion

print("=" * 70)
print("Example 1: Understanding Diagnostic Objects")
print("=" * 70)

# Create a sample diagnostic
diag = Diagnostic(
    severity=DiagnosticSeverity.ERROR,
    code="DSL_SEM_001",
    message="Unknown field 'degreee'",
    cause="The field name contains a typo",
    fixes=[
        FixSuggestion(
            description="Did you mean 'degree'?",
            replacement="degree",
            example="Q.nodes().where(degree__gt=3)"
        )
    ],
    related=["Q.nodes().compute()", "Available fields: degree, betweenness_centrality"]
)

print("\nDiagnostic object created:")
print(diag)

print("\n\nJSON export (LLM-friendly):")
print(diag.to_json())

print("\n" + "=" * 70)
print("Example 2: Automatic Error Recovery with DSL")
print("=" * 70)

# Create a sample network
network = multinet.multi_layer_network(directed=False)

nodes = [
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'social'},
    {'source': 'David', 'type': 'work'},
]
network.add_nodes(nodes)

edges = [
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'David', 'target': 'Alice', 'source_type': 'work', 'target_type': 'work'},
]
network.add_edges(edges)

# Try with a typo - will get helpful error
print("\nAttempting query with typo: .compute('betweennes')")
try:
    result = Q.nodes().compute("betweennes").execute(network)
except UnknownMeasureError as e:
    print("\nFAIL Error caught!")
    print(f"Error message: {str(e).split('Known measures:')[0].strip()}")
    
    # Get diagnostic
    if e.diagnostic:
        print("\nStructured diagnostic available:")
        print(f"  Code: {e.diagnostic.code}")
        print(f"  Severity: {e.diagnostic.severity.value}")
        
        if e.diagnostic.fixes:
            print(f"\nSuggested fixes:")
            for i, fix in enumerate(e.diagnostic.fixes, 1):
                print(f"  {i}. {fix.description}")
                if fix.replacement:
                    print(f"     Replacement: {fix.replacement}")
    
    # Auto-correct based on suggestion
    if e.suggestion:
        print(f"\nOK Auto-correcting to '{e.suggestion}'...")
        result = Q.nodes().compute(e.suggestion).execute(network)
        print(f"OK Success! Computed {e.suggestion} for {len(result.items)} nodes")

print("\n" + "=" * 70)
print("Example 3: Layer Name Typo Recovery")
print("=" * 70)

print("\nAttempting query with layer typo: L['scoial']")
try:
    result = Q.nodes().from_layers(L["scoial"]).execute(network)
except UnknownLayerError as e:
    print("\nFAIL Error caught!")
    print(f"Error: {str(e).split('Known layers:')[0].strip()}")
    
    # Get suggestion
    if e.suggestion:
        print(f"\nOK Did you mean '{e.suggestion}'?")
        print(f"OK Retrying with '{e.suggestion}'...")
        result = Q.nodes().from_layers(L[e.suggestion]).execute(network)
        print(f"OK Success! Got {len(result.items)} nodes from layer '{e.suggestion}'")

print("\n" + "=" * 70)
print("Example 4: QueryResult.explain() - Interactive Help")
print("=" * 70)

# Execute a query
result = (
    Q.nodes()
    .from_layers(L["social"])
    .compute("degree")
    .where(degree__gt=0)
    .execute(network)
)

print("\nQuery executed successfully!")
print(f"Results: {len(result.items)} nodes")

print("\n--- Calling result.explain() ---")
print(result.explain())

print("\n" + "=" * 70)
print("Example 5: QueryResult.debug() - Technical Details")
print("=" * 70)

print("\n--- Calling result.debug() ---")
print(result.debug())

print("\n" + "=" * 70)
print("Example 6: LLM-Friendly Error Recovery Pattern")
print("=" * 70)

print("\nSimulating LLM error recovery:")

import json

def llm_error_recovery(query_fn, network):
    """Simulate LLM recovering from an error."""
    try:
        return query_fn(network)
    except Exception as e:
        if hasattr(e, 'to_diagnostic'):
            diag = e.to_diagnostic()
            
            # Parse diagnostic JSON (as LLM would)
            diag_dict = json.loads(diag.to_json())
            
            print(f"\nLLM received error: {diag_dict['code']}")
            print(f"Message: {diag_dict['message']}")
            
            # Extract suggestion
            if diag_dict.get('fixes') and len(diag_dict['fixes']) > 0:
                fix = diag_dict['fixes'][0]
                replacement = fix.get('replacement')
                
                print(f"\nLLM found suggestion: {fix['description']}")
                
                if replacement:
                    print(f"LLM applying fix: {replacement}")
                    # Return the suggestion so caller can retry
                    return {'error': True, 'suggestion': replacement}
        
        # Re-raise if no recovery possible
        raise

# Try with typo
print("\nOriginal query: Q.nodes().compute('pagerank_typo')")

def bad_query(net):
    return Q.nodes().compute("pagerank_typo").execute(net)

recovery = llm_error_recovery(bad_query, network)

if isinstance(recovery, dict) and recovery.get('error'):
    print(f"\nOK LLM successfully extracted suggestion: {recovery['suggestion']}")
    print("OK LLM can now retry with corrected query")

print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
print("""
The diagnostic system provides:

1. OK Structured error information (Diagnostic objects)
2. OK Fuzzy matching for typo detection
3. OK "Did you mean?" suggestions
4. OK JSON export for LLM consumption
5. OK Interactive help with .explain() and .debug()
6. OK Stable error codes for programmatic handling

This makes py3plex errors:
- More helpful for humans (clear suggestions)
- More parseable for LLMs (JSON schema)
- More actionable (concrete fixes)
- More discoverable (related APIs)
""")
