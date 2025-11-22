"""
Example: Config-Driven Workflows in py3plex

This example demonstrates how to use YAML or JSON configuration files to define
and execute reproducible network analysis workflows.

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

from pathlib import Path

from py3plex.workflows import WorkflowConfig, WorkflowRunner


def run_yaml_workflow():
    """Run workflow from YAML configuration."""
    print("=" * 70)
    print("Running YAML-based workflow...")
    print("=" * 70)

    # Path to the example YAML config
    config_path = Path(__file__).parent / "example_config.yaml"

    # Load and validate configuration
    config = WorkflowConfig.from_file(config_path)

    print(f"\nWorkflow: {config.name}")
    print(f"Description: {config.description}")
    print(f"Datasets: {len(config.datasets)}")
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

    print("\nYAML workflow completed!")


def run_json_workflow():
    """Run workflow from JSON configuration."""
    print("\n" + "=" * 70)
    print("Running JSON-based workflow...")
    print("=" * 70)

    # Path to the example JSON config
    config_path = Path(__file__).parent / "comparison_config.json"

    # Load configuration
    config = WorkflowConfig.from_file(config_path)

    print(f"\nWorkflow: {config.name}")
    print(f"Description: {config.description}")
    print(f"Datasets: {len(config.datasets)}")
    print(f"Operations: {len(config.operations)}")

    # Execute workflow
    print("\nExecuting workflow...")
    runner = WorkflowRunner(config)
    runner.run()

    print("\nJSON workflow completed!")


def main():
    """Run both example workflows."""
    print("\nConfig-Driven Workflows Example")
    print("=" * 70)
    print(
        "\nThis example shows how to define network analysis pipelines"
        "\nusing YAML or JSON configuration files."
    )
    print("\nBenefits:")
    print("  • Reproducible research")
    print("  • Easy to share and version control")
    print("  • Pipeline automation")
    print("  • No code changes needed for different experiments")

    try:
        # Run YAML example
        run_yaml_workflow()

        # Run JSON example
        run_json_workflow()

        print("\n" + "=" * 70)
        print("All workflows completed successfully!")
        print("=" * 70)
        print("\nTo run these workflows from CLI:")
        print("  py3plex run-config example_config.yaml")
        print("  py3plex run-config comparison_config.json")
        print("\nTo validate a config without running:")
        print("  py3plex run-config example_config.yaml --validate-only")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
