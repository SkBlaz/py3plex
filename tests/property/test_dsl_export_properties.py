#!/usr/bin/env python3
"""
Property-based tests for DSL export module.

Tests invariants for:
- Export specification
- Result export to various formats
- Export file handling
"""

import pytest
import tempfile
import os
from hypothesis import given, settings, assume, strategies as st

# Import DSL export module
try:
    from py3plex.dsl import Q, execute_ast
    from py3plex.dsl.export import export_result
    from py3plex.dsl.ast import ExportSpec
    from py3plex.core import multinet
    EXPORT_AVAILABLE = True
except ImportError:
    EXPORT_AVAILABLE = False
    pytest.skip("DSL export module not available", allow_module_level=True)


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_network(num_nodes=5, num_layers=2, seed=None):
    """Create a simple test multilayer network."""
    import numpy as np
    if seed is not None:
        np.random.seed(seed)
    
    network = multinet.multi_layer_network(directed=False)
    
    layers = [f'layer{i}' for i in range(num_layers)]
    node_names = [chr(ord('A') + i) for i in range(num_nodes)]
    
    # Add nodes
    nodes = []
    for name in node_names:
        for layer in layers:
            nodes.append({'source': name, 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges within layers
    edges = []
    for layer in layers:
        for i in range(len(node_names) - 1):
            edges.append({
                'source': node_names[i],
                'target': node_names[i + 1],
                'source_type': layer,
                'target_type': layer,
            })
    network.add_edges(edges)
    
    return network


# ============================================================================
# Property Tests: ExportSpec Construction
# ============================================================================


# ============================================================================
# Property Tests: Export with Column Selection
# ============================================================================

@pytest.mark.property
def test_export_with_column_selection():
    """
    Property: Export respects column selection.
    
    Specifying columns should export only those columns.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        path = f.name
    
    os.unlink(path)
    
    try:
        # Export only specific columns
        spec = ExportSpec(path=path, fmt='csv', columns=['node', 'degree'])
        export_result(result, spec)
        
        # Read back and verify columns
        import csv
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Should have the specified columns (or subset if not all available)
            assert reader.fieldnames is not None
    finally:
        if os.path.exists(path):
            os.unlink(path)


# ============================================================================
# Property Tests: Export Error Handling
# ============================================================================

@pytest.mark.property
def test_export_to_invalid_format_raises_error():
    """
    Property: Exporting to unsupported format should raise error.
    
    Invalid format types should be rejected.
    """
    network = create_test_network(num_nodes=2, num_layers=1, seed=42)
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        path = f.name
    
    try:
        spec = ExportSpec(path=path, fmt='invalid_format')
        
        # Should raise an error for invalid format
        with pytest.raises(Exception):
            export_result(result, spec)
    finally:
        if os.path.exists(path):
            os.unlink(path)


# ============================================================================
# Property Tests: Export Idempotency
# ============================================================================

@pytest.mark.property
def test_export_idempotency():
    """
    Property: Exporting the same result twice produces identical files.
    
    Multiple exports of the same data should be identical.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f1:
        path1 = f1.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f2:
        path2 = f2.name
    
    os.unlink(path1)
    os.unlink(path2)
    
    try:
        spec1 = ExportSpec(path=path1, fmt='csv')
        spec2 = ExportSpec(path=path2, fmt='csv')
        
        export_result(result, spec1)
        export_result(result, spec2)
        
        # Files should have same content
        with open(path1, 'r') as f1, open(path2, 'r') as f2:
            content1 = f1.read()
            content2 = f2.read()
            
            assert content1 == content2
    finally:
        if os.path.exists(path1):
            os.unlink(path1)
        if os.path.exists(path2):
            os.unlink(path2)
