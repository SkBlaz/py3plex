"""
Core abstractions for py3plex.lab experiment pipelines.

This module provides:
- ExperimentConfig: Configuration dataclass for experiments
- Step: Abstract base class for pipeline steps
- Pipeline: Orchestrates step execution
- Report: Collects and exports experiment results
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ExperimentConfig:
    """
    Configuration for an experiment.

    Attributes:
        name: Experiment name
        seed: Optional random seed for reproducibility
        metadata: Optional additional metadata
    """

    name: str
    seed: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a JSON-serializable dictionary representation.

        Returns:
            Dictionary containing name, seed, and metadata.
        """
        return asdict(self)


class Step(ABC):
    """
    Abstract base class for pipeline steps.

    Attributes:
        name: Step name
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a step.

        Args:
            name: Name of the step
        """
        self.name = name

    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the step.

        Args:
            state: Mutable state dictionary with at least:
                - "graph": a NetworkX-like graph object
                - "config": ExperimentConfig
                - "results": list[dict[str, Any]]

        Returns:
            Updated state dictionary (may be modified in-place).

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError


class Pipeline:
    """
    Pipeline that orchestrates step execution.

    Attributes:
        config: Experiment configuration
        steps: List of steps to execute
    """

    def __init__(self, config: ExperimentConfig, steps: List[Step]) -> None:
        """
        Initialize the pipeline.

        Args:
            config: Experiment configuration
            steps: List of Step instances to execute in sequence
        """
        self.config = config
        self.steps = steps

    def fit_run(self, graph: Any) -> "Report":
        """
        Run all steps on the graph and return a report.

        Args:
            graph: A NetworkX-like graph object

        Returns:
            Report containing experiment results
        """
        state: Dict[str, Any] = {
            "graph": graph,
            "config": self.config,
            "results": [],
        }

        for step in self.steps:
            state = step.run(state)

        return Report.from_state(state)


class Report:
    """
    Report containing experiment results.

    Attributes:
        config: Experiment configuration
        records: List of result records (one dict per measurement row)
    """

    def __init__(self, config: ExperimentConfig, records: List[Dict[str, Any]]) -> None:
        """
        Initialize the report.

        Args:
            config: Experiment configuration
            records: List of result dictionaries
        """
        self._config = config
        self._records = records

    @property
    def config(self) -> ExperimentConfig:
        """Return the experiment configuration."""
        return self._config

    @property
    def records(self) -> List[Dict[str, Any]]:
        """Return the result records."""
        return self._records

    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> "Report":
        """
        Create a Report from pipeline state.

        Args:
            state: Pipeline state dictionary with "config" and "results" keys

        Returns:
            Report instance
        """
        return cls(config=state["config"], records=state["results"])

    def to_dataframe(self) -> Any:
        """
        Convert records to a pandas DataFrame.

        Returns:
            pandas DataFrame with one row per record.

        Note:
            Pandas is imported lazily inside this method.
        """
        import pandas as pd

        return pd.DataFrame(self._records)

    def to_markdown(self, path: str) -> None:
        """
        Write the report to a markdown file.

        Args:
            path: Output file path

        The file contains:
            - Experiment name header
            - Config section with seed and metadata
            - Results table (if records exist)
        """
        lines: List[str] = []

        # Header
        lines.append(f"# {self._config.name}")
        lines.append("")

        # Config section
        lines.append("## Configuration")
        lines.append("")
        lines.append(f"- **Seed**: {self._config.seed}")
        if self._config.metadata:
            lines.append(f"- **Metadata**: {self._config.metadata}")
        lines.append("")

        # Results section
        lines.append("## Results")
        lines.append("")

        if self._records:
            # Get all unique keys from records (preserve order, O(n) complexity)
            all_keys: List[str] = list(
                dict.fromkeys(key for record in self._records for key in record.keys())
            )

            # Table header
            lines.append("| " + " | ".join(all_keys) + " |")
            lines.append("| " + " | ".join(["---"] * len(all_keys)) + " |")

            # Table rows
            for record in self._records:
                row = [str(record.get(key, "")) for key in all_keys]
                lines.append("| " + " | ".join(row) + " |")
        else:
            lines.append("No results recorded.")

        lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
