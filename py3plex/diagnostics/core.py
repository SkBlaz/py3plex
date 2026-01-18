"""Core diagnostic types and infrastructure.

This module defines the fundamental diagnostic model used throughout py3plex.
All errors, warnings, and informational messages should emit Diagnostic objects.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional
from enum import Enum


class DiagnosticSeverity(str, Enum):
    """Severity level for diagnostics."""
    
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    

@dataclass
class FixSuggestion:
    """A concrete, actionable fix for a diagnostic.
    
    Attributes:
        description: Human-readable description of the fix
        replacement: Suggested replacement code/text (if applicable)
        example: Example of correct usage (optional)
    """
    
    description: str
    replacement: Optional[str] = None
    example: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class DiagnosticContext:
    """Context information for a diagnostic.
    
    Attributes:
        ast_node: AST node type where error occurred (e.g., "WhereClause")
        builder_method: Builder method name (e.g., "where", "compute")
        query_fragment: Fragment of query that caused the issue
        file_path: File path if applicable
        line_number: Line number if applicable
        column_number: Column number if applicable
        additional: Any additional context
    """
    
    ast_node: Optional[str] = None
    builder_method: Optional[str] = None
    query_fragment: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    additional: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        for k, v in asdict(self).items():
            if v is not None:
                if k == "additional":
                    result.update(v)
                else:
                    result[k] = v
        return result


@dataclass
class Diagnostic:
    """A diagnostic message with structured information.
    
    This is the core diagnostic object used throughout py3plex. It provides:
    - A stable error code for programmatic handling
    - Human-readable message explaining what went wrong
    - Context about where the issue occurred
    - Explanation of why it happened
    - Concrete fixes and suggestions
    - Related documentation and APIs
    
    Attributes:
        severity: Severity level (error, warning, info)
        code: Stable error code (e.g., "DSL_SEM_001")
        message: Human-readable summary
        context: Context information (AST node, query fragment, etc.)
        cause: Explanation of why this happened (conceptual)
        fixes: List of concrete actionable fixes
        related: Related methods, builders, docs anchors
    """
    
    severity: DiagnosticSeverity
    code: str
    message: str
    context: Optional[DiagnosticContext] = None
    cause: Optional[str] = None
    fixes: List[FixSuggestion] = field(default_factory=list)
    related: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns stable, machine-readable representation suitable for:
        - LLM consumption
        - Test snapshots
        - API responses
        """
        result = {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
        }
        
        if self.context:
            result["context"] = self.context.to_dict()
        
        if self.cause:
            result["cause"] = self.cause
        
        if self.fixes:
            result["fixes"] = [fix.to_dict() for fix in self.fixes]
        
        if self.related:
            result["related"] = self.related
        
        return result
    
    def to_json(self, indent: Optional[int] = 2) -> str:
        """Convert to JSON string.
        
        Args:
            indent: JSON indentation level (None for compact)
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Diagnostic":
        """Create Diagnostic from dictionary.
        
        Args:
            data: Dictionary representation
        
        Returns:
            Diagnostic instance
        """
        context_data = data.get("context")
        context = DiagnosticContext(**context_data) if context_data else None
        
        fixes_data = data.get("fixes", [])
        fixes = [FixSuggestion(**fix) for fix in fixes_data]
        
        return cls(
            severity=DiagnosticSeverity(data["severity"]),
            code=data["code"],
            message=data["message"],
            context=context,
            cause=data.get("cause"),
            fixes=fixes,
            related=data.get("related", []),
        )
    
    def format(self, use_color: bool = True) -> str:
        """Format the diagnostic as a human-readable message.
        
        Args:
            use_color: Whether to use ANSI colors (default: True)
        
        Returns:
            Formatted string
        """
        from py3plex.errors import Colors
        
        lines = []
        
        # Header: severity[code]: message
        if use_color and Colors.supports_color():
            color = {
                DiagnosticSeverity.ERROR: Colors.RED,
                DiagnosticSeverity.WARNING: Colors.YELLOW,
                DiagnosticSeverity.INFO: Colors.BLUE,
            }.get(self.severity, Colors.WHITE)
            
            header = (
                f"{Colors.BOLD}{color}{self.severity.value}{Colors.RESET}"
                f"{Colors.BOLD}[{self.code}]{Colors.RESET}: "
                f"{self.message}"
            )
        else:
            header = f"{self.severity.value}[{self.code}]: {self.message}"
        
        lines.append(header)
        
        # Context
        if self.context:
            if self.context.builder_method:
                lines.append(f"  Location: .{self.context.builder_method}()")
            if self.context.query_fragment:
                lines.append(f"  Fragment: {self.context.query_fragment}")
            if self.context.ast_node:
                lines.append(f"  AST Node: {self.context.ast_node}")
        
        # Cause
        if self.cause:
            lines.append("")
            if use_color and Colors.supports_color():
                lines.append(f"{Colors.CYAN}Cause:{Colors.RESET}")
            else:
                lines.append("Cause:")
            lines.append(f"  {self.cause}")
        
        # Fixes
        if self.fixes:
            lines.append("")
            for i, fix in enumerate(self.fixes, 1):
                if use_color and Colors.supports_color():
                    lines.append(f"{Colors.GREEN}Fix {i}:{Colors.RESET} {fix.description}")
                else:
                    lines.append(f"Fix {i}: {fix.description}")
                
                if fix.replacement:
                    if use_color and Colors.supports_color():
                        lines.append(f"  {Colors.GREEN}{fix.replacement}{Colors.RESET}")
                    else:
                        lines.append(f"  {fix.replacement}")
                
                if fix.example:
                    lines.append(f"  Example: {fix.example}")
        
        # Related
        if self.related:
            lines.append("")
            if use_color and Colors.supports_color():
                lines.append(f"{Colors.BLUE}Related:{Colors.RESET}")
            else:
                lines.append("Related:")
            for item in self.related:
                lines.append(f"  - {item}")
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        """Return formatted diagnostic message."""
        return self.format(use_color=True)


@dataclass
class DiagnosticResult:
    """Container for multiple diagnostics.
    
    This is used to collect diagnostics during query execution,
    algorithm runs, or other operations.
    
    Attributes:
        diagnostics: List of diagnostic messages
    """
    
    diagnostics: List[Diagnostic] = field(default_factory=list)
    
    def add(self, diagnostic: Diagnostic) -> None:
        """Add a diagnostic to the collection."""
        self.diagnostics.append(diagnostic)
    
    def has_errors(self) -> bool:
        """Check if any diagnostics are errors."""
        return any(d.severity == DiagnosticSeverity.ERROR for d in self.diagnostics)
    
    def has_warnings(self) -> bool:
        """Check if any diagnostics are warnings."""
        return any(d.severity == DiagnosticSeverity.WARNING for d in self.diagnostics)
    
    def errors(self) -> List[Diagnostic]:
        """Get all error diagnostics."""
        return [d for d in self.diagnostics if d.severity == DiagnosticSeverity.ERROR]
    
    def warnings(self) -> List[Diagnostic]:
        """Get all warning diagnostics."""
        return [d for d in self.diagnostics if d.severity == DiagnosticSeverity.WARNING]
    
    def infos(self) -> List[Diagnostic]:
        """Get all info diagnostics."""
        return [d for d in self.diagnostics if d.severity == DiagnosticSeverity.INFO]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "summary": {
                "total": len(self.diagnostics),
                "errors": len(self.errors()),
                "warnings": len(self.warnings()),
                "infos": len(self.infos()),
            }
        }
    
    def to_json(self, indent: Optional[int] = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def format(self, use_color: bool = True) -> str:
        """Format all diagnostics as human-readable messages."""
        if not self.diagnostics:
            return ""
        
        return "\n\n".join(d.format(use_color=use_color) for d in self.diagnostics)
    
    def __str__(self) -> str:
        """Return formatted diagnostics."""
        return self.format(use_color=True)
