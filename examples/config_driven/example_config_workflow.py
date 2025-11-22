"""
Example: Config-Driven Workflows in py3plex

This example demonstrates how to use YAML or JSON configuration files to define
and execute reproducible network analysis workflows.

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

from pathlib import Path

from py3plex.workflows import WorkflowConfig, WorkflowRunner


def run_file_loading_workflow():
    """Run workflow that loads network from file."""
    print("=" * 70)
    print("Example 1: Loading Network from File (YAML)")
    print("=" * 70)

    # Path to the file-loading YAML config
    config_path = Path(__file__).parent / "load_from_file.yaml"

    # Load and validate configuration
    config = WorkflowConfig.from_file(config_path)

    print(f"\nWorkflow: {config.name}")
    print(f"Description: {config.description}")
    print(f"Dataset type: {config.datasets[0]['type']}")
    print(f"Loading from: {config.datasets[0]['path']}")
    print(f"Operations: {len(config.operations)}")

    # Validate configuration
    errors = config.validate()
    if errors:
        print("\nValidation errors:")
        for error in errors:
            print(f"  - {error}")
        return

    print("\nConfiguration is valid!")

    # Execute workflow
    print("\nExecuting workflow...")
    runner = WorkflowRunner(config)
    runner.run()

    print("\nFile-loading workflow completed!")


def run_file_comparison_workflow():
    """Run workflow comparing file-loaded and generated networks."""
    print("\n" + "=" * 70)
    print("Example 2: File vs Generated Network Comparison (JSON)")
    print("=" * 70)

    # Path to the comparison JSON config
    config_path = Path(__file__).parent / "load_and_compare.json"

    # Load configuration
    config = WorkflowConfig.from_file(config_path)

    print(f"\nWorkflow: {config.name}")
    print(f"Description: {config.description}")
    print(f"Datasets: {len(config.datasets)}")
    print(f"  - {config.datasets[0]['name']}: loaded from {config.datasets[0]['path']}")
    print(f"  - {config.datasets[1]['name']}: generated")
    print(f"Operations: {len(config.operations)}")

    # Execute workflow
    print("\nExecuting workflow...")
    runner = WorkflowRunner(config)
    runner.run()

    print("\nComparison workflow completed!")


def run_generation_workflow():
    """Run workflow that generates networks (for completeness)."""
    print("\n" + "=" * 70)
    print("Example 3: Network Generation Workflow (YAML)")
    print("=" * 70)

    # Path to the generation YAML config
    config_path = Path(__file__).parent / "example_config.yaml"

    # Load configuration
    config = WorkflowConfig.from_file(config_path)

    print(f"\nWorkflow: {config.name}")
    print(f"Description: {config.description}")
    print(f"Dataset type: {config.datasets[0]['type']} (for comparison)")

    # Execute workflow
    print("\nExecuting workflow...")
    runner = WorkflowRunner(config)
    runner.run()

    print("\nGeneration workflow completed!")


def main():
    """Run all example workflows."""
    print("\nConfig-Driven Workflows Examples")
    print("=" * 70)
    print(
        "\nThis example shows how to define network analysis pipelines"
        "\nusing YAML or JSON configuration files."
    )
    print("\nBenefits:")
    print("  • Reproducible research")
    print("  • Easy to share and version control")
    print("  • Pipeline automation")
    print("  • Load existing networks or generate new ones")
    print("  • No code changes needed for different experiments")

    try:
        # Run file-loading example (primary focus)
        run_file_loading_workflow()

        # Run comparison example (file + generation)
        run_file_comparison_workflow()

        # Run generation example (for completeness)
        run_generation_workflow()

        print("\n" + "=" * 70)
        print("All workflows completed successfully!")
        print("=" * 70)
        print("\nTo run these workflows from CLI:")
        print("  py3plex run-config load_from_file.yaml")
        print("  py3plex run-config load_and_compare.json")
        print("  py3plex run-config example_config.yaml")
        print("\nTo validate a config without running:")
        print("  py3plex run-config load_from_file.yaml --validate-only")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
