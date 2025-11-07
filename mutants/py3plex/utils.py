"""
Utility functions for py3plex.

This module provides common utilities used across the library,
including random state management for reproducibility and deprecation warnings.
"""

import functools
import inspect
import os
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
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


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


def x_warn_if_deprecated__mutmut_orig(feature_name: str, reason: str, alternative: str = None) -> None:
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


def x_warn_if_deprecated__mutmut_1(feature_name: str, reason: str, alternative: str = None) -> None:
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
    msg = None
    if alternative:
        msg += f" Use {alternative} instead."

    warnings.warn(msg, category=DeprecationWarning, stacklevel=2)


def x_warn_if_deprecated__mutmut_2(feature_name: str, reason: str, alternative: str = None) -> None:
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
        msg = f" Use {alternative} instead."

    warnings.warn(msg, category=DeprecationWarning, stacklevel=2)


def x_warn_if_deprecated__mutmut_3(feature_name: str, reason: str, alternative: str = None) -> None:
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
        msg -= f" Use {alternative} instead."

    warnings.warn(msg, category=DeprecationWarning, stacklevel=2)


def x_warn_if_deprecated__mutmut_4(feature_name: str, reason: str, alternative: str = None) -> None:
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

    warnings.warn(None, category=DeprecationWarning, stacklevel=2)


def x_warn_if_deprecated__mutmut_5(feature_name: str, reason: str, alternative: str = None) -> None:
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

    warnings.warn(msg, category=None, stacklevel=2)


def x_warn_if_deprecated__mutmut_6(feature_name: str, reason: str, alternative: str = None) -> None:
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

    warnings.warn(msg, category=DeprecationWarning, stacklevel=None)


def x_warn_if_deprecated__mutmut_7(feature_name: str, reason: str, alternative: str = None) -> None:
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

    warnings.warn(category=DeprecationWarning, stacklevel=2)


def x_warn_if_deprecated__mutmut_8(feature_name: str, reason: str, alternative: str = None) -> None:
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

    warnings.warn(msg, stacklevel=2)


def x_warn_if_deprecated__mutmut_9(feature_name: str, reason: str, alternative: str = None) -> None:
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

    warnings.warn(msg, category=DeprecationWarning, )


def x_warn_if_deprecated__mutmut_10(feature_name: str, reason: str, alternative: str = None) -> None:
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

    warnings.warn(msg, category=DeprecationWarning, stacklevel=3)

x_warn_if_deprecated__mutmut_mutants : ClassVar[MutantDict] = {
'x_warn_if_deprecated__mutmut_1': x_warn_if_deprecated__mutmut_1, 
    'x_warn_if_deprecated__mutmut_2': x_warn_if_deprecated__mutmut_2, 
    'x_warn_if_deprecated__mutmut_3': x_warn_if_deprecated__mutmut_3, 
    'x_warn_if_deprecated__mutmut_4': x_warn_if_deprecated__mutmut_4, 
    'x_warn_if_deprecated__mutmut_5': x_warn_if_deprecated__mutmut_5, 
    'x_warn_if_deprecated__mutmut_6': x_warn_if_deprecated__mutmut_6, 
    'x_warn_if_deprecated__mutmut_7': x_warn_if_deprecated__mutmut_7, 
    'x_warn_if_deprecated__mutmut_8': x_warn_if_deprecated__mutmut_8, 
    'x_warn_if_deprecated__mutmut_9': x_warn_if_deprecated__mutmut_9, 
    'x_warn_if_deprecated__mutmut_10': x_warn_if_deprecated__mutmut_10
}

def warn_if_deprecated(*args, **kwargs):
    result = _mutmut_trampoline(x_warn_if_deprecated__mutmut_orig, x_warn_if_deprecated__mutmut_mutants, args, kwargs)
    return result 

