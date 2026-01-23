"""Query provenance tracking for DSL v2.

This module provides structures and functions for tracking query execution
provenance, including:
- Query AST fingerprints
- Network fingerprints
- Performance timings
- Backend/engine information
- Randomness configuration

All provenance data is stored in QueryResult.meta["provenance"] with a stable schema.
"""

import hashlib
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Union

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from .ast import Query, SelectStmt


@dataclass
class ProvenanceRecord:
    """Provenance record for a query execution.
    
    This structure captures all metadata about how a query was executed,
    enabling reproducibility and debugging.
    
    Attributes:
        engine: Engine used ("dsl_v2_executor", "dsl_legacy", "graph_ops", etc.)
        py3plex_version: Version of py3plex used
        timestamp_utc: ISO8601 timestamp of query execution start
        network_fingerprint: Lightweight network summary (counts, layers)
        network_version: Mutation counter if available
        query: Query details (target, AST hash, summary, params)
        randomness: Seed configuration if randomness is used
        backend: Backend information (graph backend, algo backends, fast paths)
        performance: Timing information per stage
        warnings: List of warnings/notes from execution
    """
    engine: str
    py3plex_version: str
    timestamp_utc: str
    network_fingerprint: Dict[str, Any]
    network_version: Optional[int] = None
    query: Dict[str, Any] = field(default_factory=dict)
    randomness: Dict[str, Any] = field(default_factory=dict)
    backend: Dict[str, Any] = field(default_factory=dict)
    performance: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage in QueryResult.meta."""
        return asdict(self)


def get_py3plex_version() -> str:
    """Get py3plex version string.
    
    Returns:
        Version string (e.g., "1.1.0")
    """
    try:
        from py3plex import __version__
        return __version__
    except ImportError:
        # Fallback: read from pyproject.toml
        try:
            import os
            import re
            root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            pyproject_path = os.path.join(root, "pyproject.toml")
            if os.path.exists(pyproject_path):
                with open(pyproject_path, "r") as f:
                    for line in f:
                        if line.startswith("version"):
                            match = re.search(r'version\s*=\s*"([^"]+)"', line)
                            if match:
                                return match.group(1)
        except Exception:
            pass
    return "unknown"


def network_fingerprint(network: Any) -> Dict[str, Any]:
    """Create a lightweight fingerprint of a network.
    
    Args:
        network: Multilayer network object
        
    Returns:
        Dictionary with node_count, edge_count, layer_count, layers (list)
    """
    fingerprint = {
        "node_count": 0,
        "edge_count": 0,
        "layer_count": 0,
        "layers": [],
    }
    
    try:
        # Get node count
        if hasattr(network, "get_nodes"):
            fingerprint["node_count"] = len(list(network.get_nodes()))
        elif hasattr(network, "core_network"):
            fingerprint["node_count"] = network.core_network.number_of_nodes()
        
        # Get edge count
        if hasattr(network, "get_edges"):
            fingerprint["edge_count"] = len(list(network.get_edges()))
        elif hasattr(network, "core_network"):
            fingerprint["edge_count"] = network.core_network.number_of_edges()
        
        # Get layers
        if hasattr(network, "layers"):
            layers = [str(layer) for layer in network.layers]
            fingerprint["layers"] = sorted(layers)
            fingerprint["layer_count"] = len(layers)
        elif hasattr(network, "get_nodes"):
            # Derive layers from nodes
            layers_set = set()
            for node in network.get_nodes():
                if isinstance(node, tuple) and len(node) >= 2:
                    layers_set.add(str(node[1]))
            fingerprint["layers"] = sorted(layers_set)
            fingerprint["layer_count"] = len(layers_set)
    except Exception:
        # If fingerprinting fails, return partial fingerprint
        pass
    
    return fingerprint


def ast_fingerprint(ast: Union['Query', 'SelectStmt', Any]) -> str:
    """Compute a stable hash of an AST using canonical representation.
    
    The hash is computed from the canonical AST, which normalizes:
    - Commutative operations (sorted AND filters, sorted computes)
    - Numeric precision (floats to 10 decimal places)
    - Field aliases
    
    This ensures that semantically equivalent ASTs produce identical hashes.
    
    Args:
        ast: Query or SelectStmt AST
        
    Returns:
        Hex string of SHA256 hash (first 16 chars)
    """
    # Import here to avoid circular dependency
    from .ast import canonicalize_ast as canonical_ast_transform
    
    # For Query AST, use canonical transformation
    if hasattr(ast, '__class__') and ast.__class__.__name__ == 'Query':
        canonical = canonical_ast_transform(ast)
        # Use the repr-based canonicalization for hashing
        canonical_repr = _ast_repr(canonical)
        hasher = hashlib.sha256()
        hasher.update(canonical_repr.encode('utf-8'))
        return hasher.hexdigest()[:16]
    
    # Fallback to old canonicalization for other types
    canonical = _canonicalize_ast(ast)
    hasher = hashlib.sha256()
    hasher.update(canonical.encode('utf-8'))
    return hasher.hexdigest()[:16]


def _ast_repr(obj: Any, depth: int = 0) -> str:
    """Create a canonical string representation of AST for hashing.
    
    This is similar to _canonicalize_ast but works on already-canonical ASTs.
    
    Args:
        obj: AST node or value
        depth: Current recursion depth
        
    Returns:
        Canonical string representation
    """
    if depth > 20:
        return "..."
    
    if obj is None:
        return "null"
    
    if isinstance(obj, (str, int, float, bool)):
        return repr(obj)
    
    if isinstance(obj, (list, tuple)):
        items = [_ast_repr(item, depth + 1) for item in obj]
        return f"[{','.join(items)}]"
    
    if isinstance(obj, dict):
        items = sorted((k, _ast_repr(v, depth + 1)) for k, v in obj.items())
        pairs = [f"{k}:{v}" for k, v in items]
        return f"{{{','.join(pairs)}}}"
    
    if hasattr(obj, '__dict__'):
        cls_name = obj.__class__.__name__
        attrs = {}
        for k, v in obj.__dict__.items():
            if not k.startswith('_'):
                attrs[k] = _ast_repr(v, depth + 1)
        items = sorted((k, v) for k, v in attrs.items())
        pairs = [f"{k}:{v}" for k, v in items]
        return f"{cls_name}({','.join(pairs)})"
    
    return repr(obj)


def _canonicalize_ast(obj: Any, depth: int = 0) -> str:
    """Convert an AST object to a canonical string representation.
    
    Args:
        obj: AST node or value
        depth: Current recursion depth (for limiting)
        
    Returns:
        Canonical string representation
    """
    if depth > 20:
        return "..."
    
    if obj is None:
        return "null"
    
    if isinstance(obj, (str, int, float, bool)):
        return repr(obj)
    
    if isinstance(obj, (list, tuple)):
        items = [_canonicalize_ast(item, depth + 1) for item in obj]
        return "[" + ",".join(items) + "]"
    
    if isinstance(obj, dict):
        items = []
        for key in sorted(obj.keys()):
            items.append(f"{repr(key)}:{_canonicalize_ast(obj[key], depth + 1)}")
        return "{" + ",".join(items) + "}"
    
    if hasattr(obj, "__dict__"):
        # Dataclass or object with __dict__
        items = []
        for key in sorted(vars(obj).keys()):
            # Skip private attributes and known volatile attributes
            if key.startswith("_"):
                continue
            value = getattr(obj, key)
            items.append(f"{repr(key)}:{_canonicalize_ast(value, depth + 1)}")
        return f"{obj.__class__.__name__}({','.join(items)})"
    
    # Fallback: use repr
    return repr(type(obj).__name__)


def ast_summary(ast: Union['Query', 'SelectStmt', Any]) -> str:
    """Create a human-readable summary of an AST.
    
    Args:
        ast: Query or SelectStmt AST
        
    Returns:
        Short summary string (e.g., "SELECT nodes FROM layer='social' WHERE degree>5")
    """
    from .ast import Query, SelectStmt, Target
    
    parts = []
    
    # Handle Query wrapper
    if isinstance(ast, Query):
        select = ast.select
    elif isinstance(ast, SelectStmt):
        select = ast
    else:
        return str(type(ast).__name__)
    
    # Target
    target_str = select.target.value if hasattr(select.target, 'value') else str(select.target)
    parts.append(f"SELECT {target_str}")
    
    # Layer selection
    if select.layer_set is not None:
        parts.append(f"FROM {_summarize_layer_set(select.layer_set)}")
    elif select.layer_expr is not None:
        parts.append(f"FROM {_summarize_layer_expr(select.layer_expr)}")
    
    # WHERE conditions
    if select.where is not None:
        parts.append(f"WHERE {_summarize_conditions(select.where)}")
    
    # COMPUTE
    if select.compute:
        compute_names = [c.name for c in select.compute[:3]]  # First 3 only
        if len(select.compute) > 3:
            compute_names.append("...")
        parts.append(f"COMPUTE {','.join(compute_names)}")
    
    # GROUP BY
    if select.group_by:
        parts.append(f"GROUP BY {','.join(select.group_by[:2])}")
    
    # ORDER BY
    if select.order_by:
        parts.append(f"ORDER BY {','.join([o.key for o in select.order_by[:2]])}")
    
    # LIMIT
    if select.limit is not None:
        parts.append(f"LIMIT {select.limit}")
    
    return " ".join(parts)


def _summarize_layer_set(layer_set: Any) -> str:
    """Summarize a LayerSet object."""
    try:
        if hasattr(layer_set, '__str__'):
            return str(layer_set)
        return "LayerSet(...)"
    except Exception:
        return "LayerSet"


def _summarize_layer_expr(layer_expr: Any) -> str:
    """Summarize a LayerExpr object."""
    try:
        # LayerExpr has terms and ops
        if hasattr(layer_expr, 'terms') and layer_expr.terms:
            term_names = [str(t.name) for t in layer_expr.terms[:3]]
            if len(layer_expr.terms) > 3:
                term_names.append("...")
            return ",".join(term_names)
        return "layers"
    except Exception:
        return "layers"


def _summarize_conditions(where: Any) -> str:
    """Summarize WHERE conditions."""
    try:
        # ConditionExpr has atoms and ops
        if hasattr(where, 'atoms') and where.atoms:
            atom_strs = []
            for atom in where.atoms[:3]:  # First 3 atoms only
                if hasattr(atom, 'comparison') and atom.comparison:
                    cmp = atom.comparison
                    atom_strs.append(f"{cmp.left}{cmp.op}{cmp.right}")
                elif hasattr(atom, 'special') and atom.special:
                    atom_strs.append(str(atom.special.predicate))
            if len(where.atoms) > 3:
                atom_strs.append("...")
            
            # Join with operators
            if hasattr(where, 'ops') and where.ops:
                result = atom_strs[0] if atom_strs else ""
                for i, op in enumerate(where.ops):
                    if i + 1 < len(atom_strs):
                        result += f" {op} {atom_strs[i + 1]}"
                return result
            
            return " AND ".join(atom_strs)
        return "..."
    except Exception:
        return "..."


class ProvenanceBuilder:
    """Builder for constructing provenance records during query execution.
    
    Usage:
        builder = ProvenanceBuilder("dsl_v2_executor")
        builder.start_timer()
        builder.set_network(network)
        builder.set_query_ast(query)
        # ... execute query stages ...
        builder.record_stage("parse", 0.001)
        builder.record_stage("filter", 0.005)
        builder.add_warning("approximation used")
        provenance = builder.build()
    """
    
    def __init__(self, engine: str):
        """Initialize builder.
        
        Args:
            engine: Engine name (e.g., "dsl_v2_executor", "dsl_legacy")
        """
        self.engine = engine
        self.start_time: Optional[float] = None
        self.timestamp_utc: str = datetime.now(timezone.utc).isoformat()
        self.network_fp: Dict[str, Any] = {}
        self.network_ver: Optional[int] = None
        self.query_info: Dict[str, Any] = {}
        self.randomness_info: Dict[str, Any] = {}
        self.backend_info: Dict[str, Any] = {
            "graph_backend": "networkx",
            "algo_backends": [],
            "fast_path": False,
        }
        self.timings: Dict[str, float] = {}
        self.warnings: List[str] = []
    
    def start_timer(self) -> None:
        """Start the execution timer."""
        self.start_time = time.monotonic()
    
    def set_network(self, network: Any) -> None:
        """Set network fingerprint.
        
        Args:
            network: Multilayer network object
        """
        self.network_fp = network_fingerprint(network)
        
        # Try to get network version if available
        if hasattr(network, "_version"):
            self.network_ver = network._version
        elif hasattr(network, "version"):
            self.network_ver = network.version
    
    def set_query_ast(self, query: Union['Query', 'SelectStmt', Any]) -> None:
        """Set query information from AST.
        
        Args:
            query: Query or SelectStmt AST
        """
        from .ast import Query, SelectStmt, Target
        
        # Determine target
        if isinstance(query, Query):
            select = query.select
        elif isinstance(query, SelectStmt):
            select = query
        else:
            select = None
        
        target_str = "unknown"
        if select and hasattr(select, 'target'):
            target_str = select.target.value if hasattr(select.target, 'value') else str(select.target)
        
        self.query_info = {
            "target": target_str,
            "ast_hash": ast_fingerprint(query),
            "ast_summary": ast_summary(query),
            "params": {},  # Will be populated separately
        }
    
    def set_query_legacy(self, query_string: str, target: str) -> None:
        """Set query information for legacy DSL.
        
        Args:
            query_string: Raw query string
            target: "nodes" or "edges"
        """
        # For legacy, use query string hash as fingerprint
        hasher = hashlib.sha256()
        hasher.update(query_string.encode('utf-8'))
        
        self.query_info = {
            "target": target,
            "raw_string": query_string,
            "ast_hash": hasher.hexdigest()[:16],
            "ast_summary": query_string[:100],  # Truncate long queries
            "params": {},
        }
    
    def set_params(self, params: Dict[str, Any]) -> None:
        """Set query parameters.
        
        Args:
            params: Parameter dictionary
        """
        if self.query_info:
            self.query_info["params"] = dict(params) if params else {}
    
    def set_randomness(self, seed: Optional[int] = None, **kwargs: Any) -> None:
        """Set randomness configuration.
        
        Args:
            seed: Base seed if any
            **kwargs: Additional randomness config (n_samples, method, etc.)
        """
        self.randomness_info = {"seed": seed}
        self.randomness_info.update(kwargs)
    
    def set_backend_info(self, **kwargs: Any) -> None:
        """Set backend information.
        
        Args:
            **kwargs: Backend info (algo_backend, fast_path, etc.)
        """
        self.backend_info.update(kwargs)
    
    def record_stage(self, stage: str, duration_ms: float) -> None:
        """Record timing for a stage.
        
        Args:
            stage: Stage name (e.g., "parse", "filter", "compute")
            duration_ms: Duration in milliseconds
        """
        self.timings[stage] = duration_ms
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message.
        
        Args:
            warning: Warning message
        """
        self.warnings.append(warning)
    
    def build(self) -> Dict[str, Any]:
        """Build the final provenance record.
        
        Returns:
            Dictionary suitable for QueryResult.meta["provenance"]
        """
        # Calculate total time if timer was started
        if self.start_time is not None:
            total_time_ms = (time.monotonic() - self.start_time) * 1000
            self.timings["total_ms"] = total_time_ms
        
        record = ProvenanceRecord(
            engine=self.engine,
            py3plex_version=get_py3plex_version(),
            timestamp_utc=self.timestamp_utc,
            network_fingerprint=self.network_fp,
            network_version=self.network_ver,
            query=self.query_info,
            randomness=self.randomness_info,
            backend=self.backend_info,
            performance=self.timings,
            warnings=self.warnings,
        )
        
        return record.to_dict()
