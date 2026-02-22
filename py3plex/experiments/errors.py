"""Typed exceptions for the experiments subsystem."""


class ExperimentError(Exception):
    """Base class for all experiment-related errors."""


class ExperimentNotFound(ExperimentError):
    """Raised when an experiment ID is not in the store."""

    def __init__(self, exp_id: str):
        super().__init__(f"Experiment not found: {exp_id!r}")
        self.exp_id = exp_id


class ArtifactError(ExperimentError):
    """Raised when an artifact cannot be read or written."""


class SchemaMismatch(ExperimentError):
    """Raised when a stored artifact schema does not match the expected one."""


class ReproductionError(ExperimentError):
    """Raised when an experiment cannot be reproduced (e.g. missing network)."""
