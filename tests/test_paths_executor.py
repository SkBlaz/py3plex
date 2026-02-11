"""Tests for py3plex.paths.executor module.

Tests path query execution functions.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from py3plex.paths.executor import find_paths, execute_path_stmt
from py3plex.paths.result import PathResult


class TestFindPaths:
    """Test find_paths function."""
    
    @patch('py3plex.paths.executor.path_registry')
    def test_basic_shortest_path(self, mock_registry):
        """Test basic shortest path query."""
        # Setup mock
        mock_fn = Mock(return_value={'paths': [['A', 'B', 'C']]})
        mock_registry.get.return_value = mock_fn
        
        network = Mock()
        
        result = find_paths(
            network=network,
            source='A',
            target='C',
            path_type='shortest'
        )
        
        # Verify function was called
        mock_registry.get.assert_called_once_with('shortest')
        mock_fn.assert_called_once()
        
        # Verify result structure
        assert isinstance(result, PathResult)
        assert result.path_type == 'shortest'
        assert result.source == 'A'
        assert result.target == 'C'
        assert len(result.paths) == 1
        assert result.paths[0] == ['A', 'B', 'C']
    
    @patch('py3plex.paths.executor.path_registry')
    def test_with_layers(self, mock_registry):
        """Test path query with layer filtering."""
        mock_fn = Mock(return_value={'paths': [['A', 'B']]})
        mock_registry.get.return_value = mock_fn
        
        network = Mock()
        layers = ['layer1', 'layer2']
        
        result = find_paths(
            network=network,
            source='A',
            target='B',
            path_type='shortest',
            layers=layers
        )
        
        # Verify layers were passed
        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs['layers'] == layers
        
        # Verify metadata
        assert result.meta['layers'] == layers
    
    @patch('py3plex.paths.executor.path_registry')
    def test_cross_layer_paths(self, mock_registry):
        """Test cross-layer path query."""
        mock_fn = Mock(return_value={'paths': [[('A', 'l1'), ('B', 'l2')]]})
        mock_registry.get.return_value = mock_fn
        
        network = Mock()
        
        result = find_paths(
            network=network,
            source='A',
            target='B',
            path_type='shortest',
            cross_layer=True
        )
        
        # Verify cross_layer flag was passed
        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs['cross_layer'] is True
        
        # Verify metadata
        assert result.meta['cross_layer'] is True
    
    @patch('py3plex.paths.executor.path_registry')
    def test_with_limit(self, mock_registry):
        """Test path query with result limit."""
        paths = [['A', 'B'], ['A', 'C', 'B'], ['A', 'D', 'B'], ['A', 'E', 'B']]
        mock_fn = Mock(return_value={'paths': paths})
        mock_registry.get.return_value = mock_fn
        
        network = Mock()
        
        result = find_paths(
            network=network,
            source='A',
            target='B',
            path_type='all',
            limit=2
        )
        
        # Verify only 2 paths returned
        assert len(result.paths) == 2
        assert result.paths == paths[:2]
    
    @patch('py3plex.paths.executor.path_registry')
    def test_without_target(self, mock_registry):
        """Test path query without target (all paths from source)."""
        mock_fn = Mock(return_value={'paths': [['A', 'B'], ['A', 'C']]})
        mock_registry.get.return_value = mock_fn
        
        network = Mock()
        
        result = find_paths(
            network=network,
            source='A',
            target=None,
            path_type='shortest'
        )
        
        # Verify target is None
        assert result.target is None
        
        # Should still have paths
        assert len(result.paths) == 2
    
    @patch('py3plex.paths.executor.path_registry')
    def test_with_visit_frequency(self, mock_registry):
        """Test path query that returns visit frequency."""
        mock_fn = Mock(return_value={
            'paths': [['A', 'B', 'C']],
            'visit_frequency': {'A': 1.0, 'B': 0.8, 'C': 0.6}
        })
        mock_registry.get.return_value = mock_fn
        
        network = Mock()
        
        result = find_paths(
            network=network,
            source='A',
            target='C',
            path_type='random_walk'
        )
        
        # Verify visit frequency is included
        assert result.visit_frequency is not None
        assert result.visit_frequency['A'] == 1.0
        assert result.visit_frequency['B'] == 0.8
    
    @patch('py3plex.paths.executor.path_registry')
    def test_with_flow_values(self, mock_registry):
        """Test path query that returns flow values."""
        mock_fn = Mock(return_value={
            'paths': [[('A', 'B'), ('B', 'C')]],
            'flow_values': {('A', 'B'): 10, ('B', 'C'): 8}
        })
        mock_registry.get.return_value = mock_fn
        
        network = Mock()
        
        result = find_paths(
            network=network,
            source='A',
            target='C',
            path_type='flow'
        )
        
        # Verify flow values are included
        assert result.flow_values is not None
        assert result.flow_values[('A', 'B')] == 10
    
    @patch('py3plex.paths.executor.path_registry')
    def test_with_extra_params(self, mock_registry):
        """Test passing extra parameters to path algorithm."""
        mock_fn = Mock(return_value={'paths': [['A', 'B']]})
        mock_registry.get.return_value = mock_fn
        
        network = Mock()
        
        result = find_paths(
            network=network,
            source='A',
            target='B',
            path_type='shortest',
            weight='weight',
            cutoff=10
        )
        
        # Verify extra params were passed
        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs['weight'] == 'weight'
        assert call_kwargs['cutoff'] == 10
        
        # Verify params are in metadata
        assert result.meta['params']['weight'] == 'weight'
        assert result.meta['params']['cutoff'] == 10
    
    @patch('py3plex.paths.executor.path_registry')
    def test_empty_paths_result(self, mock_registry):
        """Test when no paths are found."""
        mock_fn = Mock(return_value={'paths': []})
        mock_registry.get.return_value = mock_fn
        
        network = Mock()
        
        result = find_paths(
            network=network,
            source='A',
            target='Z',
            path_type='shortest'
        )
        
        # Should handle empty paths gracefully
        assert result.paths == []
        assert isinstance(result, PathResult)
    
    @patch('py3plex.paths.executor.path_registry')
    def test_metadata_extraction(self, mock_registry):
        """Test that extra metadata is extracted from raw result."""
        mock_fn = Mock(return_value={
            'paths': [['A', 'B']],
            'algorithm': 'dijkstra',
            'execution_time': 0.5,
            'nodes_visited': 10
        })
        mock_registry.get.return_value = mock_fn
        
        network = Mock()
        
        result = find_paths(
            network=network,
            source='A',
            target='B',
            path_type='shortest'
        )
        
        # Verify extra metadata is in result
        assert result.meta['algorithm'] == 'dijkstra'
        assert result.meta['execution_time'] == 0.5
        assert result.meta['nodes_visited'] == 10


class TestExecutePathStmt:
    """Test execute_path_stmt function."""
    
    @patch('py3plex.paths.executor.find_paths')
    def test_basic_execution(self, mock_find):
        """Test basic PATH statement execution."""
        # Create mock statement
        stmt = Mock()
        stmt.source = 'A'
        stmt.target = 'B'
        stmt.path_type = 'shortest'
        stmt.layer_expr = None
        stmt.cross_layer = False
        stmt.limit = None
        stmt.params = {}
        
        # Setup mock return
        mock_result = Mock(spec=PathResult)
        mock_find.return_value = mock_result
        
        network = Mock()
        
        result = execute_path_stmt(network, stmt)
        
        # Verify find_paths was called correctly
        mock_find.assert_called_once_with(
            network=network,
            source='A',
            target='B',
            path_type='shortest',
            layers=None,
            cross_layer=False,
            limit=None
        )
        
        assert result == mock_result
    
    @patch('py3plex.paths.executor.find_paths')
    def test_with_layer_expression(self, mock_find):
        """Test execution with layer expression."""
        # Create mock statement with layer expression
        stmt = Mock()
        stmt.source = 'A'
        stmt.target = 'B'
        stmt.path_type = 'shortest'
        stmt.cross_layer = False
        stmt.limit = None
        stmt.params = {}
        
        # Mock layer expression
        layer_expr = Mock()
        layer_expr.get_layer_names.return_value = ['layer1', 'layer2']
        stmt.layer_expr = layer_expr
        
        mock_result = Mock(spec=PathResult)
        mock_find.return_value = mock_result
        
        network = Mock()
        
        result = execute_path_stmt(network, stmt)
        
        # Verify layers were extracted
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['layers'] == ['layer1', 'layer2']
    
    @patch('py3plex.paths.executor.find_paths')
    def test_with_params(self, mock_find):
        """Test execution with additional parameters."""
        stmt = Mock()
        stmt.source = 'A'
        stmt.target = 'B'
        stmt.path_type = 'flow'
        stmt.layer_expr = None
        stmt.cross_layer = True
        stmt.limit = 10
        stmt.params = {'capacity': 'capacity', 'cutoff': 100}
        
        mock_result = Mock(spec=PathResult)
        mock_find.return_value = mock_result
        
        network = Mock()
        
        result = execute_path_stmt(network, stmt)
        
        # Verify params were passed
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['capacity'] == 'capacity'
        assert call_kwargs['cutoff'] == 100
    
    @patch('py3plex.paths.executor.find_paths')
    def test_cross_layer_flag(self, mock_find):
        """Test that cross_layer flag is passed correctly."""
        stmt = Mock()
        stmt.source = 'A'
        stmt.target = 'B'
        stmt.path_type = 'shortest'
        stmt.layer_expr = None
        stmt.cross_layer = True
        stmt.limit = None
        stmt.params = {}
        
        mock_result = Mock(spec=PathResult)
        mock_find.return_value = mock_result
        
        network = Mock()
        
        execute_path_stmt(network, stmt)
        
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['cross_layer'] is True
    
    @patch('py3plex.paths.executor.find_paths')
    def test_limit_propagation(self, mock_find):
        """Test that limit is passed through correctly."""
        stmt = Mock()
        stmt.source = 'A'
        stmt.target = 'B'
        stmt.path_type = 'all'
        stmt.layer_expr = None
        stmt.cross_layer = False
        stmt.limit = 5
        stmt.params = {}
        
        mock_result = Mock(spec=PathResult)
        mock_find.return_value = mock_result
        
        network = Mock()
        
        execute_path_stmt(network, stmt)
        
        call_kwargs = mock_find.call_args[1]
        assert call_kwargs['limit'] == 5
