"""
Utility functions for py3plex.

This module provides common utilities used across the library,
including random state management for reproducibility and deprecation warnings.
"""

import functools
import inspect
import warnings
from pathlib import Path
from typing import Any, Callable, Optional, Union

import numpy as np

# Configuration for dataset path search
MAX_UPWARD_SEARCH_LEVELS = 4  # Check current dir + 3 parent levels

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

        Negative seeds are converted to positive values by taking absolute value
        to ensure compatibility with NumPy's SeedSequence.
    """
    if isinstance(seed, np.random.Generator):
        return seed
    # Convert negative seeds to positive (NumPy SeedSequence requires non-negative)
    if seed is not None and seed < 0:
        seed = abs(seed)
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
    from py3plex.exceptions import NetworkConstructionError, Py3plexIOError

    if network_data is None:
        raise NetworkConstructionError("Network data cannot be None")

    # Additional validation logic can be added here
    # This is a placeholder for future validation enhancements


def get_data_path(relative_path: str) -> str:
    """
    Get the absolute path to a data file in the repository.

    This function searches for data files in multiple locations to support both:
    - Running examples from a cloned repository
    - Running scripts/notebooks from any directory with datasets locally available

    Search order:
    1. Relative to the calling script's directory (for examples in cloned repo)
    2. Relative to current working directory (for notebooks/user scripts)
    3. Relative to py3plex package location (for editable installs)

    Args:
        relative_path: Path relative to repository root (e.g., "datasets/intact02.gpickle")

    Returns:
        str: Absolute path to the file

    Raises:
        Py3plexIOError: If the file cannot be found in any search location

    Examples:
        >>> from py3plex.utils import get_data_path
        >>> path = get_data_path("datasets/intact02.gpickle")
        >>> os.path.exists(path)
        True

    Note:
        When py3plex is installed via pip, datasets are not included in the package.
        Users should either:
        - Clone the repository and run examples from there
        - Download datasets separately and place them relative to their scripts
        - Use current working directory with datasets folder
    """
    from py3plex.exceptions import Py3plexIOError

    search_paths = []

    # 1. Try relative to the calling script's directory
    try:
        caller_path = _find_caller_script_path()
        if caller_path:
            for candidate in _search_upward_from_script(caller_path, relative_path):
                if candidate.exists():
                    return str(candidate)
                search_paths.append(str(candidate))
    except (OSError, AttributeError):
        pass  # Continue to other search methods

    # 2. Try relative to current working directory
    try:
        cwd_path = Path.cwd() / relative_path
        if cwd_path.exists():
            return str(cwd_path)
        search_paths.append(str(cwd_path))
    except (OSError, AttributeError):
        pass

    # 3. Try relative to py3plex package location (for editable installs)
    try:
        utils_dir = Path(__file__).parent
        repo_root = utils_dir.parent
        package_path = repo_root / relative_path
        if package_path.exists():
            return str(package_path)
        search_paths.append(str(package_path))
    except (OSError, AttributeError):
        pass

    # If we reach here, file was not found in any location
    raise Py3plexIOError(
        f"Could not find dataset file '{relative_path}' in any expected location.\n\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To resolve this issue:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory, OR\n"
        f"  4. Provide the absolute path to your data file"
    )


def _find_caller_script_path() -> Path:
    """
    Find the path of the script that called get_data_path.

    Walks up the call stack to find the first frame outside the py3plex package.

    Returns:
        Path to the calling script, or None if not found
    """
    frame = inspect.currentframe()
    utils_file = Path(__file__).resolve()
    package_dir = utils_file.parent  # py3plex package directory

    try:
        while frame is not None:
            frame_file = inspect.getframeinfo(frame).filename
            if frame_file:
                frame_path = Path(frame_file).resolve()
                # Check if frame is outside the py3plex package directory
                try:
                    frame_path.relative_to(package_dir)
                    # If relative_to succeeds, frame is inside package, skip it
                except ValueError:
                    # Frame is outside package, this is our caller
                    return frame_path.parent
            frame = frame.f_back
    finally:
        del frame  # Avoid reference cycles

    return None


def _search_upward_from_script(script_dir: Path, relative_path: str) -> list:
    """
    Generate candidate paths by searching upward from script directory.

    Searches the script's directory and up to MAX_UPWARD_SEARCH_LEVELS-1 parent
    directories for the requested file path.

    Args:
        script_dir: Directory containing the calling script
        relative_path: Relative path to search for

    Returns:
        List of candidate paths to check
    """
    candidates = []
    # Check current directory and up to 3 parent levels (4 total)
    for level in range(MAX_UPWARD_SEARCH_LEVELS):
        potential_root = script_dir
        for _ in range(level):
            potential_root = potential_root.parent
        candidates.append(potential_root / relative_path)
    return candidates


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


def get_multilayer_dataset_path(relative_path: str) -> str:
    """
    Get the absolute path to a multilayer dataset file.

    Convenience wrapper around get_data_path() specifically for multilayer dataset files.

    Args:
        relative_path: Relative path within multilayer_datasets directory

    Returns:
        str: Absolute path to the multilayer dataset file

    Examples:
        >>> from py3plex.utils import get_multilayer_dataset_path
        >>> path = get_multilayer_dataset_path("MLKing/MLKing2013_multiplex.edges")
    """
    # If the path already includes "multilayer_datasets/", use it as-is
    if relative_path.startswith("multilayer_datasets/"):
        return get_data_path(relative_path)
    # Otherwise, prepend "multilayer_datasets/"
    return get_data_path(f"multilayer_datasets/{relative_path}")


def get_background_knowledge_path(filename: str) -> str:
    """
    Get the absolute path to a background knowledge file or directory.

    Convenience wrapper around get_data_path() specifically for background knowledge files.

    Args:
        filename: Name or relative path of the background knowledge file.
                 Use empty string or '.' to get the background_knowledge directory itself.

    Returns:
        str: Absolute path to the background knowledge file or directory

    Examples:
        >>> from py3plex.utils import get_background_knowledge_path
        >>> path = get_background_knowledge_path("bk.n3")
        >>> dir_path = get_background_knowledge_path(".")
    """
    # If the filename already includes "background_knowledge/", use it as-is
    if filename.startswith("background_knowledge/"):
        return get_data_path(filename)
    # If empty string or '.', return the directory itself
    if not filename or filename == '.':
        return get_data_path("background_knowledge")
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def get_background_knowledge_dir() -> str:
    """
    Get the absolute path to the background knowledge directory.

    Returns:
        str: Absolute path to the background_knowledge directory

    Examples:
        >>> from py3plex.utils import get_background_knowledge_dir
        >>> dir_path = get_background_knowledge_dir()
    """
    return get_data_path("background_knowledge")
