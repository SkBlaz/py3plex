"""Program diffing utilities.

This module implements structural and semantic diffing for GraphPrograms.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import difflib


class DiffType(Enum):
    """Type of difference."""
    IDENTICAL = "identical"
    STRUCTURAL = "structural"  # AST structure changed
    SEMANTIC = "semantic"  # Semantics changed (types, filters, etc.)
    OPTIMIZATION = "optimization"  # Optimization level changed
    COST = "cost"  # Cost estimates differ
    UQ = "uq"  # UQ parameters changed


@dataclass
class DiffNode:
    """A difference between two programs.
    
    Attributes:
        diff_type: Type of difference
        path: Path in AST where difference occurs
        left_value: Value in first program
        right_value: Value in second program
        description: Human-readable description
        impact: Impact level ("low", "medium", "high")
    """
    diff_type: DiffType
    path: str
    left_value: Any
    right_value: Any
    description: str
    impact: str = "medium"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": self.diff_type.value,
            "path": self.path,
            "left": str(self.left_value),
            "right": str(self.right_value),
            "description": self.description,
            "impact": self.impact,
        }


@dataclass
class ProgramDiff:
    """Complete diff between two programs.
    
    Attributes:
        differences: List of differences found
        hash_changed: Whether program hashes differ
        type_changed: Whether type signatures differ
        cost_impact: Estimated cost impact (ratio)
        cache_invalidated: Whether cache would be invalidated
    """
    differences: List[DiffNode]
    hash_changed: bool
    type_changed: bool
    cost_impact: Optional[float] = None
    cache_invalidated: bool = True
    
    def is_identical(self) -> bool:
        """Check if programs are identical."""
        return len(self.differences) == 0
    
    def summary(self) -> str:
        """Get human-readable summary."""
        if self.is_identical():
            return "Programs are identical"
        
        lines = [f"Found {len(self.differences)} difference(s):"]
        for diff in self.differences:
            lines.append(f"  - {diff.description} (impact: {diff.impact})")
        
        if self.hash_changed:
            lines.append("\nProgram hash changed - cache invalidated")
        
        if self.type_changed:
            lines.append("Type signature changed")
        
        if self.cost_impact is not None:
            if self.cost_impact > 1.0:
                lines.append(f"Cost increased by {(self.cost_impact - 1.0) * 100:.1f}%")
            elif self.cost_impact < 1.0:
                lines.append(f"Cost decreased by {(1.0 - self.cost_impact) * 100:.1f}%")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "differences": [d.to_dict() for d in self.differences],
            "hash_changed": self.hash_changed,
            "type_changed": self.type_changed,
            "cost_impact": self.cost_impact,
            "cache_invalidated": self.cache_invalidated,
            "summary": self.summary(),
        }


def diff_programs(program1: "GraphProgram", program2: "GraphProgram") -> ProgramDiff:
    """Compare two GraphPrograms and generate diff.
    
    Args:
        program1: First program
        program2: Second program
        
    Returns:
        ProgramDiff object with all differences
    """
    differences = []
    
    # Compare hashes
    hash1 = program1.hash()
    hash2 = program2.hash()
    hash_changed = hash1 != hash2
    
    # Compare type signatures
    type1 = str(program1.type_signature)
    type2 = str(program2.type_signature)
    type_changed = type1 != type2
    
    if type_changed:
        differences.append(DiffNode(
            diff_type=DiffType.SEMANTIC,
            path="type_signature",
            left_value=type1,
            right_value=type2,
            description="Type signature changed",
            impact="high"
        ))
    
    # Compare AST structure (simplified)
    ast1_str = _ast_to_string(program1.canonical_ast)
    ast2_str = _ast_to_string(program2.canonical_ast)
    
    if ast1_str != ast2_str:
        # Use difflib to find differences
        diff_lines = list(difflib.unified_diff(
            ast1_str.split('\n'),
            ast2_str.split('\n'),
            lineterm='',
            n=0
        ))
        
        if diff_lines:
            differences.append(DiffNode(
                diff_type=DiffType.STRUCTURAL,
                path="ast",
                left_value=ast1_str[:100],
                right_value=ast2_str[:100],
                description=f"AST structure differs ({len(diff_lines)} line changes)",
                impact="high"
            ))
    
    # Compare metadata
    meta1 = program1.metadata
    meta2 = program2.metadata
    
    if meta1.dsl_version != meta2.dsl_version:
        differences.append(DiffNode(
            diff_type=DiffType.SEMANTIC,
            path="metadata.dsl_version",
            left_value=meta1.dsl_version,
            right_value=meta2.dsl_version,
            description="DSL version changed",
            impact="medium"
        ))
    
    # Estimate cost impact (simplified)
    cost_impact = None
    try:
        from .cost import CostModel, GraphStats
        cost_model = CostModel()
        # Use dummy stats for comparison
        stats = GraphStats(num_nodes=1000, num_edges=5000, num_layers=2)
        cost1 = cost_model.estimate_program_cost(program1, stats)
        cost2 = cost_model.estimate_program_cost(program2, stats)
        if cost1.time_estimate_seconds > 0:
            cost_impact = cost2.time_estimate_seconds / cost1.time_estimate_seconds
    except Exception:
        pass
    
    return ProgramDiff(
        differences=differences,
        hash_changed=hash_changed,
        type_changed=type_changed,
        cost_impact=cost_impact,
        cache_invalidated=hash_changed,
    )


def _ast_to_string(ast_node: Any) -> str:
    """Convert AST node to normalized string representation."""
    if ast_node is None:
        return "None"
    
    # Get type name
    type_name = type(ast_node).__name__
    
    # Handle dataclasses
    if hasattr(ast_node, "__dataclass_fields__"):
        fields = []
        for field_name in sorted(ast_node.__dataclass_fields__.keys()):
            value = getattr(ast_node, field_name)
            if isinstance(value, list):
                fields.append(f"{field_name}=[{len(value)} items]")
            elif hasattr(value, "__dataclass_fields__"):
                fields.append(f"{field_name}=<{type(value).__name__}>")
            else:
                fields.append(f"{field_name}={repr(value)}")
        return f"{type_name}({', '.join(fields)})"
    
    return f"{type_name}({repr(ast_node)})"
