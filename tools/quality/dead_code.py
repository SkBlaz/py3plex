"""Dead code detector for py3plex codebase.

This module identifies potentially dead code using multiple signals:
- Unreferenced symbols in the repository
- Unimported modules
- Functions/classes never called (best-effort static analysis)
- Whitelisting for special cases (plugins, CLI entrypoints, etc.)
"""

import ast
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
import yaml


@dataclass
class DeadCodeItem:
    """Represents a potentially dead code item."""

    file: str
    line: int
    symbol: str
    type: str  # function, class, method, module
    score: float  # 0-1, higher = more likely dead
    signals: List[str]
    reason_codes: List[str]
    suggested_action: str  # remove, deprecate, keep-but-comment, add-to-whitelist


class DeadCodeDetector:
    """Detects dead code using multiple signals."""

    def __init__(self, repo_root: Path, whitelist_path: Optional[Path] = None):
        """Initialize the detector.

        Args:
            repo_root: Root directory of the repository
            whitelist_path: Path to whitelist YAML file
        """
        self.repo_root = Path(repo_root)
        self.package_root = self.repo_root / "py3plex"
        self.whitelist = self._load_whitelist(whitelist_path)
        self.symbols: Dict[str, Dict] = {}

    def _load_whitelist(self, whitelist_path: Optional[Path]) -> Dict:
        """Load whitelist configuration."""
        if whitelist_path is None:
            whitelist_path = self.repo_root / "tools" / "whitelist.yml"

        if not whitelist_path.exists():
            return {
                "plugin_entrypoints": [],
                "reflection_used": [],
                "side_effect_modules": [],
                "registries": [],
                "cli_commands": [],
            }

        with open(whitelist_path, "r") as f:
            return yaml.safe_load(f) or {}

    def analyze(self) -> List[DeadCodeItem]:
        """Analyze codebase for dead code.

        Returns:
            List of DeadCodeItem objects
        """
        # Step 1: Extract all symbols
        self._extract_symbols()

        # Step 2: Check references for each symbol
        dead_items = []
        for symbol_name, symbol_info in self.symbols.items():
            if self._is_whitelisted(symbol_name, symbol_info):
                continue

            signals, score = self._calculate_dead_score(symbol_name, symbol_info)

            if score > 0.3:  # Threshold for reporting
                item = DeadCodeItem(
                    file=symbol_info["file"],
                    line=symbol_info["line"],
                    symbol=symbol_name,
                    type=symbol_info["type"],
                    score=score,
                    signals=signals,
                    reason_codes=self._get_reason_codes(signals),
                    suggested_action=self._suggest_action(score, symbol_info),
                )
                dead_items.append(item)

        return sorted(dead_items, key=lambda x: x.score, reverse=True)

    def _extract_symbols(self) -> None:
        """Extract all symbols from Python files."""
        for py_file in self.package_root.rglob("*.py"):
            if self._should_skip(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        self._record_symbol(py_file, node, "function")
                    elif isinstance(node, ast.ClassDef):
                        self._record_symbol(py_file, node, "class")
            except Exception:
                pass  # Skip files that can't be parsed

    def _record_symbol(self, file: Path, node: ast.AST, symbol_type: str) -> None:
        """Record a symbol for analysis."""
        name = node.name
        # Skip private symbols for now (many intentionally unused)
        if name.startswith("_") and not name.startswith("__"):
            return

        rel_path = str(file.relative_to(self.repo_root))
        full_name = f"{rel_path}::{name}"

        self.symbols[full_name] = {
            "name": name,
            "file": rel_path,
            "line": node.lineno,
            "type": symbol_type,
        }

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "__pycache__",
            ".git",
            "build",
            "dist",
            ".eggs",
            "test_",
            "conftest",
            "infomap.py",
        ]
        path_str = str(path)
        return any(pattern in path_str for pattern in skip_patterns)

    def _is_whitelisted(self, symbol_name: str, symbol_info: Dict) -> bool:
        """Check if symbol is whitelisted."""
        name = symbol_info["name"]

        # Check various whitelist categories
        for category in [
            "plugin_entrypoints",
            "reflection_used",
            "registries",
            "cli_commands",
        ]:
            if name in self.whitelist.get(category, []):
                return True

        # Check if in side-effect module
        for module in self.whitelist.get("side_effect_modules", []):
            if module in symbol_info["file"]:
                return True

        return False

    def _calculate_dead_score(
        self, symbol_name: str, symbol_info: Dict
    ) -> tuple[List[str], float]:
        """Calculate dead code score using multiple signals.

        Returns:
            Tuple of (signals, score)
        """
        signals = []
        score = 0.0

        # Signal 1: Unreferenced in repo (ripgrep)
        name = symbol_info["name"]
        if not self._has_references(name):
            signals.append("unreferenced")
            score += 0.4

        # Signal 2: Not in __init__.py exports
        if not self._is_exported(symbol_info["file"], name):
            signals.append("not_exported")
            score += 0.2

        # Signal 3: Function/class appears unused in imports
        if not self._appears_in_imports(name):
            signals.append("not_imported")
            score += 0.3

        # Signal 4: No tests reference it
        if not self._has_test_references(name):
            signals.append("no_tests")
            score += 0.1

        return signals, min(score, 1.0)

    def _has_references(self, symbol_name: str) -> bool:
        """Check if symbol has references using ripgrep."""
        try:
            result = subprocess.run(
                [
                    "rg",
                    "--count",
                    "--type",
                    "py",
                    rf"\b{symbol_name}\b",
                    str(self.package_root),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # If found in more than 1 file (definition + usage), consider referenced
            line_count = len([l for l in result.stdout.strip().split("\n") if l])
            return line_count > 1
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # If ripgrep not available or timeout, be conservative
            return True

    def _is_exported(self, file: str, symbol: str) -> bool:
        """Check if symbol is exported in __init__.py."""
        init_path = Path(file).parent / "__init__.py"
        full_init = self.repo_root / init_path

        if not full_init.exists():
            return False

        try:
            with open(full_init, "r") as f:
                content = f.read()
                return symbol in content and "__all__" in content
        except Exception:
            return False

    def _appears_in_imports(self, symbol: str) -> bool:
        """Check if symbol appears in import statements."""
        try:
            result = subprocess.run(
                [
                    "rg",
                    "--count",
                    "--type",
                    "py",
                    rf"(from .* import .*{symbol}|import .*{symbol})",
                    str(self.repo_root),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True

    def _has_test_references(self, symbol: str) -> bool:
        """Check if symbol is referenced in tests."""
        tests_dir = self.repo_root / "tests"
        if not tests_dir.exists():
            return False

        try:
            result = subprocess.run(
                [
                    "rg",
                    "--count",
                    "--type",
                    "py",
                    rf"\b{symbol}\b",
                    str(tests_dir),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_reason_codes(self, signals: List[str]) -> List[str]:
        """Convert signals to human-readable reason codes."""
        code_map = {
            "unreferenced": "NO_REFERENCES",
            "not_exported": "NOT_IN_PUBLIC_API",
            "not_imported": "NEVER_IMPORTED",
            "no_tests": "NO_TEST_COVERAGE",
        }
        return [code_map.get(s, s.upper()) for s in signals]

    def _suggest_action(self, score: float, symbol_info: Dict) -> str:
        """Suggest action based on score."""
        if score >= 0.8:
            return "remove"
        elif score >= 0.6:
            return "deprecate"
        elif score >= 0.4:
            return "keep-but-comment"
        else:
            return "add-to-whitelist"

    def save_to_json(self, output_path: Path) -> None:
        """Save analysis results to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        items = self.analyze()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {
            "total_candidates": len(items),
            "high_confidence": len([i for i in items if i.score >= 0.7]),
            "medium_confidence": len([i for i in items if 0.4 <= i.score < 0.7]),
            "low_confidence": len([i for i in items if i.score < 0.4]),
            "items": [asdict(item) for item in items],
        }

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Dead code analysis saved to {output_path}")


def main():
    """CLI entry point for dead code detection."""
    import sys

    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])
    else:
        repo_root = Path.cwd()

    detector = DeadCodeDetector(repo_root)
    output_path = repo_root / "build" / "quality" / "dead_code.json"
    detector.save_to_json(output_path)

    # Print summary
    items = detector.analyze()
    high_conf = [i for i in items if i.score >= 0.7]
    print(f"\nDead Code Detection Summary:")
    print(f"  Total candidates: {len(items)}")
    print(f"  High confidence: {len(high_conf)}")
    if high_conf:
        print(f"\n  Top 5 candidates:")
        for item in high_conf[:5]:
            print(f"    - {item.file}:{item.line} {item.symbol} (score: {item.score:.2f})")


if __name__ == "__main__":
    main()
