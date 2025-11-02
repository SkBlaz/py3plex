"""
Utility functions for py3plex.

This module provides common utilities used across the library,
including random state management for reproducibility and deprecation warnings.
"""

import functools
import os
import warnings
from pathlib import Path
from typing import Any, Callable, Optional, Union

import numpy as np

# Optional formal verification support
try:
    from icontract import ensure, require

    ICONTRACT_AVAILABLE = True
except ImportError:
    # Create no-op decorators when icontract is not available
    def require(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def ensure(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    ICONTRACT_AVAILABLE = False


@ensure(
    lambda result: isinstance(result, np.random.Generator),
    "result must be a numpy random Generator",
)
def get_rng(
    seed: Optional[Union[int, np.random.Generator]] = None,
) -> np.random.Generator:
    """
    Get a NumPy random number generator with optional seed.

    This provides a unified interface for random state management across
    the library, ensuring reproducibility when a seed is provided.

    Args:
        seed: Random seed for reproducibility. Can be:
            - None: Use default unseeded generator
            - int: Seed value for the generator
            - np.random.Generator: Pass through existing generator

    Returns:
        np.random.Generator: Initialized random number generator

    Examples:
        >>> rng = get_rng(42)
        >>> rng.random()  # Reproducible random number
        0.7739560485559633

        >>> rng1 = get_rng(42)
        >>> rng2 = get_rng(42)
        >>> rng1.random() == rng2.random()
        True

        >>> existing_rng = np.random.default_rng(123)
        >>> rng = get_rng(existing_rng)
        >>> rng is existing_rng
        True

    Contracts:
        - Postcondition: result is a NumPy random Generator

    Note:
        Uses numpy.random.Generator (modern API introduced in NumPy 1.17)
        rather than the legacy numpy.random.RandomState API.
    """
    if isinstance(seed, np.random.Generator):
        return seed
    return np.random.default_rng(seed)


def deprecated(
    reason: str, version: str = None, alternative: str = None
) -> Callable[[Callable], Callable]:
    """
    Decorator to mark functions/methods as deprecated.

    This decorator will issue a DeprecationWarning when the decorated
    function is called, providing information about why it's deprecated
    and what to use instead.

    Args:
        reason: Explanation of why the function is deprecated
        version: Version in which the function was deprecated (optional)
        alternative: Suggested alternative function/method (optional)

    Returns:
        Decorator function

    Example:
        >>> @deprecated(
        ...     reason="This function is obsolete",
        ...     version="0.95a",
        ...     alternative="new_function()"
        ... )
        ... def old_function():
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            msg = f"{func.__name__} is deprecated"
            if version:
                msg += f" (since version {version})"
            msg += f": {reason}"
            if alternative:
                msg += f" Use {alternative} instead."

            warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def warn_if_deprecated(feature_name: str, reason: str, alternative: str = None) -> None:
    """
    Issue a deprecation warning for a feature.

    This is useful for deprecating specific usage patterns or parameter
    combinations rather than entire functions.

    Args:
        feature_name: Name of the deprecated feature
        reason: Explanation of why it's deprecated
        alternative: Suggested alternative (optional)

    Example:
        >>> def my_function(old_param=None, new_param=None):
        ...     if old_param is not None:
        ...         warn_if_deprecated(
        ...             "old_param",
        ...             "This parameter is no longer used",
        ...             "new_param"
        ...         )
    """
    msg = f"{feature_name} is deprecated: {reason}"
    if alternative:
        msg += f" Use {alternative} instead."

    warnings.warn(msg, category=DeprecationWarning, stacklevel=2)


@require(lambda network_data: network_data is not None, "network_data must not be None")
def validate_multilayer_input(network_data: Any) -> None:
    """
    Validate multilayer network input data.

    Performs sanity checks on multilayer network structures to catch
    common errors early.

    Args:
        network_data: Network data to validate (can be various formats)

    Raises:
        ValueError: If the network data is invalid

    Contracts:
        - Precondition: network_data must not be None

    Example:
        >>> from py3plex.utils import validate_multilayer_input
        >>> validate_multilayer_input(my_network)
    """
    # Import here to avoid circular dependencies
    from py3plex.exceptions import NetworkConstructionError

    if network_data is None:
        raise NetworkConstructionError("Network data cannot be None")

    # Additional validation logic can be added here
    # This is a placeholder for future validation enhancements


def get_data_path(relative_path: str) -> str:
    """
    Get the absolute path to a data file in the repository.
    
    This function resolves paths relative to the repository root,
    allowing example scripts to work regardless of the current working directory.
    
    Args:
        relative_path: Path relative to repository root (e.g., "datasets/intact02.gpickle")
    
    Returns:
        str: Absolute path to the file
    
    Examples:
        >>> from py3plex.utils import get_data_path
        >>> path = get_data_path("datasets/intact02.gpickle")
        >>> os.path.exists(path)
        True
    
    Note:
        This function assumes the py3plex package is installed or the script
        is run from within the repository structure.
    """
    # Get the directory containing this file (py3plex/utils.py)
    utils_dir = Path(__file__).parent
    # Go up one level to get the repository root (parent of py3plex package)
    repo_root = utils_dir.parent
    # Resolve the full path
    full_path = repo_root / relative_path
    return str(full_path)


def get_dataset_path(filename: str) -> str:
    """
    Get the absolute path to a dataset file.
    
    Convenience wrapper around get_data_path() specifically for dataset files.
    
    Args:
        filename: Name or relative path of the dataset file
    
    Returns:
        str: Absolute path to the dataset file
    
    Examples:
        >>> from py3plex.utils import get_dataset_path
        >>> path = get_dataset_path("intact02.gpickle")
        >>> os.path.exists(path)
        True
    """
    # If the filename already includes "datasets/", use it as-is
    if filename.startswith("datasets/"):
        return get_data_path(filename)
    # Otherwise, prepend "datasets/"
    return get_data_path(f"datasets/{filename}")


def get_example_image_path(filename: str) -> str:
    """
    Get the absolute path to an example image file.
    
    Convenience wrapper around get_data_path() specifically for example image files.
    
    Args:
        filename: Name or relative path of the image file
    
    Returns:
        str: Absolute path to the example image file
    
    Examples:
        >>> from py3plex.utils import get_example_image_path
        >>> path = get_example_image_path("intact_10_BH.png")
    """
    # If the filename already includes "example_images/", use it as-is
    if filename.startswith("example_images/"):
        return get_data_path(filename)
    # Otherwise, prepend "example_images/"
    return get_data_path(f"example_images/{filename}")
