"""Public API auditor for py3plex codebase.

This module audits the public API surface, identifying what's exposed,
where it's used, and assigning stability tiers.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class APISymbol:
    """Represents a public API symbol."""

    symbol: str
    definition_file: str
    definition_line: int
    type: str  # function, class, constant
    exported_from: List[str]  # __init__.py files that export it
    used_in_examples: List[str]
    used_in_docs: List[str]
    used_internally: int  # count
    stability_tier: str  # core, supported, experimental, internal


class PublicAPIAuditor:
    """Audits the public API surface of py3plex."""

    def __init__(self, repo_root: Path):
        """Initialize the auditor.

        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = Path(repo_root)
        self.package_root = self.repo_root / "py3plex"
        self.examples_root = self.repo_root / "examples"
        self.docs_root = self.repo_root / "docfiles"
        self.symbols: Dict[str, APISymbol] = {}

    def analyze(self) -> List[APISymbol]:
        """Analyze the public API.

        Returns:
            List of APISymbol objects
        """
        # Step 1: Find all exported symbols from __init__.py files
        exported = self._find_exported_symbols()

        # Step 2: Check usage in examples
        example_usage = self._scan_examples()

        # Step 3: Check usage in docs
        doc_usage = self._scan_docs()

        # Step 4: Check internal usage
        internal_usage = self._scan_internal_usage()

        # Step 5: Build API symbol records
        for symbol_name, export_info in exported.items():
            symbol = APISymbol(
                symbol=symbol_name,
                definition_file=export_info["file"],
                definition_line=export_info["line"],
                type=export_info["type"],
                exported_from=export_info["exported_from"],
                used_in_examples=example_usage.get(symbol_name, []),
                used_in_docs=doc_usage.get(symbol_name, []),
                used_internally=internal_usage.get(symbol_name, 0),
                stability_tier=self._assign_stability_tier(
                    symbol_name, export_info, example_usage, doc_usage, internal_usage
                ),
            )
            self.symbols[symbol_name] = symbol

        return list(self.symbols.values())

    def _find_exported_symbols(self) -> Dict[str, Dict]:
        """Find all symbols exported from __init__.py files."""
        exported = {}

        for init_file in self.package_root.rglob("__init__.py"):
            if self._should_skip(init_file):
                continue

            try:
                with open(init_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(init_file))

                # Look for __all__ definition
                all_symbols = self._extract_all_symbols(tree)

                # Look for explicit imports
                imported_symbols = self._extract_imported_symbols(tree)

                # Record symbols
                module_path = str(init_file.relative_to(self.repo_root))

                for symbol in all_symbols:
                    if symbol not in exported:
                        exported[symbol] = {
                            "file": module_path,
                            "line": 0,
                            "type": "unknown",
                            "exported_from": [],
                        }
                    exported[symbol]["exported_from"].append(module_path)

                for symbol, info in imported_symbols.items():
                    if symbol not in exported:
                        exported[symbol] = {
                            "file": info["from"],
                            "line": info["line"],
                            "type": info["type"],
                            "exported_from": [],
                        }
                    exported[symbol]["exported_from"].append(module_path)

            except Exception:
                pass

        return exported

    def _extract_all_symbols(self, tree: ast.AST) -> List[str]:
        """Extract symbols from __all__ list."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            symbols = []
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    symbols.append(elt.value)
                            return symbols
        return []

    def _extract_imported_symbols(self, tree: ast.AST) -> Dict[str, Dict]:
        """Extract imported symbols from imports."""
        symbols = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if not node.module or not node.module.startswith("py3plex"):
                    continue

                for alias in node.names:
                    symbol_name = alias.name
                    symbols[symbol_name] = {
                        "from": node.module,
                        "line": node.lineno,
                        "type": "imported",
                    }

        return symbols

    def _scan_examples(self) -> Dict[str, List[str]]:
        """Scan examples for symbol usage."""
        usage = defaultdict(list)

        if not self.examples_root.exists():
            return usage

        for py_file in self.examples_root.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Simple grep for symbol names
                rel_path = str(py_file.relative_to(self.repo_root))
                for symbol in self.symbols.keys():
                    if symbol in content:
                        usage[symbol].append(rel_path)

            except Exception:
                pass

        return usage

    def _scan_docs(self) -> Dict[str, List[str]]:
        """Scan documentation for symbol usage."""
        usage = defaultdict(list)

        if not self.docs_root.exists():
            return usage

        for doc_file in self.docs_root.rglob("*.rst"):
            try:
                with open(doc_file, "r", encoding="utf-8") as f:
                    content = f.read()

                rel_path = str(doc_file.relative_to(self.repo_root))
                for symbol in self.symbols.keys():
                    if symbol in content:
                        usage[symbol].append(rel_path)

            except Exception:
                pass

        return usage

    def _scan_internal_usage(self) -> Dict[str, int]:
        """Scan internal codebase for symbol usage."""
        usage = defaultdict(int)

        for py_file in self.package_root.rglob("*.py"):
            if self._should_skip(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                for symbol in self.symbols.keys():
                    usage[symbol] += content.count(symbol)

            except Exception:
                pass

        return usage

    def _assign_stability_tier(
        self,
        symbol: str,
        export_info: Dict,
        example_usage: Dict,
        doc_usage: Dict,
        internal_usage: Dict,
    ) -> str:
        """Assign stability tier to a symbol."""
        # Core: Used in docs, examples, and heavily internally
        if (
            symbol in example_usage
            and symbol in doc_usage
            and internal_usage.get(symbol, 0) > 10
        ):
            return "core"

        # Supported: Used in docs or examples
        if symbol in example_usage or symbol in doc_usage:
            return "supported"

        # Experimental: Exported but not documented
        if "exported_from" in export_info and export_info["exported_from"]:
            return "experimental"

        # Internal: Not exported
        return "internal"

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = ["__pycache__", ".git", "build", "dist", ".eggs", "test_"]
        path_str = str(path)
        return any(pattern in path_str for pattern in skip_patterns)

    def save_to_json(self, output_path: Path) -> None:
        """Save API audit to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        symbols = self.analyze()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {
            "total_symbols": len(symbols),
            "by_tier": {
                "core": len([s for s in symbols if s.stability_tier == "core"]),
                "supported": len([s for s in symbols if s.stability_tier == "supported"]),
                "experimental": len([s for s in symbols if s.stability_tier == "experimental"]),
                "internal": len([s for s in symbols if s.stability_tier == "internal"]),
            },
            "symbols": [asdict(symbol) for symbol in symbols],
        }

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Public API audit saved to {output_path}")


def main():
    """CLI entry point for API auditing."""
    import sys

    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])
    else:
        repo_root = Path.cwd()

    auditor = PublicAPIAuditor(repo_root)
    output_path = repo_root / "build" / "quality" / "public_api.json"
    auditor.save_to_json(output_path)

    # Print summary
    symbols = auditor.analyze()
    by_tier = defaultdict(int)
    for symbol in symbols:
        by_tier[symbol.stability_tier] += 1

    print(f"\nPublic API Audit Summary:")
    print(f"  Total symbols: {len(symbols)}")
    print(f"  Core: {by_tier['core']}")
    print(f"  Supported: {by_tier['supported']}")
    print(f"  Experimental: {by_tier['experimental']}")


if __name__ == "__main__":
    main()
