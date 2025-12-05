"""Error types for dynamics module.

This module provides structured error types with helpful diagnostic information.
Errors include suggestions like "did you mean?" when applicable.
"""

from typing import List, Optional


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _suggest_similar(name: str, known_names: List[str], max_distance: int = 3) -> Optional[str]:
    """Suggest a similar name from known names.

    Args:
        name: The unknown name
        known_names: List of valid names
        max_distance: Maximum Levenshtein distance for suggestions

    Returns:
        The most similar known name, or None if none are close enough
    """
    if not known_names:
        return None

    best_match = None
    best_distance = max_distance + 1

    for known in known_names:
        distance = _levenshtein_distance(name.lower(), known.lower())
        if distance < best_distance:
            best_distance = distance
            best_match = known

    return best_match if best_distance <= max_distance else None


class DynamicsError(Exception):
    """Base exception for all dynamics errors."""

    def __init__(self, message: str, dsl: Optional[str] = None):
        super().__init__(message)
        self.dsl = dsl

    def format_message(self) -> str:
        """Format the error message with context."""
        msg = str(self)

        if self.dsl:
            msg = f"{msg}\n\nDSL:\n{self.dsl}"

        return msg


class UnknownProcessError(DynamicsError):
    """Exception raised when an unknown process is referenced.

    Attributes:
        process: The unknown process name
        known_processes: List of valid process names
        suggestion: Suggested alternative, if any
    """

    def __init__(self, process: str, known_processes: Optional[List[str]] = None,
                 dsl: Optional[str] = None):
        self.process = process
        self.known_processes = known_processes or []
        self.suggestion = _suggest_similar(process, self.known_processes)

        message = f"Unknown process '{process}'."
        if self.suggestion:
            message += f" Did you mean '{self.suggestion}'?"
        if self.known_processes:
            message += f"\nKnown processes: {', '.join(sorted(self.known_processes))}"

        super().__init__(message, dsl)


class MissingInitialConditionError(DynamicsError):
    """Exception raised when a required initial condition is missing.

    Attributes:
        key: The missing initial condition key
        required_keys: List of required initial condition keys
    """

    def __init__(self, key: str, required_keys: Optional[List[str]] = None,
                 dsl: Optional[str] = None):
        self.key = key
        self.required_keys = required_keys or []

        message = f"Missing required initial condition '{key}'."
        if self.required_keys:
            message += f"\nRequired initial conditions: {', '.join(sorted(self.required_keys))}"

        super().__init__(message, dsl)


class UnknownMeasureError(DynamicsError):
    """Exception raised when an unknown measure is referenced.

    Attributes:
        measure: The unknown measure name
        known_measures: List of valid measure names
        suggestion: Suggested alternative, if any
    """

    def __init__(self, measure: str, known_measures: Optional[List[str]] = None,
                 process_name: Optional[str] = None, dsl: Optional[str] = None):
        self.measure = measure
        self.known_measures = known_measures or []
        self.process_name = process_name
        self.suggestion = _suggest_similar(measure, self.known_measures)

        message = f"Unknown measure '{measure}'"
        if process_name:
            message += f" for process '{process_name}'"
        message += "."
        if self.suggestion:
            message += f" Did you mean '{self.suggestion}'?"
        if self.known_measures:
            message += f"\nKnown measures: {', '.join(sorted(self.known_measures))}"

        super().__init__(message, dsl)


class SimulationConfigError(DynamicsError):
    """Exception raised for invalid simulation configuration.

    Attributes:
        config_key: The configuration key with the error
        reason: Explanation of the error
    """

    def __init__(self, config_key: str, reason: str, dsl: Optional[str] = None):
        self.config_key = config_key
        self.reason = reason

        message = f"Invalid simulation configuration '{config_key}': {reason}"

        super().__init__(message, dsl)
