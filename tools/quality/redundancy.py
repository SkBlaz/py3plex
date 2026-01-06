"""Redundancy and duplication detector for py3plex codebase.

This module detects duplicate code at three levels:
1. Exact duplicates (identical function bodies)
2. Near duplicates (token-based similarity)
3. Semantic duplicates (same signature + similar call patterns)
"""

import ast
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class DuplicationCluster:
    """Represents a cluster of duplicate code."""

    cluster_id: str
    similarity_type: str  # exact, near, semantic
    similarity_score: float
    members: List[Dict]  # file, line, symbol, code_hash
    canonical_location: str
    suggested_action: str


class RedundancyDetector:
    """Detects code redundancy and duplication."""

    def __init__(self, repo_root: Path):
        """Initialize the detector.

        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = Path(repo_root)
        self.package_root = self.repo_root / "py3plex"
        self.functions: Dict[str, Dict] = {}
        self.hash_to_functions: Dict[str, List[str]] = defaultdict(list)

    def analyze(self) -> List[DuplicationCluster]:
        """Analyze codebase for duplications.

        Returns:
            List of DuplicationCluster objects
        """
        # Step 1: Extract all functions and their hashes
        self._extract_functions()

        # Step 2: Find exact duplicates
        exact_clusters = self._find_exact_duplicates()

        # Step 3: Find near duplicates (simplified token-based)
        near_clusters = self._find_near_duplicates()

        # Step 4: Find semantic duplicates (signature similarity)
        semantic_clusters = self._find_semantic_duplicates()

        all_clusters = exact_clusters + near_clusters + semantic_clusters
        return sorted(all_clusters, key=lambda x: x.similarity_score, reverse=True)

    def _extract_functions(self) -> None:
        """Extract all functions and compute their hashes."""
        for py_file in self.package_root.rglob("*.py"):
            if self._should_skip(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        self._record_function(py_file, node, content)
            except Exception:
                pass  # Skip files that can't be parsed

    def _record_function(self, file: Path, node: ast.FunctionDef, content: str) -> None:
        """Record a function for analysis."""
        rel_path = str(file.relative_to(self.repo_root))

        # Extract function source code
        try:
            func_source = ast.get_source_segment(content, node)
            if not func_source:
                return
        except Exception:
            return

        # Compute normalized hash (remove whitespace/comments for comparison)
        normalized = self._normalize_code(func_source)
        code_hash = hashlib.md5(normalized.encode()).hexdigest()

        # Record function
        func_key = f"{rel_path}::{node.name}"
        self.functions[func_key] = {
            "file": rel_path,
            "line": node.lineno,
            "name": node.name,
            "hash": code_hash,
            "source": func_source,
            "args": [arg.arg for arg in node.args.args],
            "num_lines": len(func_source.split("\n")),
        }

        self.hash_to_functions[code_hash].append(func_key)

    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison (remove whitespace, comments)."""
        # Simple normalization: remove leading/trailing whitespace from each line
        lines = []
        for line in code.split("\n"):
            stripped = line.strip()
            # Skip comments and docstrings (simplified)
            if stripped.startswith("#"):
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            lines.append(stripped)
        return "\n".join(lines)

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
            "examples",  # Examples may intentionally duplicate
        ]
        path_str = str(path)
        return any(pattern in path_str for pattern in skip_patterns)

    def _find_exact_duplicates(self) -> List[DuplicationCluster]:
        """Find exact duplicates (identical normalized code)."""
        clusters = []

        for code_hash, func_keys in self.hash_to_functions.items():
            if len(func_keys) < 2:
                continue

            # Skip very small functions (< 3 lines)
            func_info = self.functions[func_keys[0]]
            if func_info["num_lines"] < 3:
                continue

            members = []
            for func_key in func_keys:
                func = self.functions[func_key]
                members.append(
                    {
                        "file": func["file"],
                        "line": func["line"],
                        "symbol": func["name"],
                        "code_hash": code_hash,
                    }
                )

            # Choose canonical location (first alphabetically)
            canonical = sorted(members, key=lambda x: x["file"])[0]

            cluster = DuplicationCluster(
                cluster_id=f"exact_{code_hash[:8]}",
                similarity_type="exact",
                similarity_score=1.0,
                members=members,
                canonical_location=f"{canonical['file']}:{canonical['line']}",
                suggested_action="unify_into_helper",
            )
            clusters.append(cluster)

        return clusters

    def _find_near_duplicates(self) -> List[DuplicationCluster]:
        """Find near duplicates using token-based similarity."""
        clusters = []
        processed = set()

        func_list = list(self.functions.items())

        for i, (key1, func1) in enumerate(func_list):
            if key1 in processed:
                continue

            similar_funcs = [key1]

            for key2, func2 in func_list[i + 1 :]:
                if key2 in processed:
                    continue

                # Skip if already exact duplicates
                if func1["hash"] == func2["hash"]:
                    continue

                # Check token similarity
                similarity = self._token_similarity(func1["source"], func2["source"])

                if similarity >= 0.8:  # 80% similar
                    similar_funcs.append(key2)

            if len(similar_funcs) >= 2:
                # Create cluster
                members = []
                for func_key in similar_funcs:
                    func = self.functions[func_key]
                    members.append(
                        {
                            "file": func["file"],
                            "line": func["line"],
                            "symbol": func["name"],
                            "code_hash": func["hash"],
                        }
                    )
                    processed.add(func_key)

                canonical = sorted(members, key=lambda x: x["file"])[0]

                cluster = DuplicationCluster(
                    cluster_id=f"near_{hashlib.md5(str(similar_funcs).encode()).hexdigest()[:8]}",
                    similarity_type="near",
                    similarity_score=0.8,
                    members=members,
                    canonical_location=f"{canonical['file']}:{canonical['line']}",
                    suggested_action="review_and_unify",
                )
                clusters.append(cluster)

        return clusters

    def _token_similarity(self, code1: str, code2: str) -> float:
        """Calculate token-based similarity between two code snippets."""
        # Simple token similarity: Jaccard index of tokens
        tokens1 = set(self._tokenize(code1))
        tokens2 = set(self._tokenize(code2))

        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        return intersection / union if union > 0 else 0.0

    def _tokenize(self, code: str) -> List[str]:
        """Simple tokenization of code."""
        # Split on whitespace and common delimiters
        import re

        tokens = re.findall(r"\w+|[^\w\s]", code)
        # Filter out very common tokens
        common = {"def", "return", "if", "else", "for", "in", "and", "or"}
        return [t for t in tokens if t not in common]

    def _find_semantic_duplicates(self) -> List[DuplicationCluster]:
        """Find semantic duplicates (same signature, similar structure)."""
        clusters = []

        # Group functions by signature (name + args)
        signature_groups: Dict[str, List[str]] = defaultdict(list)

        for func_key, func_info in self.functions.items():
            signature = f"{func_info['name']}_{len(func_info['args'])}"
            signature_groups[signature].append(func_key)

        # Check for similar signatures
        for signature, func_keys in signature_groups.items():
            if len(func_keys) < 2:
                continue

            # If they have similar names and same arity, flag as potential duplicates
            members = []
            for func_key in func_keys:
                func = self.functions[func_key]
                members.append(
                    {
                        "file": func["file"],
                        "line": func["line"],
                        "symbol": func["name"],
                        "code_hash": func["hash"],
                    }
                )

            if len(members) >= 2:
                canonical = sorted(members, key=lambda x: x["file"])[0]

                cluster = DuplicationCluster(
                    cluster_id=f"semantic_{hashlib.md5(signature.encode()).hexdigest()[:8]}",
                    similarity_type="semantic",
                    similarity_score=0.6,
                    members=members,
                    canonical_location=f"{canonical['file']}:{canonical['line']}",
                    suggested_action="review",
                )
                clusters.append(cluster)

        return clusters

    def save_to_json(self, output_path: Path) -> None:
        """Save analysis results to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        clusters = self.analyze()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {
            "total_clusters": len(clusters),
            "exact_duplicates": len([c for c in clusters if c.similarity_type == "exact"]),
            "near_duplicates": len([c for c in clusters if c.similarity_type == "near"]),
            "semantic_duplicates": len([c for c in clusters if c.similarity_type == "semantic"]),
            "clusters": [asdict(cluster) for cluster in clusters],
        }

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Redundancy analysis saved to {output_path}")


def main():
    """CLI entry point for redundancy detection."""
    import sys

    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])
    else:
        repo_root = Path.cwd()

    detector = RedundancyDetector(repo_root)
    output_path = repo_root / "build" / "quality" / "redundancy.json"
    detector.save_to_json(output_path)

    # Print summary
    clusters = detector.analyze()
    exact = [c for c in clusters if c.similarity_type == "exact"]
    print(f"\nRedundancy Detection Summary:")
    print(f"  Total clusters: {len(clusters)}")
    print(f"  Exact duplicates: {len(exact)}")
    if exact:
        print(f"\n  Top 3 exact duplicate clusters:")
        for cluster in exact[:3]:
            print(f"    - {cluster.cluster_id}: {len(cluster.members)} copies")


if __name__ == "__main__":
    main()
