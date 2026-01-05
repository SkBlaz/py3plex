"""Query replay functionality for deterministic result reproduction.

This module provides the replay API that reconstructs query results from
provenance records.
"""

import warnings
from typing import Any, Dict, Optional

from .schema import ProvenanceSchema, ProvenanceMode
from .capture import NetworkCapture, restore_network


class ReplayError(Exception):
    """Exception raised during query replay."""
    pass


class ReplayContext:
    """Context for replaying a query.
    
    Holds the provenance record and reconstructed network for replay.
    """
    
    def __init__(self, provenance: ProvenanceSchema, network: Optional[Any] = None):
        """Initialize replay context.
        
        Args:
            provenance: Provenance record
            network: Optional pre-constructed network (if None, will be restored from provenance)
        """
        self.provenance = provenance
        self.network = network
        self._validated = False
    
    def validate(self, strict: bool = True) -> None:
        """Validate that replay is possible.
        
        Args:
            strict: If True, check version compatibility strictly
            
        Raises:
            ReplayError: If replay is not possible
        """
        prov = self.provenance
        
        # Check mode
        if prov.mode != ProvenanceMode.REPLAYABLE:
            raise ReplayError(
                f"Provenance mode is '{prov.mode.value}', not 'replayable'. "
                "Cannot replay queries without replayable provenance."
            )
        
        # Check required query fields
        if not prov.query.ast_serialized:
            raise ReplayError(
                "Query AST not serialized in provenance. "
                "Cannot replay without AST."
            )
        
        # Check network capture
        nc = prov.network_capture
        if not nc.snapshot_data and not nc.snapshot_external_path and not nc.delta_ops:
            raise ReplayError(
                "Network snapshot not captured in provenance. "
                "Cannot replay without network state."
            )
        
        # Check version compatibility if strict
        if strict:
            from py3plex.dsl.provenance import get_py3plex_version
            current_version = get_py3plex_version()
            recorded_version = prov.environment.py3plex_version
            
            if current_version != recorded_version:
                warnings.warn(
                    f"Version mismatch: recorded with py3plex {recorded_version}, "
                    f"replaying with {current_version}. Results may differ.",
                    UserWarning
                )
        
        self._validated = True
    
    def restore_network(self) -> Any:
        """Restore network from provenance.
        
        Returns:
            Restored multilayer network
            
        Raises:
            ReplayError: If network cannot be restored
        """
        if self.network is not None:
            return self.network
        
        nc = self.provenance.network_capture
        
        # Try inline snapshot first
        if nc.snapshot_data:
            try:
                capture = NetworkCapture.from_dict(nc.snapshot_data)
                self.network = restore_network(capture)
                return self.network
            except Exception as e:
                raise ReplayError(f"Failed to restore network from inline snapshot: {e}")
        
        # Try external snapshot
        if nc.snapshot_external_path:
            raise ReplayError(
                "External snapshot restoration not yet implemented. "
                f"Snapshot path: {nc.snapshot_external_path}"
            )
        
        # Try delta reconstruction
        if nc.delta_ops:
            raise ReplayError(
                "Delta-based reconstruction not yet implemented. "
                "Use snapshot-based capture for replay."
            )
        
        raise ReplayError("No network capture data available in provenance.")
    
    def reconstruct_query(self) -> Any:
        """Reconstruct query AST from provenance.
        
        Returns:
            Query object
            
        Raises:
            ReplayError: If query cannot be reconstructed
        """
        engine = self.provenance.query.engine
        
        if engine == "dsl_v2_executor":
            return self._reconstruct_dsl_v2_query()
        elif engine == "dsl_legacy":
            return self._reconstruct_legacy_query()
        else:
            raise ReplayError(f"Unsupported engine for replay: {engine}")
    
    def _reconstruct_dsl_v2_query(self) -> Any:
        """Reconstruct DSL v2 query from serialized AST."""
        from py3plex.dsl.ast import Query
        from py3plex.dsl.serializer import deserialize_query
        
        try:
            ast_data = self.provenance.query.ast_serialized
            if not ast_data:
                raise ReplayError("No serialized AST in provenance")
            
            # Deserialize AST
            query = deserialize_query(ast_data)
            return query
        except Exception as e:
            raise ReplayError(f"Failed to reconstruct DSL v2 query: {e}")
    
    def _reconstruct_legacy_query(self) -> str:
        """Reconstruct legacy DSL query string."""
        query_info = self.provenance.query
        raw_string = query_info.params.get("raw_string")
        
        if not raw_string:
            raise ReplayError("No raw query string in provenance")
        
        return raw_string


def replay_query(
    provenance: ProvenanceSchema,
    network: Optional[Any] = None,
    strict: bool = True,
    restore_randomness: bool = True
) -> Any:
    """Replay a query from provenance.
    
    Args:
        provenance: Provenance record
        network: Optional pre-constructed network (if None, restored from provenance)
        strict: If True, enforce strict version compatibility
        restore_randomness: If True, restore random state for deterministic replay
        
    Returns:
        QueryResult from replayed query
        
    Raises:
        ReplayError: If replay fails
    """
    # Create replay context
    ctx = ReplayContext(provenance, network)
    
    # Validate
    ctx.validate(strict=strict)
    
    # Restore network
    net = ctx.restore_network()
    
    # Reconstruct query
    query = ctx.reconstruct_query()
    
    # Restore randomness if needed
    if restore_randomness and provenance.randomness.used:
        _restore_random_state(provenance.randomness)
    
    # Execute query based on engine
    engine = provenance.query.engine
    
    if engine == "dsl_v2_executor":
        from py3plex.dsl import execute_ast
        
        # Get params
        params = provenance.query.params or {}
        
        # Execute
        result = execute_ast(net, query, params, progress=False)
        return result
    
    elif engine == "dsl_legacy":
        from py3plex.dsl_legacy import execute_query
        
        # Execute
        result = execute_query(net, query)
        return result
    
    else:
        raise ReplayError(f"Unsupported engine for replay: {engine}")


def _restore_random_state(randomness_info: Any) -> None:
    """Restore random state from provenance.
    
    Args:
        randomness_info: RandomnessInfo from provenance
    """
    import numpy as np
    
    # Set base seed if available
    if randomness_info.base_seed is not None:
        np.random.seed(randomness_info.base_seed)
        
        # Also set Python random module
        import random
        random.seed(randomness_info.base_seed)
    
    # If seed sequence entropy is available, use it
    if randomness_info.seed_sequence_entropy:
        try:
            from numpy.random import SeedSequence
            seq = SeedSequence(randomness_info.seed_sequence_entropy)
            # This creates a new Generator with the seed sequence
            # Individual stages can spawn from this
            # For now, just use the base seed
        except Exception:
            pass
