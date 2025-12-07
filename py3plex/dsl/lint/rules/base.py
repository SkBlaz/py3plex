"""Base classes and protocols for lint rules."""

from typing import Protocol, List, Literal
from ...ast import Query
from ..diagnostic import Diagnostic
from ..lint_context import LintContext


class LintRule(Protocol):
    """Protocol for lint rules.
    
    Each rule implements this protocol to check for specific issues.
    """
    
    code: str
    description: str
    default_severity: Literal["error", "warning", "info", "hint"]
    
    def apply(self, query: Query, context: LintContext) -> List[Diagnostic]:
        """Apply the lint rule to a query.
        
        Args:
            query: The query AST
            context: Lint context with shared state
            
        Returns:
            List of diagnostics found by this rule
        """
        ...


class RuleRegistry:
    """Registry for lint rules."""
    
    def __init__(self):
        """Initialize empty registry."""
        self.rules: List[LintRule] = []
    
    def register(self, rule: LintRule):
        """Register a lint rule.
        
        Args:
            rule: Rule to register
        """
        self.rules.append(rule)
    
    def get_all(self) -> List[LintRule]:
        """Get all registered rules."""
        return self.rules.copy()
    
    def clear(self):
        """Clear all registered rules."""
        self.rules.clear()


# Global rule registry
_global_registry = RuleRegistry()


def register_rule(rule: LintRule):
    """Register a rule in the global registry."""
    _global_registry.register(rule)


def get_all_rules() -> List[LintRule]:
    """Get all registered rules."""
    return _global_registry.get_all()


def clear_rules():
    """Clear all registered rules."""
    _global_registry.clear()