warn_if_deprecated.__signature__ = _mutmut_signature(x_warn_if_deprecated__mutmut_orig)
x_warn_if_deprecated__mutmut_orig.__name__ = 'x_warn_if_deprecated'


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
    from py3plex.exceptions import NetworkConstructionError

    if network_data is None:
        raise NetworkConstructionError("Network data cannot be None")

    # Additional validation logic can be added here
    # This is a placeholder for future validation enhancements


def x_get_data_path__mutmut_orig(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_1(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    search_paths = None
    
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_2(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    search_paths = []
    
    # 1. Try relative to the calling script's directory
    try:
        caller_path = None
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_3(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    search_paths = []
    
    # 1. Try relative to the calling script's directory
    try:
        caller_path = _find_caller_script_path()
        if caller_path:
            for candidate in _search_upward_from_script(None, relative_path):
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_4(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    search_paths = []
    
    # 1. Try relative to the calling script's directory
    try:
        caller_path = _find_caller_script_path()
        if caller_path:
            for candidate in _search_upward_from_script(caller_path, None):
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_5(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    search_paths = []
    
    # 1. Try relative to the calling script's directory
    try:
        caller_path = _find_caller_script_path()
        if caller_path:
            for candidate in _search_upward_from_script(relative_path):
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_6(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    search_paths = []
    
    # 1. Try relative to the calling script's directory
    try:
        caller_path = _find_caller_script_path()
        if caller_path:
            for candidate in _search_upward_from_script(caller_path, ):
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_7(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    search_paths = []
    
    # 1. Try relative to the calling script's directory
    try:
        caller_path = _find_caller_script_path()
        if caller_path:
            for candidate in _search_upward_from_script(caller_path, relative_path):
                if candidate.exists():
                    return str(None)
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_8(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    search_paths = []
    
    # 1. Try relative to the calling script's directory
    try:
        caller_path = _find_caller_script_path()
        if caller_path:
            for candidate in _search_upward_from_script(caller_path, relative_path):
                if candidate.exists():
                    return str(candidate)
                search_paths.append(None)
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_9(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    search_paths = []
    
    # 1. Try relative to the calling script's directory
    try:
        caller_path = _find_caller_script_path()
        if caller_path:
            for candidate in _search_upward_from_script(caller_path, relative_path):
                if candidate.exists():
                    return str(candidate)
                search_paths.append(str(None))
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_10(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
        cwd_path = None
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_11(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
        cwd_path = Path.cwd() * relative_path
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_12(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
            return str(None)
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_13(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
        search_paths.append(None)
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_14(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
        search_paths.append(str(None))
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_15(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
        utils_dir = None
        repo_root = utils_dir.parent
        package_path = repo_root / relative_path
        if package_path.exists():
            return str(package_path)
        search_paths.append(str(package_path))
    except (OSError, AttributeError):
        pass
    
    # If we reach here, file was not found in any location
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_16(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
        utils_dir = Path(None).parent
        repo_root = utils_dir.parent
        package_path = repo_root / relative_path
        if package_path.exists():
            return str(package_path)
        search_paths.append(str(package_path))
    except (OSError, AttributeError):
        pass
    
    # If we reach here, file was not found in any location
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_17(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
        repo_root = None
        package_path = repo_root / relative_path
        if package_path.exists():
            return str(package_path)
        search_paths.append(str(package_path))
    except (OSError, AttributeError):
        pass
    
    # If we reach here, file was not found in any location
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_18(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
        package_path = None
        if package_path.exists():
            return str(package_path)
        search_paths.append(str(package_path))
    except (OSError, AttributeError):
        pass
    
    # If we reach here, file was not found in any location
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_19(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
        package_path = repo_root * relative_path
        if package_path.exists():
            return str(package_path)
        search_paths.append(str(package_path))
    except (OSError, AttributeError):
        pass
    
    # If we reach here, file was not found in any location
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_20(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
            return str(None)
        search_paths.append(str(package_path))
    except (OSError, AttributeError):
        pass
    
    # If we reach here, file was not found in any location
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_21(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
        search_paths.append(None)
    except (OSError, AttributeError):
        pass
    
    # If we reach here, file was not found in any location
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_22(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
        search_paths.append(str(None))
    except (OSError, AttributeError):
        pass
    
    # If we reach here, file was not found in any location
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_23(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    raise FileNotFoundError(
        None
    )


def x_get_data_path__mutmut_24(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) - "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_25(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" - "\n".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_26(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(None) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_27(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "XX\nXX".join(f"  - {p}" for p in search_paths) + "\n\n"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )


def x_get_data_path__mutmut_28(relative_path: str) -> str:
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
        FileNotFoundError: If the file cannot be found in any search location
    
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
    raise FileNotFoundError(
        f"Could not find '{relative_path}' in any of the expected locations.\n"
        f"Searched paths:\n" + "\n".join(f"  - {p}" for p in search_paths) + "XX\n\nXX"
        f"The datasets directory is not included when py3plex is installed via pip.\n"
        f"To use examples and datasets:\n"
        f"  1. Clone the repository: git clone https://github.com/SkBlaz/py3plex.git\n"
        f"  2. Run examples from the repository root directory, OR\n"
        f"  3. Copy the datasets directory to your working directory"
    )

x_get_data_path__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_data_path__mutmut_1': x_get_data_path__mutmut_1, 
    'x_get_data_path__mutmut_2': x_get_data_path__mutmut_2, 
    'x_get_data_path__mutmut_3': x_get_data_path__mutmut_3, 
    'x_get_data_path__mutmut_4': x_get_data_path__mutmut_4, 
    'x_get_data_path__mutmut_5': x_get_data_path__mutmut_5, 
    'x_get_data_path__mutmut_6': x_get_data_path__mutmut_6, 
    'x_get_data_path__mutmut_7': x_get_data_path__mutmut_7, 
    'x_get_data_path__mutmut_8': x_get_data_path__mutmut_8, 
    'x_get_data_path__mutmut_9': x_get_data_path__mutmut_9, 
    'x_get_data_path__mutmut_10': x_get_data_path__mutmut_10, 
    'x_get_data_path__mutmut_11': x_get_data_path__mutmut_11, 
    'x_get_data_path__mutmut_12': x_get_data_path__mutmut_12, 
    'x_get_data_path__mutmut_13': x_get_data_path__mutmut_13, 
    'x_get_data_path__mutmut_14': x_get_data_path__mutmut_14, 
    'x_get_data_path__mutmut_15': x_get_data_path__mutmut_15, 
    'x_get_data_path__mutmut_16': x_get_data_path__mutmut_16, 
    'x_get_data_path__mutmut_17': x_get_data_path__mutmut_17, 
    'x_get_data_path__mutmut_18': x_get_data_path__mutmut_18, 
    'x_get_data_path__mutmut_19': x_get_data_path__mutmut_19, 
    'x_get_data_path__mutmut_20': x_get_data_path__mutmut_20, 
    'x_get_data_path__mutmut_21': x_get_data_path__mutmut_21, 
    'x_get_data_path__mutmut_22': x_get_data_path__mutmut_22, 
    'x_get_data_path__mutmut_23': x_get_data_path__mutmut_23, 
    'x_get_data_path__mutmut_24': x_get_data_path__mutmut_24, 
    'x_get_data_path__mutmut_25': x_get_data_path__mutmut_25, 
    'x_get_data_path__mutmut_26': x_get_data_path__mutmut_26, 
    'x_get_data_path__mutmut_27': x_get_data_path__mutmut_27, 
    'x_get_data_path__mutmut_28': x_get_data_path__mutmut_28
}

def get_data_path(*args, **kwargs):
    result = _mutmut_trampoline(x_get_data_path__mutmut_orig, x_get_data_path__mutmut_mutants, args, kwargs)
    return result 

get_data_path.__signature__ = _mutmut_signature(x_get_data_path__mutmut_orig)
x_get_data_path__mutmut_orig.__name__ = 'x_get_data_path'


def x__find_caller_script_path__mutmut_orig() -> Path:
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


def x__find_caller_script_path__mutmut_1() -> Path:
    """
    Find the path of the script that called get_data_path.
    
    Walks up the call stack to find the first frame outside the py3plex package.
    
    Returns:
        Path to the calling script, or None if not found
    """
    frame = None
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


def x__find_caller_script_path__mutmut_2() -> Path:
    """
    Find the path of the script that called get_data_path.
    
    Walks up the call stack to find the first frame outside the py3plex package.
    
    Returns:
        Path to the calling script, or None if not found
    """
    frame = inspect.currentframe()
    utils_file = None
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


def x__find_caller_script_path__mutmut_3() -> Path:
    """
    Find the path of the script that called get_data_path.
    
    Walks up the call stack to find the first frame outside the py3plex package.
    
    Returns:
        Path to the calling script, or None if not found
    """
    frame = inspect.currentframe()
    utils_file = Path(None).resolve()
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


def x__find_caller_script_path__mutmut_4() -> Path:
    """
    Find the path of the script that called get_data_path.
    
    Walks up the call stack to find the first frame outside the py3plex package.
    
    Returns:
        Path to the calling script, or None if not found
    """
    frame = inspect.currentframe()
    utils_file = Path(__file__).resolve()
    package_dir = None  # py3plex package directory
    
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


def x__find_caller_script_path__mutmut_5() -> Path:
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
        while frame is None:
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


def x__find_caller_script_path__mutmut_6() -> Path:
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
            frame_file = None
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


def x__find_caller_script_path__mutmut_7() -> Path:
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
            frame_file = inspect.getframeinfo(None).filename
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


def x__find_caller_script_path__mutmut_8() -> Path:
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
                frame_path = None
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


def x__find_caller_script_path__mutmut_9() -> Path:
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
                frame_path = Path(None).resolve()
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


def x__find_caller_script_path__mutmut_10() -> Path:
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
                    frame_path.relative_to(None)
                    # If relative_to succeeds, frame is inside package, skip it
                except ValueError:
                    # Frame is outside package, this is our caller
                    return frame_path.parent
            frame = frame.f_back
    finally:
        del frame  # Avoid reference cycles
    
    return None


def x__find_caller_script_path__mutmut_11() -> Path:
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
            frame = None
    finally:
        del frame  # Avoid reference cycles
    
    return None

x__find_caller_script_path__mutmut_mutants : ClassVar[MutantDict] = {
'x__find_caller_script_path__mutmut_1': x__find_caller_script_path__mutmut_1, 
    'x__find_caller_script_path__mutmut_2': x__find_caller_script_path__mutmut_2, 
    'x__find_caller_script_path__mutmut_3': x__find_caller_script_path__mutmut_3, 
    'x__find_caller_script_path__mutmut_4': x__find_caller_script_path__mutmut_4, 
    'x__find_caller_script_path__mutmut_5': x__find_caller_script_path__mutmut_5, 
    'x__find_caller_script_path__mutmut_6': x__find_caller_script_path__mutmut_6, 
    'x__find_caller_script_path__mutmut_7': x__find_caller_script_path__mutmut_7, 
    'x__find_caller_script_path__mutmut_8': x__find_caller_script_path__mutmut_8, 
    'x__find_caller_script_path__mutmut_9': x__find_caller_script_path__mutmut_9, 
    'x__find_caller_script_path__mutmut_10': x__find_caller_script_path__mutmut_10, 
    'x__find_caller_script_path__mutmut_11': x__find_caller_script_path__mutmut_11
}

def _find_caller_script_path(*args, **kwargs):
    result = _mutmut_trampoline(x__find_caller_script_path__mutmut_orig, x__find_caller_script_path__mutmut_mutants, args, kwargs)
    return result 

_find_caller_script_path.__signature__ = _mutmut_signature(x__find_caller_script_path__mutmut_orig)
x__find_caller_script_path__mutmut_orig.__name__ = 'x__find_caller_script_path'


def x__search_upward_from_script__mutmut_orig(script_dir: Path, relative_path: str) -> list:
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


def x__search_upward_from_script__mutmut_1(script_dir: Path, relative_path: str) -> list:
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
    candidates = None
    # Check current directory and up to 3 parent levels (4 total)
    for level in range(MAX_UPWARD_SEARCH_LEVELS):
        potential_root = script_dir
        for _ in range(level):
            potential_root = potential_root.parent
        candidates.append(potential_root / relative_path)
    return candidates


def x__search_upward_from_script__mutmut_2(script_dir: Path, relative_path: str) -> list:
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
    for level in range(None):
        potential_root = script_dir
        for _ in range(level):
            potential_root = potential_root.parent
        candidates.append(potential_root / relative_path)
    return candidates


def x__search_upward_from_script__mutmut_3(script_dir: Path, relative_path: str) -> list:
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
        potential_root = None
        for _ in range(level):
            potential_root = potential_root.parent
        candidates.append(potential_root / relative_path)
    return candidates


def x__search_upward_from_script__mutmut_4(script_dir: Path, relative_path: str) -> list:
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
        for _ in range(None):
            potential_root = potential_root.parent
        candidates.append(potential_root / relative_path)
    return candidates


def x__search_upward_from_script__mutmut_5(script_dir: Path, relative_path: str) -> list:
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
            potential_root = None
        candidates.append(potential_root / relative_path)
    return candidates


def x__search_upward_from_script__mutmut_6(script_dir: Path, relative_path: str) -> list:
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
        candidates.append(None)
    return candidates


def x__search_upward_from_script__mutmut_7(script_dir: Path, relative_path: str) -> list:
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
        candidates.append(potential_root * relative_path)
    return candidates

x__search_upward_from_script__mutmut_mutants : ClassVar[MutantDict] = {
'x__search_upward_from_script__mutmut_1': x__search_upward_from_script__mutmut_1, 
    'x__search_upward_from_script__mutmut_2': x__search_upward_from_script__mutmut_2, 
    'x__search_upward_from_script__mutmut_3': x__search_upward_from_script__mutmut_3, 
    'x__search_upward_from_script__mutmut_4': x__search_upward_from_script__mutmut_4, 
    'x__search_upward_from_script__mutmut_5': x__search_upward_from_script__mutmut_5, 
    'x__search_upward_from_script__mutmut_6': x__search_upward_from_script__mutmut_6, 
    'x__search_upward_from_script__mutmut_7': x__search_upward_from_script__mutmut_7
}

def _search_upward_from_script(*args, **kwargs):
    result = _mutmut_trampoline(x__search_upward_from_script__mutmut_orig, x__search_upward_from_script__mutmut_mutants, args, kwargs)
    return result 

_search_upward_from_script.__signature__ = _mutmut_signature(x__search_upward_from_script__mutmut_orig)
x__search_upward_from_script__mutmut_orig.__name__ = 'x__search_upward_from_script'


def x_get_dataset_path__mutmut_orig(filename: str) -> str:
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


def x_get_dataset_path__mutmut_1(filename: str) -> str:
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
    if filename.startswith(None):
        return get_data_path(filename)
    # Otherwise, prepend "datasets/"
    return get_data_path(f"datasets/{filename}")


def x_get_dataset_path__mutmut_2(filename: str) -> str:
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
    if filename.startswith("XXdatasets/XX"):
        return get_data_path(filename)
    # Otherwise, prepend "datasets/"
    return get_data_path(f"datasets/{filename}")


def x_get_dataset_path__mutmut_3(filename: str) -> str:
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
    if filename.startswith("DATASETS/"):
        return get_data_path(filename)
    # Otherwise, prepend "datasets/"
    return get_data_path(f"datasets/{filename}")


def x_get_dataset_path__mutmut_4(filename: str) -> str:
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
        return get_data_path(None)
    # Otherwise, prepend "datasets/"
    return get_data_path(f"datasets/{filename}")


def x_get_dataset_path__mutmut_5(filename: str) -> str:
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
    return get_data_path(None)

x_get_dataset_path__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_dataset_path__mutmut_1': x_get_dataset_path__mutmut_1, 
    'x_get_dataset_path__mutmut_2': x_get_dataset_path__mutmut_2, 
    'x_get_dataset_path__mutmut_3': x_get_dataset_path__mutmut_3, 
    'x_get_dataset_path__mutmut_4': x_get_dataset_path__mutmut_4, 
    'x_get_dataset_path__mutmut_5': x_get_dataset_path__mutmut_5
}

def get_dataset_path(*args, **kwargs):
    result = _mutmut_trampoline(x_get_dataset_path__mutmut_orig, x_get_dataset_path__mutmut_mutants, args, kwargs)
    return result 

get_dataset_path.__signature__ = _mutmut_signature(x_get_dataset_path__mutmut_orig)
x_get_dataset_path__mutmut_orig.__name__ = 'x_get_dataset_path'


def x_get_example_image_path__mutmut_orig(filename: str) -> str:
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


def x_get_example_image_path__mutmut_1(filename: str) -> str:
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
    if filename.startswith(None):
        return get_data_path(filename)
    # Otherwise, prepend "example_images/"
    return get_data_path(f"example_images/{filename}")


def x_get_example_image_path__mutmut_2(filename: str) -> str:
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
    if filename.startswith("XXexample_images/XX"):
        return get_data_path(filename)
    # Otherwise, prepend "example_images/"
    return get_data_path(f"example_images/{filename}")


def x_get_example_image_path__mutmut_3(filename: str) -> str:
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
    if filename.startswith("EXAMPLE_IMAGES/"):
        return get_data_path(filename)
    # Otherwise, prepend "example_images/"
    return get_data_path(f"example_images/{filename}")


def x_get_example_image_path__mutmut_4(filename: str) -> str:
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
        return get_data_path(None)
    # Otherwise, prepend "example_images/"
    return get_data_path(f"example_images/{filename}")


def x_get_example_image_path__mutmut_5(filename: str) -> str:
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
    return get_data_path(None)

x_get_example_image_path__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_example_image_path__mutmut_1': x_get_example_image_path__mutmut_1, 
    'x_get_example_image_path__mutmut_2': x_get_example_image_path__mutmut_2, 
    'x_get_example_image_path__mutmut_3': x_get_example_image_path__mutmut_3, 
    'x_get_example_image_path__mutmut_4': x_get_example_image_path__mutmut_4, 
    'x_get_example_image_path__mutmut_5': x_get_example_image_path__mutmut_5
}

def get_example_image_path(*args, **kwargs):
    result = _mutmut_trampoline(x_get_example_image_path__mutmut_orig, x_get_example_image_path__mutmut_mutants, args, kwargs)
    return result 

get_example_image_path.__signature__ = _mutmut_signature(x_get_example_image_path__mutmut_orig)
x_get_example_image_path__mutmut_orig.__name__ = 'x_get_example_image_path'


def x_get_multilayer_dataset_path__mutmut_orig(relative_path: str) -> str:
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


def x_get_multilayer_dataset_path__mutmut_1(relative_path: str) -> str:
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
    if relative_path.startswith(None):
        return get_data_path(relative_path)
    # Otherwise, prepend "multilayer_datasets/"
    return get_data_path(f"multilayer_datasets/{relative_path}")


def x_get_multilayer_dataset_path__mutmut_2(relative_path: str) -> str:
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
    if relative_path.startswith("XXmultilayer_datasets/XX"):
        return get_data_path(relative_path)
    # Otherwise, prepend "multilayer_datasets/"
    return get_data_path(f"multilayer_datasets/{relative_path}")


def x_get_multilayer_dataset_path__mutmut_3(relative_path: str) -> str:
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
    if relative_path.startswith("MULTILAYER_DATASETS/"):
        return get_data_path(relative_path)
    # Otherwise, prepend "multilayer_datasets/"
    return get_data_path(f"multilayer_datasets/{relative_path}")


def x_get_multilayer_dataset_path__mutmut_4(relative_path: str) -> str:
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
        return get_data_path(None)
    # Otherwise, prepend "multilayer_datasets/"
    return get_data_path(f"multilayer_datasets/{relative_path}")


def x_get_multilayer_dataset_path__mutmut_5(relative_path: str) -> str:
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
    return get_data_path(None)

x_get_multilayer_dataset_path__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_multilayer_dataset_path__mutmut_1': x_get_multilayer_dataset_path__mutmut_1, 
    'x_get_multilayer_dataset_path__mutmut_2': x_get_multilayer_dataset_path__mutmut_2, 
    'x_get_multilayer_dataset_path__mutmut_3': x_get_multilayer_dataset_path__mutmut_3, 
    'x_get_multilayer_dataset_path__mutmut_4': x_get_multilayer_dataset_path__mutmut_4, 
    'x_get_multilayer_dataset_path__mutmut_5': x_get_multilayer_dataset_path__mutmut_5
}

def get_multilayer_dataset_path(*args, **kwargs):
    result = _mutmut_trampoline(x_get_multilayer_dataset_path__mutmut_orig, x_get_multilayer_dataset_path__mutmut_mutants, args, kwargs)
    return result 

get_multilayer_dataset_path.__signature__ = _mutmut_signature(x_get_multilayer_dataset_path__mutmut_orig)
x_get_multilayer_dataset_path__mutmut_orig.__name__ = 'x_get_multilayer_dataset_path'


def x_get_background_knowledge_path__mutmut_orig(filename: str) -> str:
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


def x_get_background_knowledge_path__mutmut_1(filename: str) -> str:
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
    if filename.startswith(None):
        return get_data_path(filename)
    # If empty string or '.', return the directory itself
    if not filename or filename == '.':
        return get_data_path("background_knowledge")
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def x_get_background_knowledge_path__mutmut_2(filename: str) -> str:
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
    if filename.startswith("XXbackground_knowledge/XX"):
        return get_data_path(filename)
    # If empty string or '.', return the directory itself
    if not filename or filename == '.':
        return get_data_path("background_knowledge")
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def x_get_background_knowledge_path__mutmut_3(filename: str) -> str:
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
    if filename.startswith("BACKGROUND_KNOWLEDGE/"):
        return get_data_path(filename)
    # If empty string or '.', return the directory itself
    if not filename or filename == '.':
        return get_data_path("background_knowledge")
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def x_get_background_knowledge_path__mutmut_4(filename: str) -> str:
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
        return get_data_path(None)
    # If empty string or '.', return the directory itself
    if not filename or filename == '.':
        return get_data_path("background_knowledge")
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def x_get_background_knowledge_path__mutmut_5(filename: str) -> str:
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
    if not filename and filename == '.':
        return get_data_path("background_knowledge")
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def x_get_background_knowledge_path__mutmut_6(filename: str) -> str:
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
    if filename or filename == '.':
        return get_data_path("background_knowledge")
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def x_get_background_knowledge_path__mutmut_7(filename: str) -> str:
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
    if not filename or filename != '.':
        return get_data_path("background_knowledge")
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def x_get_background_knowledge_path__mutmut_8(filename: str) -> str:
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
    if not filename or filename == 'XX.XX':
        return get_data_path("background_knowledge")
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def x_get_background_knowledge_path__mutmut_9(filename: str) -> str:
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
        return get_data_path(None)
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def x_get_background_knowledge_path__mutmut_10(filename: str) -> str:
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
        return get_data_path("XXbackground_knowledgeXX")
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def x_get_background_knowledge_path__mutmut_11(filename: str) -> str:
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
        return get_data_path("BACKGROUND_KNOWLEDGE")
    # Otherwise, prepend "background_knowledge/"
    return get_data_path(f"background_knowledge/{filename}")


def x_get_background_knowledge_path__mutmut_12(filename: str) -> str:
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
    return get_data_path(None)

x_get_background_knowledge_path__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_background_knowledge_path__mutmut_1': x_get_background_knowledge_path__mutmut_1, 
    'x_get_background_knowledge_path__mutmut_2': x_get_background_knowledge_path__mutmut_2, 
    'x_get_background_knowledge_path__mutmut_3': x_get_background_knowledge_path__mutmut_3, 
    'x_get_background_knowledge_path__mutmut_4': x_get_background_knowledge_path__mutmut_4, 
    'x_get_background_knowledge_path__mutmut_5': x_get_background_knowledge_path__mutmut_5, 
    'x_get_background_knowledge_path__mutmut_6': x_get_background_knowledge_path__mutmut_6, 
    'x_get_background_knowledge_path__mutmut_7': x_get_background_knowledge_path__mutmut_7, 
    'x_get_background_knowledge_path__mutmut_8': x_get_background_knowledge_path__mutmut_8, 
    'x_get_background_knowledge_path__mutmut_9': x_get_background_knowledge_path__mutmut_9, 
    'x_get_background_knowledge_path__mutmut_10': x_get_background_knowledge_path__mutmut_10, 
    'x_get_background_knowledge_path__mutmut_11': x_get_background_knowledge_path__mutmut_11, 
    'x_get_background_knowledge_path__mutmut_12': x_get_background_knowledge_path__mutmut_12
}

def get_background_knowledge_path(*args, **kwargs):
    result = _mutmut_trampoline(x_get_background_knowledge_path__mutmut_orig, x_get_background_knowledge_path__mutmut_mutants, args, kwargs)
    return result 

get_background_knowledge_path.__signature__ = _mutmut_signature(x_get_background_knowledge_path__mutmut_orig)
x_get_background_knowledge_path__mutmut_orig.__name__ = 'x_get_background_knowledge_path'


def x_get_background_knowledge_dir__mutmut_orig() -> str:
    """
    Get the absolute path to the background knowledge directory.
    
    Returns:
        str: Absolute path to the background_knowledge directory
    
    Examples:
        >>> from py3plex.utils import get_background_knowledge_dir
        >>> dir_path = get_background_knowledge_dir()
    """
    return get_data_path("background_knowledge")


def x_get_background_knowledge_dir__mutmut_1() -> str:
    """
    Get the absolute path to the background knowledge directory.
    
    Returns:
        str: Absolute path to the background_knowledge directory
    
    Examples:
        >>> from py3plex.utils import get_background_knowledge_dir
        >>> dir_path = get_background_knowledge_dir()
    """
    return get_data_path(None)


def x_get_background_knowledge_dir__mutmut_2() -> str:
    """
    Get the absolute path to the background knowledge directory.
    
    Returns:
        str: Absolute path to the background_knowledge directory
    
    Examples:
        >>> from py3plex.utils import get_background_knowledge_dir
        >>> dir_path = get_background_knowledge_dir()
    """
    return get_data_path("XXbackground_knowledgeXX")


def x_get_background_knowledge_dir__mutmut_3() -> str:
    """
    Get the absolute path to the background knowledge directory.
    
    Returns:
        str: Absolute path to the background_knowledge directory
    
    Examples:
        >>> from py3plex.utils import get_background_knowledge_dir
        >>> dir_path = get_background_knowledge_dir()
    """
    return get_data_path("BACKGROUND_KNOWLEDGE")

x_get_background_knowledge_dir__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_background_knowledge_dir__mutmut_1': x_get_background_knowledge_dir__mutmut_1, 
    'x_get_background_knowledge_dir__mutmut_2': x_get_background_knowledge_dir__mutmut_2, 
    'x_get_background_knowledge_dir__mutmut_3': x_get_background_knowledge_dir__mutmut_3
}

def get_background_knowledge_dir(*args, **kwargs):
    result = _mutmut_trampoline(x_get_background_knowledge_dir__mutmut_orig, x_get_background_knowledge_dir__mutmut_mutants, args, kwargs)
    return result 

get_background_knowledge_dir.__signature__ = _mutmut_signature(x_get_background_knowledge_dir__mutmut_orig)
x_get_background_knowledge_dir__mutmut_orig.__name__ = 'x_get_background_knowledge_dir'
