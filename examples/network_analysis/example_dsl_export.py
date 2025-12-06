"""Example: DSL Export Functionality

This example demonstrates how to use the EXPORT functionality in py3plex DSL v2
to declaratively export query results to files (CSV, JSON, etc.).

The export feature allows you to write results directly to disk as part of the
query pipeline, making it easy to create reproducible analysis workflows.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L


def create_sample_network():
    """Create a sample multilayer network for demonstration."""
    network = multinet.multi_layer_network(directed=False)

    # Add nodes to different layers
    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'Diana', 'type': 'social'},
        {'source': 'Eve', 'type': 'social'},
        {'source': 'Alice', 'type': 'work'},
        {'source': 'Bob', 'type': 'work'},
        {'source': 'Frank', 'type': 'work'},
    ]
    network.add_nodes(nodes)

    # Add edges within layers
    edges = [
        # Social layer
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'Diana', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Diana', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Diana', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
        # Work layer
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Alice', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work'},
    ]
    network.add_edges(edges)

    return network


def example_basic_csv_export():
    """Example 1: Basic CSV export."""
    print("\n=== Example 1: Basic CSV Export ===")
    
    network = create_sample_network()
    
    # Query with CSV export
    result = (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree")
        .export_csv("results/social_degree.csv")
        .execute(network)
    )
    
    print(f"Exported {len(result.items)} nodes to results/social_degree.csv")
    print(f"Result still available in Python: {result}")


def example_json_export_with_columns():
    """Example 2: JSON export with column selection."""
    print("\n=== Example 2: JSON Export with Column Selection ===")
    
    network = create_sample_network()
    
    # Export specific columns in specific order
    result = (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree", "betweenness_centrality")
        .order_by("degree", desc=True)
        .limit(5)
        .export_json(
            "results/top_nodes.json",
            columns=["id", "degree", "betweenness_centrality"],
            orient="records"
        )
        .execute(network)
    )
    
    print(f"Exported top 5 nodes to results/top_nodes.json")
    print(f"Top node: {result.items[0]} with degree {result.attributes['degree'][result.items[0]]}")


def example_multiple_exports():
    """Example 3: Running multiple queries with different exports."""
    print("\n=== Example 3: Multiple Exports ===")
    
    network = create_sample_network()
    
    # Export social layer analysis
    (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree", "clustering")
        .export_csv("results/social_analysis.csv", columns=["id", "degree", "clustering"])
        .execute(network)
    )
    print("Exported social layer analysis")
    
    # Export work layer analysis
    (
        Q.nodes()
        .from_layers(L["work"])
        .compute("degree", "betweenness_centrality")
        .export_csv("results/work_analysis.csv")
        .execute(network)
    )
    print("Exported work layer analysis")
    
    # Export combined analysis with custom delimiter
    (
        Q.nodes()
        .compute("degree")
        .order_by("degree", desc=True)
        .export_csv("results/all_nodes.tsv", delimiter="\t")
        .execute(network)
    )
    print("Exported combined analysis as TSV")


def example_export_with_filtering():
    """Example 4: Export with filtering and ordering."""
    print("\n=== Example 4: Export with Filtering ===")
    
    network = create_sample_network()
    
    # Export only high-degree nodes
    result = (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree")
        .order_by("degree", desc=True)
        .export_json(
            "results/high_degree_nodes.json",
            orient="split"  # Different JSON format
        )
        .execute(network)
    )
    
    print(f"Exported {len(result.items)} nodes with degree information")


def example_export_formats():
    """Example 5: Different export formats."""
    print("\n=== Example 5: Different Export Formats ===")
    
    network = create_sample_network()
    
    # Build base query
    query_base = Q.nodes().from_layers(L["social"]).compute("degree")
    
    # Export as CSV
    query_base.export_csv("results/format_demo.csv").execute(network)
    print("Exported as CSV")
    
    # Export as JSON (need to rebuild query)
    (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree")
        .export_json("results/format_demo.json")
        .execute(network)
    )
    print("Exported as JSON")
    
    # Export as TSV using generic export method
    (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree")
        .export("results/format_demo.tsv", fmt="tsv")
        .execute(network)
    )
    print("Exported as TSV")


def example_export_with_custom_options():
    """Example 6: Export with custom format options."""
    print("\n=== Example 6: Custom Export Options ===")
    
    network = create_sample_network()
    
    # CSV with semicolon delimiter
    (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree")
        .export_csv("results/custom_delim.csv", delimiter=";")
        .execute(network)
    )
    print("Exported CSV with semicolon delimiter")
    
    # JSON with custom indent
    (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree")
        .export_json("results/pretty.json", indent=4)
        .execute(network)
    )
    print("Exported JSON with 4-space indent")
    
    # JSON with different orientations
    for orient in ["records", "columns", "split"]:
        (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .limit(3)
            .export_json(f"results/orient_{orient}.json", orient=orient)
            .execute(network)
        )
        print(f"Exported JSON with orient='{orient}'")


def example_inspect_dsl_string():
    """Example 7: Inspect generated DSL string with export."""
    print("\n=== Example 7: DSL String with Export ===")
    
    # Build a query with export
    query = (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree", alias="deg")
        .order_by("deg", desc=True)
        .limit(10)
        .export_csv("results/output.csv", columns=["id", "deg"])
    )
    
    # Get DSL string representation
    dsl_string = query.to_dsl()
    print("Generated DSL string:")
    print(dsl_string)
    print("\nNote: The EXPORT clause is now part of the declarative query!")


if __name__ == "__main__":
    print("=" * 70)
    print("py3plex DSL Export Functionality Examples")
    print("=" * 70)
    
    # Run examples
    example_basic_csv_export()
    example_json_export_with_columns()
    example_multiple_exports()
    example_export_with_filtering()
    example_export_formats()
    example_export_with_custom_options()
    example_inspect_dsl_string()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("Check the 'results/' directory for exported files.")
    print("=" * 70)
