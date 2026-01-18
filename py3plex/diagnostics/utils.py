"""Utility functions for diagnostics.

This module provides helper functions for fuzzy matching, similarity detection,
and "did you mean?" suggestions.
"""

import difflib
from typing import List, Optional, Tuple


def fuzzy_match(
    query: str,
    candidates: List[str],
    cutoff: float = 0.6,
    max_suggestions: int = 3
) -> List[Tuple[str, float]]:
    """Find fuzzy matches from a list of candidates.
    
    Uses difflib's SequenceMatcher for similarity scoring.
    
    Args:
        query: The string to match
        candidates: List of candidate strings
        cutoff: Minimum similarity ratio (0.0 to 1.0)
        max_suggestions: Maximum number of suggestions to return
    
    Returns:
        List of (candidate, similarity_score) tuples, sorted by score descending
    """
    if not candidates:
        return []
    
    # Use difflib for fuzzy matching
    matches = difflib.get_close_matches(
        query, candidates, n=max_suggestions, cutoff=cutoff
    )
    
    # Calculate scores for each match
    results = []
    for match in matches:
        score = difflib.SequenceMatcher(None, query.lower(), match.lower()).ratio()
        results.append((match, score))
    
    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results


def did_you_mean(
    query: str,
    candidates: List[str],
    cutoff: float = 0.6
) -> Optional[str]:
    """Get the best "did you mean?" suggestion.
    
    Args:
        query: The string to match
        candidates: List of candidate strings
        cutoff: Minimum similarity ratio (0.0 to 1.0)
    
    Returns:
        Best matching candidate, or None if no good match found
    """
    matches = fuzzy_match(query, candidates, cutoff=cutoff, max_suggestions=1)
    return matches[0][0] if matches else None


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
    
    Returns:
        Edit distance (number of single-character edits needed)
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def suggest_similar_field(
    field: str,
    known_fields: List[str],
    max_distance: int = 3
) -> Optional[str]:
    """Suggest similar field name based on Levenshtein distance.
    
    Args:
        field: Unknown field name
        known_fields: List of valid field names
        max_distance: Maximum edit distance for suggestions
    
    Returns:
        Most similar field name, or None if none are close enough
    """
    if not known_fields:
        return None
    
    best_match = None
    best_distance = max_distance + 1
    
    for known in known_fields:
        distance = levenshtein_distance(field.lower(), known.lower())
        if distance < best_distance:
            best_distance = distance
            best_match = known
    
    return best_match if best_distance <= max_distance else None


def suggest_builder_method(
    method: str,
    known_methods: List[str]
) -> Optional[str]:
    """Suggest similar builder method name.
    
    Handles common patterns like:
    - .perlayer() → .per_layer()
    - .toplimit() → .top_k() or .limit()
    
    Args:
        method: Unknown method name
        known_methods: List of valid method names
    
    Returns:
        Most similar method name, or None
    """
    # Try direct fuzzy match first
    suggestion = did_you_mean(method, known_methods, cutoff=0.6)
    if suggestion:
        return suggestion
    
    # Handle specific common mistakes
    method_lower = method.lower()
    
    # Remove underscores and try again (perlayer → per_layer)
    if "_" not in method_lower:
        with_underscores = []
        for known in known_methods:
            if known.replace("_", "").lower() == method_lower:
                with_underscores.append(known)
        if with_underscores:
            return with_underscores[0]
    
    return None
