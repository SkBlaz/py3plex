"""
Example demonstrating statistical report generation.

This example shows how to generate comprehensive statistical reports
for multilayer networks in text, HTML, or JSON format.
"""

from py3plex.core.multinet import multi_layer_network
from py3plex.algorithms.statistical_report import generate_statistical_report


def main():
    """Demonstrate statistical report generation."""
    print("=== Statistical Report Demo ===\n")

    # Create a sample network
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2'},
    ])

    print(f"Network: {net.core_network.number_of_nodes()} nodes, "
          f"{net.core_network.number_of_edges()} edges\n")

    # Generate comprehensive text report
    print("Generating statistical report...\n")
    report = generate_statistical_report(
        net,
        output_format='text',
        include_sections=['basic', 'degree', 'layers', 'clustering']
    )

    # Print report
    print(report)

    # Can also save to file
    # generate_statistical_report(net, output_format='html', output_file='report.html')
    # generate_statistical_report(net, output_format='json', output_file='report.json')

    print("\nSupported formats:")
    print("  - text: Human-readable plain text")
    print("  - html: Interactive HTML with formatting")
    print("  - json: Machine-readable structured data\n")


if __name__ == "__main__":
    main()
