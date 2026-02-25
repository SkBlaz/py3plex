"""Errors for out-of-core query execution."""


class OutOfCoreError(Exception):
    """Base exception for out-of-core execution errors."""


class UnsupportedOutOfCoreOperation(OutOfCoreError):
    """Raised when a requested operation is not supported in out-of-core mode.

    Example::

        raise UnsupportedOutOfCoreOperation(
            "betweenness_centrality",
            suggestion="Convert the network to in-memory first.",
        )
    """

    SUPPORTED_OPERATIONS = [
        "edge selection (from_layers, where on scalar attrs)",
        "node selection with degree threshold (degree__gt/lt/gte/lte)",
        "per_layer() aggregations for edge/node counts",
        "coverage(mode='at_least', k=N) for edges",
        "order_by on simple scalar fields",
        "limit",
    ]

    def __init__(self, operation: str, suggestion: str = "") -> None:
        self.operation = operation
        self.suggestion = suggestion
        supported = "\n  - ".join([""] + self.SUPPORTED_OPERATIONS)
        msg = (
            f"Operation '{operation}' is not supported in out-of-core mode."
            f"\nSupported operations:{supported}"
        )
        if suggestion:
            msg += f"\nSuggestion: {suggestion}"
        else:
            msg += (
                "\nSuggestion: Load the network into memory with "
                "multi_layer_network() for exact centrality computations."
            )
        super().__init__(msg)


class OutOfCoreIOError(OutOfCoreError):
    """Raised on I/O errors when reading/writing out-of-core data."""


class SchemaError(OutOfCoreError):
    """Raised when the on-disk schema does not match the expected schema."""
