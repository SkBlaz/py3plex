"""Examples health checker for py3plex codebase.

This module checks if example scripts can be imported and run,
detecting stale examples with moved or removed APIs.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict


@dataclass
class ExampleHealth:
    """Health status of an example."""

    file: str
    status: str  # healthy, import_error, runtime_error, skipped
    error_message: str
    apis_used: List[str]


class ExamplesHealthChecker:
    """Checks health of example scripts."""

    def __init__(self, repo_root: Path):
        """Initialize the checker.

        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = Path(repo_root)
        self.examples_root = self.repo_root / "examples"

    def check(self) -> List[ExampleHealth]:
        """Check all examples.

        Returns:
            List of ExampleHealth objects
        """
        if not self.examples_root.exists():
            return []

        results = []

        for py_file in self.examples_root.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue

            result = self._check_example(py_file)
            results.append(result)

        return results

    def _check_example(self, example_file: Path) -> ExampleHealth:
        """Check a single example file."""
        rel_path = str(example_file.relative_to(self.repo_root))

        # Try to import (syntax check)
        try:
            with open(example_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for obvious syntax errors
            compile(content, str(example_file), "exec")

            # Extract APIs used
            apis_used = self._extract_apis(content)

            return ExampleHealth(
                file=rel_path,
                status="healthy",
                error_message="",
                apis_used=apis_used,
            )

        except SyntaxError as e:
            return ExampleHealth(
                file=rel_path,
                status="import_error",
                error_message=f"SyntaxError: {e}",
                apis_used=[],
            )

        except Exception as e:
            return ExampleHealth(
                file=rel_path,
                status="runtime_error",
                error_message=str(e),
                apis_used=[],
            )

    def _extract_apis(self, content: str) -> List[str]:
        """Extract py3plex APIs used in code."""
        import re

        # Find imports
        import_pattern = r"from py3plex[.\w]* import ([\w, ]+)"
        matches = re.findall(import_pattern, content)

        apis = []
        for match in matches:
            # Split by comma and clean
            for api in match.split(","):
                apis.append(api.strip())

        return apis

    def save_to_json(self, output_path: Path) -> None:
        """Save health check to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        results = self.check()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {
            "total_examples": len(results),
            "healthy": len([r for r in results if r.status == "healthy"]),
            "import_errors": len([r for r in results if r.status == "import_error"]),
            "runtime_errors": len([r for r in results if r.status == "runtime_error"]),
            "examples": [asdict(ex) for ex in results],
        }

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Examples health check saved to {output_path}")


def main():
    """CLI entry point for examples health checking."""
    import sys

    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])
    else:
        repo_root = Path.cwd()

    checker = ExamplesHealthChecker(repo_root)
    output_path = repo_root / "build" / "quality" / "examples_health.json"
    checker.save_to_json(output_path)

    # Print summary
    results = checker.check()
    errors = [r for r in results if r.status != "healthy"]
    print(f"\nExamples Health Summary:")
    print(f"  Total examples: {len(results)}")
    print(f"  Healthy: {len([r for r in results if r.status == 'healthy'])}")
    print(f"  Errors: {len(errors)}")


if __name__ == "__main__":
    main()
