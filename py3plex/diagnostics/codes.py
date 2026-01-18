"""Error code taxonomy for py3plex diagnostics.

This module defines a comprehensive, stable taxonomy of error codes
used throughout the library. Each error code is documented and searchable.

Error Code Format:
- <CATEGORY>_<SUBCATEGORY>_<NUMBER>
- Examples: DSL_PARSE_001, DSL_SEM_001, EXEC_001, RES_001

Categories:
- DSL_PARSE: Parsing and construction errors in DSL
- DSL_SEM: Semantic and logical errors in DSL
- EXEC: Execution and data errors
- RES: Result and interpretation warnings
- ALG: Algorithm-specific errors
- IO: Input/output errors
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ErrorCode:
    """Error code definition with documentation.
    
    Attributes:
        code: Stable error code (e.g., "DSL_SEM_001")
        category: High-level category
        title: Short title
        description: Detailed description
        typical_cause: Common causes
        typical_fix: Common fixes
    """
    
    code: str
    category: str
    title: str
    description: str
    typical_cause: str
    typical_fix: str


# DSL Parsing / Construction Errors
DSL_PARSE_001 = ErrorCode(
    code="DSL_PARSE_001",
    category="DSL Parsing",
    title="Unknown token or keyword",
    description="The DSL parser encountered an unrecognized token or keyword",
    typical_cause="Typo in query string, unsupported syntax, or malformed expression",
    typical_fix="Check query syntax against DSL documentation"
)

DSL_PARSE_002 = ErrorCode(
    code="DSL_PARSE_002",
    category="DSL Parsing",
    title="Invalid comparison operator",
    description="The comparison operator is not recognized or not valid in this context",
    typical_cause="Using invalid operator like '===', '!==', or malformed suffix like '__gte'",
    typical_fix="Use valid operators: __gt, __gte, __lt, __lte, __eq, __ne"
)

DSL_PARSE_003 = ErrorCode(
    code="DSL_PARSE_003",
    category="DSL Parsing",
    title="Malformed layer expression",
    description="The layer expression cannot be parsed",
    typical_cause="Invalid layer syntax, missing quotes, or malformed set operations",
    typical_fix="Use L['layer_name'] or L['*'] for all layers"
)

DSL_PARSE_004 = ErrorCode(
    code="DSL_PARSE_004",
    category="DSL Parsing",
    title="Invalid aggregation expression",
    description="The aggregation expression is malformed",
    typical_cause="Unknown aggregation function or invalid syntax",
    typical_fix="Use valid aggregations: mean, sum, count, min, max, std"
)

# DSL Semantic / Logical Errors
DSL_SEM_001 = ErrorCode(
    code="DSL_SEM_001",
    category="DSL Semantics",
    title="Unknown field",
    description="Referenced field does not exist on the target type",
    typical_cause="Typo in field name (e.g., 'degreee' instead of 'degree')",
    typical_fix="Check field name spelling or use .compute() to create the field"
)

DSL_SEM_002 = ErrorCode(
    code="DSL_SEM_002",
    category="DSL Semantics",
    title="Field not valid for target",
    description="Field is not applicable to the current target (node vs edge)",
    typical_cause="Trying to access edge-specific field on nodes or vice versa",
    typical_fix="Ensure query target matches field type (Q.nodes() for node fields)"
)

DSL_SEM_003 = ErrorCode(
    code="DSL_SEM_003",
    category="DSL Semantics",
    title="Measure incompatible with grouping",
    description="The measure cannot be computed or used with current grouping",
    typical_cause="Using node-level measure in edge-grouped query",
    typical_fix="Remove grouping or use compatible aggregation"
)

DSL_SEM_004 = ErrorCode(
    code="DSL_SEM_004",
    category="DSL Semantics",
    title="UQ requested on deterministic measure",
    description="Uncertainty quantification requested on a deterministic measure",
    typical_cause="Calling .uq() on measures that don't have uncertainty",
    typical_fix="Only use .uq() with stochastic measures or graph sampling"
)

DSL_SEM_005 = ErrorCode(
    code="DSL_SEM_005",
    category="DSL Semantics",
    title="Layer expression resolves to empty set",
    description="The layer selection doesn't match any layers in the network",
    typical_cause="Layer name typo, network has no layers, or layer filter too restrictive",
    typical_fix="Check layer names with net.list_layers() or use L['*']"
)

# Execution / Data Errors
EXEC_001 = ErrorCode(
    code="EXEC_001",
    category="Execution",
    title="Measure failed on graph backend",
    description="The measure computation failed during execution",
    typical_cause="Graph properties incompatible with measure (e.g., disconnected graph)",
    typical_fix="Check graph properties or use try_approximate=True"
)

EXEC_002 = ErrorCode(
    code="EXEC_002",
    category="Execution",
    title="Graph too large for algorithm",
    description="Graph size exceeds practical limits for this algorithm",
    typical_cause="Attempting exact computation on very large graph",
    typical_fix="Use approximate algorithms or sample the graph"
)

EXEC_003 = ErrorCode(
    code="EXEC_003",
    category="Execution",
    title="Graph assumption violated",
    description="Algorithm requires graph property that doesn't hold",
    typical_cause="Algorithm assumes connected graph but graph is disconnected",
    typical_fix="Use algorithm variant that handles disconnected graphs"
)

EXEC_004 = ErrorCode(
    code="EXEC_004",
    category="Execution",
    title="Randomness without seed",
    description="Stochastic algorithm used without seed (warning)",
    typical_cause="Forgot to specify seed parameter for reproducibility",
    typical_fix="Add seed=42 or similar to ensure reproducibility"
)

# Results / Interpretation Warnings
RES_001 = ErrorCode(
    code="RES_001",
    category="Results",
    title="Result empty after filters",
    description="Query produced no results after applying filters",
    typical_cause="Filter thresholds too restrictive",
    typical_fix="Relax filter conditions or check data distribution"
)

RES_002 = ErrorCode(
    code="RES_002",
    category="Results",
    title="High variance in UQ result",
    description="Uncertainty quantification shows high variance",
    typical_cause="Insufficient samples or unstable measure",
    typical_fix="Increase n_samples or use different resampling strategy"
)

RES_003 = ErrorCode(
    code="RES_003",
    category="Results",
    title="Aggregation hides variance",
    description="Aggregation may hide important node-level variance",
    typical_cause="Using mean/sum aggregation on heterogeneous data",
    typical_fix="Check per-node results before aggregating"
)

RES_004 = ErrorCode(
    code="RES_004",
    category="Results",
    title="Community result degenerate",
    description="Community detection produced degenerate result",
    typical_cause="Single community or trivial partition",
    typical_fix="Adjust resolution parameter or use different algorithm"
)

# Algorithm-specific Errors
ALG_001 = ErrorCode(
    code="ALG_001",
    category="Algorithm",
    title="Unknown algorithm",
    description="The specified algorithm name is not recognized",
    typical_cause="Typo in algorithm name or algorithm not available",
    typical_fix="Check algorithm name spelling or list available algorithms"
)

ALG_002 = ErrorCode(
    code="ALG_002",
    category="Algorithm",
    title="Algorithm parameter invalid",
    description="Algorithm parameter value is invalid",
    typical_cause="Parameter out of valid range or wrong type",
    typical_fix="Check algorithm documentation for valid parameter ranges"
)

ALG_003 = ErrorCode(
    code="ALG_003",
    category="Algorithm",
    title="Algorithm not converged",
    description="Iterative algorithm did not converge",
    typical_cause="Insufficient iterations or numerical instability",
    typical_fix="Increase max_iter or adjust convergence tolerance"
)

# I/O Errors
IO_001 = ErrorCode(
    code="IO_001",
    category="I/O",
    title="File not found",
    description="The specified file does not exist",
    typical_cause="Incorrect file path or file doesn't exist",
    typical_fix="Check file path and ensure file exists"
)

IO_002 = ErrorCode(
    code="IO_002",
    category="I/O",
    title="Invalid file format",
    description="File format is not recognized or supported",
    typical_cause="Wrong input_type parameter or corrupted file",
    typical_fix="Specify correct input_type or check file contents"
)

IO_003 = ErrorCode(
    code="IO_003",
    category="I/O",
    title="Missing required column",
    description="Input file is missing required column",
    typical_cause="CSV/DataFrame missing expected column",
    typical_fix="Check input format documentation and add missing columns"
)


# Registry of all error codes
ERROR_CODES: Dict[str, ErrorCode] = {
    # DSL Parsing
    "DSL_PARSE_001": DSL_PARSE_001,
    "DSL_PARSE_002": DSL_PARSE_002,
    "DSL_PARSE_003": DSL_PARSE_003,
    "DSL_PARSE_004": DSL_PARSE_004,
    # DSL Semantics
    "DSL_SEM_001": DSL_SEM_001,
    "DSL_SEM_002": DSL_SEM_002,
    "DSL_SEM_003": DSL_SEM_003,
    "DSL_SEM_004": DSL_SEM_004,
    "DSL_SEM_005": DSL_SEM_005,
    # Execution
    "EXEC_001": EXEC_001,
    "EXEC_002": EXEC_002,
    "EXEC_003": EXEC_003,
    "EXEC_004": EXEC_004,
    # Results
    "RES_001": RES_001,
    "RES_002": RES_002,
    "RES_003": RES_003,
    "RES_004": RES_004,
    # Algorithms
    "ALG_001": ALG_001,
    "ALG_002": ALG_002,
    "ALG_003": ALG_003,
    # I/O
    "IO_001": IO_001,
    "IO_002": IO_002,
    "IO_003": IO_003,
}


def get_error_code(code: str) -> ErrorCode:
    """Get error code definition.
    
    Args:
        code: Error code string
    
    Returns:
        ErrorCode definition
    
    Raises:
        KeyError: If code is not recognized
    """
    return ERROR_CODES[code]
