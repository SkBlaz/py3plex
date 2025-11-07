"""
Term parsers for working with semantic data.

This module provides a unified interface to term parsing utilities.
The actual implementations are in py3plex.algorithms.term_parsers.
"""

# Import from the main term_parsers module to avoid duplication
from py3plex.algorithms.term_parsers import (
    parse_gaf_file,
    read_termlist,
    read_topology_mappings,
    read_uniprot_GO,
)

__all__ = [
    "read_termlist",
    "parse_gaf_file",
    "read_topology_mappings",
    "read_uniprot_GO",
]
