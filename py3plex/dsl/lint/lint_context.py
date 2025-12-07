"""Lint context for DSL linting.

Context object that holds all shared state for lint rules.
"""

from dataclasses import dataclass
from typing import Optional
from .schema import SchemaProvider
from .types import TypeEnvironment


@dataclass
class LintContext:
    """Context for DSL linting.
    
    Contains all shared state needed by lint rules.
    
    Attributes:
        query: The original query string
        schema: Optional schema provider for network information
        type_env: Type environment with inferred types
    """
    query: str
    schema: Optional[SchemaProvider]
    type_env: TypeEnvironment
