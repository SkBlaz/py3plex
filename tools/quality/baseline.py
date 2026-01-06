"""Baseline comparison tool for quality metrics.

This module compares current quality metrics against a baseline,
allowing CI to detect regressions while grandfathering existing issues.
"""

import json
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class BaselineComparison:
    """Results of baseline comparison."""

    metric: str
    baseline_value: float
    current_value: float
    threshold: float
    regression: bool
    improvement: bool
    message: str


class BaselineChecker:
    """Checks current metrics against baseline."""

    def __init__(self, repo_root: Path, baseline_path: Path = None):
        """Initialize the checker.

        Args:
            repo_root: Root directory of the repository
            baseline_path: Path to baseline JSON file
        """
        self.repo_root = Path(repo_root)
        if baseline_path is None:
            baseline_path = repo_root / "build" / "quality" / "quality_baseline.json"
        self.baseline_path = baseline_path
        self.baseline = self._load_baseline()

    def _load_baseline(self) -> Dict[str, Any]:
        """Load baseline metrics."""
        if not self.baseline_path.exists():
            return {}

        with open(self.baseline_path, "r") as f:
            return json.load(f)

    def compare(self, current_metrics: Dict[str, Any]) -> list[BaselineComparison]:
        """Compare current metrics against baseline.

        Args:
            current_metrics: Dictionary of current metric values

        Returns:
            List of BaselineComparison objects
        """
        if not self.baseline:
            return []

        results = []

        # Compare dead code count
        if "dead_code" in self.baseline and "dead_code" in current_metrics:
            results.append(
                self._compare_metric(
                    "dead_code_count",
                    self.baseline["dead_code"]["total_candidates"],
                    current_metrics["dead_code"]["total_candidates"],
                    threshold=5,  # Allow 5 more dead code items
                    lower_is_better=True,
                )
            )

        # Compare redundancy clusters
        if "redundancy" in self.baseline and "redundancy" in current_metrics:
            results.append(
                self._compare_metric(
                    "redundancy_clusters",
                    self.baseline["redundancy"]["total_clusters"],
                    current_metrics["redundancy"]["total_clusters"],
                    threshold=3,  # Allow 3 more clusters
                    lower_is_better=True,
                )
            )

        return results

    def _compare_metric(
        self,
        metric_name: str,
        baseline: float,
        current: float,
        threshold: float,
        lower_is_better: bool = True,
    ) -> BaselineComparison:
        """Compare a single metric."""
        if lower_is_better:
            regression = current > baseline + threshold
            improvement = current < baseline
            message = (
                f"Regression: {current} > {baseline + threshold}"
                if regression
                else f"OK: {current} <= {baseline + threshold}"
            )
        else:
            regression = current < baseline - threshold
            improvement = current > baseline
            message = (
                f"Regression: {current} < {baseline - threshold}"
                if regression
                else f"OK: {current} >= {baseline - threshold}"
            )

        return BaselineComparison(
            metric=metric_name,
            baseline_value=baseline,
            current_value=current,
            threshold=threshold,
            regression=regression,
            improvement=improvement,
            message=message,
        )

    def update_baseline(self, metrics: Dict[str, Any]) -> None:
        """Update baseline with current metrics.

        Args:
            metrics: Dictionary of metrics to save as baseline
        """
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.baseline_path, "w") as f:
            json.dump(metrics, f, indent=2)

        print(f"Baseline updated: {self.baseline_path}")


def load_current_metrics(quality_dir: Path) -> Dict[str, Any]:
    """Load all current quality metrics.

    Args:
        quality_dir: Directory containing quality JSON files

    Returns:
        Dictionary with all metrics
    """
    metrics = {}

    # Load dead code metrics
    dead_code_path = quality_dir / "dead_code.json"
    if dead_code_path.exists():
        with open(dead_code_path, "r") as f:
            metrics["dead_code"] = json.load(f)

    # Load redundancy metrics
    redundancy_path = quality_dir / "redundancy.json"
    if redundancy_path.exists():
        with open(redundancy_path, "r") as f:
            metrics["redundancy"] = json.load(f)

    # Load examples health
    examples_path = quality_dir / "examples_health.json"
    if examples_path.exists():
        with open(examples_path, "r") as f:
            metrics["examples_health"] = json.load(f)

    return metrics


def main():
    """CLI entry point for baseline checking."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Check quality metrics against baseline")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory of the repository",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update baseline with current metrics",
    )

    args = parser.parse_args()

    repo_root = args.repo_root
    quality_dir = repo_root / "build" / "quality"

    # Load current metrics
    current_metrics = load_current_metrics(quality_dir)

    checker = BaselineChecker(repo_root)

    if args.update_baseline:
        checker.update_baseline(current_metrics)
        print("Baseline updated successfully")
        return 0

    # Compare against baseline
    results = checker.compare(current_metrics)

    if not results:
        print("No baseline found. Run with --update-baseline to create one.")
        return 0

    # Print results
    print("\nBaseline Comparison Results:")
    print("=" * 70)

    regressions = []
    for result in results:
        status = "❌ REGRESSION" if result.regression else "✅ OK"
        print(f"{status} {result.metric}: {result.message}")
        if result.regression:
            regressions.append(result)

    if regressions:
        print("\n" + "=" * 70)
        print(f"FAILURE: {len(regressions)} regression(s) detected")
        print("=" * 70)
        return 1
    else:
        print("\n" + "=" * 70)
        print("SUCCESS: No regressions detected")
        print("=" * 70)
        return 0


if __name__ == "__main__":
    sys.exit(main())
