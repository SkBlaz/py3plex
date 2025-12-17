"""
Tests for py3plex.algorithms.statistical_report module.

This module tests statistical report generation for networks.
"""

import json
import os
import pytest
import tempfile
from py3plex.core import multinet
from py3plex.algorithms.statistical_report import (
    generate_statistical_report,
)


class TestStatisticalReport:
    """Test statistical report generation."""

    def test_generate_text_report(self):
        """Test generating text format report."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        report = generate_statistical_report(net, output_format='text')
        
        assert isinstance(report, str), "Report should be a string"
        assert len(report) > 0, "Report should not be empty"

    def test_generate_html_report(self):
        """Test generating HTML format report."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        report = generate_statistical_report(net, output_format='html')
        
        assert isinstance(report, str)
        assert len(report) > 0

    def test_generate_json_report(self):
        """Test generating JSON format report."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        report = generate_statistical_report(net, output_format='json')
        
        assert isinstance(report, str)
        # Should be valid JSON
        data = json.loads(report)
        assert isinstance(data, dict)

    def test_generate_report_to_file(self):
        """Test saving report to file."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
        
        try:
            report = generate_statistical_report(
                net,
                output_format='text',
                output_file=temp_path
            )
            
            # Verify file was created
            assert os.path.exists(temp_path), "Report file should be created"
            
            # Verify file content matches report
            with open(temp_path, 'r') as f:
                file_content = f.read()
            assert file_content == report, "File content should match report"
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_generate_report_custom_sections(self):
        """Test generating report with custom sections."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        report = generate_statistical_report(
            net,
            output_format='text',
            include_sections=['basic', 'degree']
        )
        
        assert isinstance(report, str)
        assert len(report) > 0

    def test_generate_report_single_section(self):
        """Test generating report with single section."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        report = generate_statistical_report(
            net,
            output_format='json',
            include_sections=['basic']
        )
        
        assert isinstance(report, str)

    def test_generate_report_unknown_format(self):
        """Test error with unknown output format."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        
        with pytest.raises(ValueError, match="Unknown output format"):
            generate_statistical_report(net, output_format='unknown_format')

    def test_generate_report_empty_network(self):
        """Test report generation with network without core_network."""
        net = multinet.multi_layer_network(directed=False)
        
        # Should handle gracefully with basic section only
        report = generate_statistical_report(
            net,
            output_format='json',
            include_sections=['basic']
        )
        assert isinstance(report, str)

    def test_generate_report_all_sections(self):
        """Test report with all available sections."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        report = generate_statistical_report(
            net,
            output_format='json',
            include_sections=['basic', 'degree', 'layers', 'clustering', 'mixing']
        )
        
        assert isinstance(report, str)
        data = json.loads(report)
        # Should have at least some sections
        assert isinstance(data, dict)
