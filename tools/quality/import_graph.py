"""Import graph analyzer for py3plex codebase.

This module analyzes module dependencies to create a directed acyclic graph (DAG)
of imports, helping identify circular dependencies and module structure.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class ImportGraphAnalyzer:
    """Analyzes import relationships in the py3plex codebase."""

    def __init__(self, repo_root: Path):
        """Initialize the analyzer.

        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = Path(repo_root)
        self.package_root = self.repo_root / "py3plex"
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        self.files_scanned: List[str] = []

    def analyze(self) -> Dict:
        """Analyze all Python files and build import graph.

        Returns:
            Dictionary with import graph data
        """
        # Scan all Python files
        for py_file in self.package_root.rglob("*.py"):
            if self._should_skip(py_file):
                continue

            module_name = self._get_module_name(py_file)
            self.files_scanned.append(str(py_file.relative_to(self.repo_root)))

            try:
                imports = self._extract_imports(py_file)
                self.imports[module_name].update(imports)
            except Exception as e:
                print(f"Warning: Failed to parse {py_file}: {e}")

        # Build result
        result = {
            "nodes": list(self.imports.keys()),
            "edges": self._build_edges(),
            "stats": self._calculate_stats(),
            "files_scanned": sorted(self.files_scanned),
        }

        return result

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "__pycache__",
            ".git",
            "build",
            "dist",
            ".eggs",
            "infomap.py",  # Auto-generated SWIG bindings
        ]
        path_str = str(path)
        return any(pattern in path_str for pattern in skip_patterns)

    def _get_module_name(self, path: Path) -> str:
        """Convert file path to module name."""
        rel_path = path.relative_to(self.repo_root)
        parts = list(rel_path.parts)

        # Remove .py extension
        if parts[-1].endswith(".py"):
            if parts[-1] == "__init__.py":
                parts.pop()
            else:
                parts[-1] = parts[-1][:-3]

        return ".".join(parts)

    def _extract_imports(self, path: Path) -> Set[str]:
        """Extract imports from a Python file."""
        imports = set()

        try:
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Only track py3plex imports
                    if alias.name.startswith("py3plex"):
                        imports.add(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("py3plex"):
                    imports.add(node.module)

        return imports

    def _build_edges(self) -> List[Dict]:
        """Build edge list for graph visualization."""
        edges = []
        for source, targets in self.imports.items():
            for target in targets:
                edges.append({"source": source, "target": target})
        return edges

    def _calculate_stats(self) -> Dict:
        """Calculate statistics about the import graph."""
        all_modules = set(self.imports.keys())
        all_imported = set()
        for targets in self.imports.values():
            all_imported.update(targets)

        return {
            "total_modules": len(all_modules),
            "total_edges": sum(len(targets) for targets in self.imports.values()),
            "modules_never_imported": len(all_modules - all_imported),
            "external_modules_imported": len(all_imported - all_modules),
        }

    def save_to_json(self, output_path: Path) -> None:
        """Save import graph to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        result = self.analyze()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, sort_keys=True)

        print(f"Import graph saved to {output_path}")


def main():
    """CLI entry point for import graph analysis."""
    import sys

    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])
    else:
        repo_root = Path.cwd()

    analyzer = ImportGraphAnalyzer(repo_root)
    output_path = repo_root / "build" / "quality" / "import_graph.json"
    analyzer.save_to_json(output_path)

    # Print summary
    result = analyzer.analyze()
    print(f"\nImport Graph Analysis Summary:")
    print(f"  Modules analyzed: {result['stats']['total_modules']}")
    print(f"  Import edges: {result['stats']['total_edges']}")
    print(
        f"  Modules never imported: {result['stats']['modules_never_imported']}"
    )


if __name__ == "__main__":
    main()
