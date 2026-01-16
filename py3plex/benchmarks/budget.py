"""Budget management for fair benchmarking.

This module implements the Budget abstraction used to enforce fair resource
allocation across algorithms during benchmarking.
"""

import time
from dataclasses import dataclass, field
from typing import Optional


class BudgetExhaustedException(Exception):
    """Exception raised when a budget is exhausted."""

    pass


@dataclass
class Budget:
    """Budget tracker for fair algorithm comparisons.

    Tracks runtime (milliseconds) and evaluation count to ensure fair
    comparisons across algorithms. Both limits are optional but at least
    one should be provided.

    Attributes:
        limit_ms: Maximum runtime in milliseconds (optional)
        limit_evals: Maximum number of evaluations (optional)
        start_time: Start timestamp (set automatically)
        used_ms: Elapsed runtime in milliseconds
        eval_count: Number of evaluations performed

    Example:
        >>> budget = Budget(limit_ms=5000, limit_evals=100)
        >>> budget.charge(ms=250, evals=1)
        >>> budget.used_ms
        250.0
        >>> budget.exhausted()
        False
    """

    limit_ms: Optional[float] = None
    limit_evals: Optional[int] = None
    start_time: float = field(default_factory=time.time)
    used_ms: float = 0.0
    eval_count: int = 0

    def __post_init__(self):
        """Validate budget configuration."""
        if self.limit_ms is None and self.limit_evals is None:
            raise ValueError("Budget must specify at least one limit (limit_ms or limit_evals)")

    def charge(self, ms: float = 0.0, evals: int = 0) -> None:
        """Charge the budget with consumed resources.

        Args:
            ms: Milliseconds to charge
            evals: Number of evaluations to charge
        """
        self.used_ms += ms
        self.eval_count += evals

    def exhausted(self) -> bool:
        """Check if the budget is exhausted.

        Returns:
            True if any limit is exceeded, False otherwise
        """
        if self.limit_ms is not None and self.used_ms >= self.limit_ms:
            return True
        if self.limit_evals is not None and self.eval_count >= self.limit_evals:
            return True
        return False

    def remaining_ms(self) -> Optional[float]:
        """Get remaining time budget in milliseconds.

        Returns:
            Remaining milliseconds, or None if no time limit
        """
        if self.limit_ms is None:
            return None
        return max(0.0, self.limit_ms - self.used_ms)

    def remaining_evals(self) -> Optional[int]:
        """Get remaining evaluation budget.

        Returns:
            Remaining evaluations, or None if no eval limit
        """
        if self.limit_evals is None:
            return None
        return max(0, self.limit_evals - self.eval_count)

    def to_dict(self) -> dict:
        """Convert budget to dictionary for serialization.

        Returns:
            Dictionary with budget information
        """
        return {
            "limit_ms": self.limit_ms,
            "limit_evals": self.limit_evals,
            "used_ms": self.used_ms,
            "eval_count": self.eval_count,
            "exhausted": self.exhausted(),
        }

    def reset(self) -> None:
        """Reset the budget counters (keeps limits)."""
        self.start_time = time.time()
        self.used_ms = 0.0
        self.eval_count = 0
