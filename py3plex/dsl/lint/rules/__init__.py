"""Lint rules for DSL queries.

This module contains all lint rules and handles their registration.
"""

from .base import LintRule, RuleRegistry, register_rule, get_all_rules, clear_rules
from .dsl001_unknown_layer import UnknownLayerRule
from .dsl002_unknown_attribute import UnknownAttributeRule
from .dsl101_type_mismatch import TypeMismatchRule
from .dsl201_unsatisfiable import UnsatisfiablePredicateRule
from .dsl202_redundant import RedundantPredicateRule
from .perf301_full_scan import FullScanWarningRule
from .perf302_cross_layer import CrossLayerJoinWarningRule


# Initialize and register all default rules
def init_default_rules():
    """Initialize and register all default lint rules."""
    rules = [
        UnknownLayerRule(),
        UnknownAttributeRule(),
        TypeMismatchRule(),
        UnsatisfiablePredicateRule(),
        RedundantPredicateRule(),
        FullScanWarningRule(),
        CrossLayerJoinWarningRule(),
    ]
    
    for rule in rules:
        register_rule(rule)


# Register rules on module import
init_default_rules()


__all__ = [
    "LintRule",
    "RuleRegistry",
    "register_rule",
    "get_all_rules",
    "clear_rules",
    "init_default_rules",
    # Individual rules
    "UnknownLayerRule",
    "UnknownAttributeRule",
    "TypeMismatchRule",
    "UnsatisfiablePredicateRule",
    "RedundantPredicateRule",
    "FullScanWarningRule",
    "CrossLayerJoinWarningRule",
]
