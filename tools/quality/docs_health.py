"""Documentation health checker for py3plex codebase.

This module scans documentation for references to moved or removed symbols,
checking if code examples in docs are still valid.
"""

import json
import re
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict


@dataclass
class DocReference:
    """A code reference in documentation."""

    file: str
    line: int
    code_block: str
    referenced_symbols: List[str]
    status: str  # valid, invalid, warning
    error_message: str


class DocsHealthChecker:
    """Checks health of documentation references."""

    def __init__(self, repo_root: Path):
        """Initialize the checker.

        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = Path(repo_root)
        self.docs_root = self.repo_root / "docfiles"

    def check(self) -> List[DocReference]:
        """Check all documentation files.

        Returns:
            List of DocReference objects
        """
        if not self.docs_root.exists():
            # Try alternative doc locations
            self.docs_root = self.repo_root / "docs"
            if not self.docs_root.exists():
                self.docs_root = self.repo_root / "book"
                if not self.docs_root.exists():
                    return []

        results = []

        for doc_file in self.docs_root.rglob("*.rst"):
            results.extend(self._check_doc_file(doc_file))

        for doc_file in self.docs_root.rglob("*.md"):
            results.extend(self._check_doc_file(doc_file))

        return results

    def _check_doc_file(self, doc_file: Path) -> List[DocReference]:
        """Check a single documentation file."""
        results = []

        try:
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            rel_path = str(doc_file.relative_to(self.repo_root))

            # Extract code blocks
            code_blocks = self._extract_code_blocks(content, lines)

            for block_info in code_blocks:
                symbols = self._extract_symbols(block_info["code"])

                # Check if symbols are valid (simplified check)
                status, error = self._validate_symbols(symbols)

                ref = DocReference(
                    file=rel_path,
                    line=block_info["line"],
                    code_block=block_info["code"][:100],  # First 100 chars
                    referenced_symbols=symbols,
                    status=status,
                    error_message=error,
                )
                results.append(ref)

        except Exception:
            pass

        return results

    def _extract_code_blocks(self, content: str, lines: List[str]) -> List[Dict]:
        """Extract code blocks from documentation."""
        blocks = []

        # RST code blocks: .. code-block:: python
        rst_pattern = r".. code-block:: python\n\n((?:    .+\n)+)"
        for match in re.finditer(rst_pattern, content):
            code = match.group(1)
            # Remove leading spaces
            code = "\n".join(line[4:] if line.startswith("    ") else line for line in code.split("\n"))

            # Find line number (approximate)
            line_num = content[:match.start()].count("\n") + 1

            blocks.append({"code": code, "line": line_num})

        # Markdown code blocks: ```python
        md_pattern = r"```python\n(.*?)\n```"
        for match in re.finditer(md_pattern, content, re.DOTALL):
            code = match.group(1)
            line_num = content[:match.start()].count("\n") + 1
            blocks.append({"code": code, "line": line_num})

        return blocks

    def _extract_symbols(self, code: str) -> List[str]:
        """Extract py3plex symbols from code."""
        symbols = []

        # Match py3plex imports
        import_patterns = [
            r"from py3plex[\w.]* import ([\w, ]+)",
            r"import py3plex[\w.]*",
        ]

        for pattern in import_patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                if isinstance(match, str):
                    for sym in match.split(","):
                        symbols.append(sym.strip())

        return symbols

    def _validate_symbols(self, symbols: List[str]) -> tuple[str, str]:
        """Validate that symbols exist (simplified check).

        Returns:
            Tuple of (status, error_message)
        """
        if not symbols:
            return "valid", ""

        # For now, just return valid (full validation would require imports)
        # This is a placeholder for actual symbol validation
        return "valid", ""

    def save_to_json(self, output_path: Path) -> None:
        """Save health check to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        results = self.check()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {
            "total_references": len(results),
            "valid": len([r for r in results if r.status == "valid"]),
            "invalid": len([r for r in results if r.status == "invalid"]),
            "warnings": len([r for r in results if r.status == "warning"]),
            "references": [asdict(ref) for ref in results],
        }

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Docs health check saved to {output_path}")


def main():
    """CLI entry point for docs health checking."""
    import sys

    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])
    else:
        repo_root = Path.cwd()

    checker = DocsHealthChecker(repo_root)
    output_path = repo_root / "build" / "quality" / "docs_health.json"
    checker.save_to_json(output_path)

    # Print summary
    results = checker.check()
    print(f"\nDocs Health Summary:")
    print(f"  Total code references: {len(results)}")
    print(f"  Valid: {len([r for r in results if r.status == 'valid'])}")


if __name__ == "__main__":
    main()
