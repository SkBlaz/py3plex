"""Config-driven workflows with YAML/JSON definitions.

Shows how to load, validate, and run workflows defined in the sibling YAML/JSON
configs. Uses only local files—no network calls—and finishes quickly (<5s).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from py3plex.workflows import WorkflowConfig, WorkflowRunner


def load_config(config_path: Path) -> Optional[WorkflowConfig]:
    """Load a workflow config from disk with a helpful message on failure."""
    if not config_path.exists():
        print(f" Missing config file: {config_path}")
        return None

    try:
        config = WorkflowConfig.from_file(config_path)
        return rebase_paths(config_path, config)
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f" Could not read {config_path.name}: {exc}")
    return None


def rebase_paths(config_path: Path, config: WorkflowConfig) -> WorkflowConfig:
    """Resolve all relative paths in the config against the config file location."""
    base = config_path.parent

    for dataset in config.datasets:
        path = dataset.get("path")
        if path and not Path(path).is_absolute():
            dataset["path"] = str(base / path)

    for operation in config.operations:
        params = operation.get("parameters", {})
        output = params.get("output")
        if isinstance(output, str) and not Path(output).is_absolute():
            params["output"] = str(base / output)

    if config.output:
        directory = config.output.get("directory")
        if isinstance(directory, str) and not Path(directory).is_absolute():
            config.output["directory"] = str(base / directory)

        summary = config.output.get("summary")
        if isinstance(summary, str) and not Path(summary).is_absolute():
            config.output["summary"] = str(base / summary)

    return config


def print_dataset_summary(config: WorkflowConfig) -> None:
    """Print a compact overview of the datasets and operations in a config."""
    print(f"\nWorkflow: {config.name}")
    print(f"Description: {config.description}")
    print(f"Datasets: {len(config.datasets)}")
    for dataset in config.datasets:
        path = dataset.get("path", "<generated>")
        print(f"  - {dataset.get('name', dataset.get('type', 'dataset'))}: {path}")
    print(f"Operations: {len(config.operations)}")


def run_file_loading_workflow() -> None:
    """Run workflow that loads network from file."""
    print("=" * 70)
    print("Example 1: Loading Network from File (YAML)")
    print("=" * 70)

    config_path = Path(__file__).parent / "load_from_file.yaml"

    config = load_config(config_path)
    if config is None:
        return

    errors = config.validate()
    if errors:
        print("\nValidation errors:")
        for error in errors:
            print(f"  - {error}")
        return

    print_dataset_summary(config)
    print("\nConfiguration is valid!")

    print("\nExecuting workflow...")
    runner = WorkflowRunner(config)
    runner.run()

    print("\nFile-loading workflow completed!")


def run_file_comparison_workflow() -> None:
    """Run workflow comparing file-loaded and generated networks."""
    print("\n" + "=" * 70)
    print("Example 2: File vs Generated Network Comparison (JSON)")
    print("=" * 70)

    config_path = Path(__file__).parent / "load_and_compare.json"

    config = load_config(config_path)
    if config is None:
        return

    print_dataset_summary(config)
    print("\nExecuting workflow...")
    runner = WorkflowRunner(config)
    runner.run()

    print("\nComparison workflow completed!")


def run_generation_workflow() -> None:
    """Run workflow that generates networks (for completeness)."""
    print("\n" + "=" * 70)
    print("Example 3: Network Generation Workflow (YAML)")
    print("=" * 70)

    config_path = Path(__file__).parent / "example_config.yaml"

    config = load_config(config_path)
    if config is None:
        return

    print_dataset_summary(config)

    print("\nExecuting workflow...")
    runner = WorkflowRunner(config)
    runner.run()

    print("\nGeneration workflow completed!")


def main() -> int:
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

    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"\nError: {exc}")
        import traceback  # local import to avoid polluting top-level

        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
