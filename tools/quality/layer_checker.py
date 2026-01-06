"""Import boundary checker for enforcing module layering rules.

This module checks that import dependencies respect defined layering
constraints (e.g., DSL should not import heavy algorithm modules).
"""

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass, asdict

# Use tomllib for Python 3.11+ (built-in), tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # Will handle gracefully


@dataclass
class LayerViolation:
    """Represents a layer boundary violation."""

    file: str
    line: int
    imported_module: str
    rule: str
    severity: str  # error, warning


class ImportBoundaryChecker:
    """Checks import boundaries against layering rules."""

    def __init__(self, repo_root: Path):
        """Initialize the checker.

        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = Path(repo_root)
        self.package_root = self.repo_root / "py3plex"
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, List[str]]:
        """Load layering rules from pyproject.toml."""
        pyproject_path = self.repo_root / "pyproject.toml"

        if not pyproject_path.exists():
            return {}

        if tomllib is None:
            print("Warning: tomli/tomllib not available, skipping layer checks")
            return {}

        try:
            with open(pyproject_path, "rb") as f:
                config = tomllib.load(f)

            layering = config.get("tool", {}).get("py3plex", {}).get("layering", {})
            return layering
        except Exception as e:
            print(f"Warning: Failed to load layering rules: {e}")
            return {}

    def check(self) -> List[LayerViolation]:
        """Check all files for layer violations.

        Returns:
            List of LayerViolation objects
        """
        violations = []

        # Check DSL forbidden imports
        if "dsl_forbidden_imports" in self.rules:
            violations.extend(
                self._check_module_imports(
                    "py3plex/dsl",
                    self.rules["dsl_forbidden_imports"],
                    "dsl_forbidden_imports",
                )
            )

        # Check algorithms forbidden imports
        if "algorithms_forbidden_imports" in self.rules:
            violations.extend(
                self._check_module_imports(
                    "py3plex/algorithms",
                    self.rules["algorithms_forbidden_imports"],
                    "algorithms_forbidden_imports",
                )
            )

        # Check datasets forbidden imports
        if "datasets_forbidden_imports" in self.rules:
            violations.extend(
                self._check_module_imports(
                    "py3plex/datasets",
                    self.rules["datasets_forbidden_imports"],
                    "datasets_forbidden_imports",
                )
            )

        # Check uncertainty forbidden imports
        if "uncertainty_forbidden_imports" in self.rules:
            violations.extend(
                self._check_module_imports(
                    "py3plex/uncertainty",
                    self.rules["uncertainty_forbidden_imports"],
                    "uncertainty_forbidden_imports",
                )
            )

        return violations

    def _check_module_imports(
        self, module_path: str, forbidden: List[str], rule_name: str
    ) -> List[LayerViolation]:
        """Check imports in a specific module."""
        violations = []
        module_dir = self.repo_root / module_path

        if not module_dir.exists():
            return violations

        for py_file in module_dir.rglob("*.py"):
            if self._should_skip(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if self._is_forbidden(alias.name, forbidden):
                                violations.append(
                                    LayerViolation(
                                        file=str(py_file.relative_to(self.repo_root)),
                                        line=node.lineno,
                                        imported_module=alias.name,
                                        rule=rule_name,
                                        severity="error",
                                    )
                                )

                    elif isinstance(node, ast.ImportFrom):
                        if node.module and self._is_forbidden(node.module, forbidden):
                            violations.append(
                                LayerViolation(
                                    file=str(py_file.relative_to(self.repo_root)),
                                    line=node.lineno,
                                    imported_module=node.module,
                                    rule=rule_name,
                                    severity="error",
                                )
                            )

            except Exception:
                pass

        return violations

    def _is_forbidden(self, import_name: str, forbidden_list: List[str]) -> bool:
        """Check if import is forbidden."""
        for forbidden in forbidden_list:
            if import_name.startswith(forbidden):
                return True
        return False

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = ["__pycache__", ".git", "build", "dist", "test_"]
        path_str = str(path)
        return any(pattern in path_str for pattern in skip_patterns)

    def save_to_json(self, output_path: Path) -> None:
        """Save violations to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        violations = self.check()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {
            "total_violations": len(violations),
            "by_rule": self._group_by_rule(violations),
            "violations": [asdict(v) for v in violations],
        }

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Layer violations saved to {output_path}")

    def _group_by_rule(self, violations: List[LayerViolation]) -> Dict[str, int]:
        """Group violations by rule."""
        groups = {}
        for v in violations:
            groups[v.rule] = groups.get(v.rule, 0) + 1
        return groups


def main():
    """CLI entry point for boundary checking."""
    import sys

    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])
    else:
        repo_root = Path.cwd()

    checker = ImportBoundaryChecker(repo_root)
    output_path = repo_root / "build" / "quality" / "layer_violations.json"
    checker.save_to_json(output_path)

    # Print summary
    violations = checker.check()
    print(f"\nImport Boundary Check Summary:")
    print(f"  Total violations: {len(violations)}")

    if violations:
        print(f"\n  Violations by rule:")
        by_rule = checker._group_by_rule(violations)
        for rule, count in by_rule.items():
            print(f"    {rule}: {count}")

        print(f"\n  First 5 violations:")
        for v in violations[:5]:
            print(f"    {v.file}:{v.line} imports {v.imported_module}")

        sys.exit(1)
    else:
        print("  ✅ No violations found")
        sys.exit(0)


if __name__ == "__main__":
    main()
