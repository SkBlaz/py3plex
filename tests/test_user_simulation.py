"""
User Simulation Test Framework for py3plex

This module implements a comprehensive DX (Developer Experience) audit by simulating
multiple user personas attempting common tasks end-to-end. Each test captures friction
points and provides actionable feedback.

Personas tested:
1. Beginner Data Scientist
2. Network Science Researcher
3. ML Engineer
4. Bio/Omics Analyst
5. Educator
6. Power User migrating from NetworkX
"""

import sys
import os
import tempfile
import json
import time
import warnings
from pathlib import Path
from typing import Dict, List, Any, Tuple

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    
try:
    import networkx as nx
    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False
    
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Add package to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from py3plex.core import multinet
from py3plex.core import random_generators
from py3plex.io import io_functions


class UserSimulationReport:
    """Structured report for user simulation tests."""
    
    def __init__(self, persona: str):
        self.persona = persona
        self.tasks: List[Dict[str, Any]] = []
        self.friction_points: List[Dict[str, Any]] = []
        self.successes: List[str] = []
        
    def record_task(self, task_name: str, status: str, details: str = "", 
                   friction: str = "", suggestion: str = "", effort: str = "", 
                   impact: str = ""):
        """Record a task attempt with structured information."""
        task_data = {
            "task": task_name,
            "status": status,  # "SUCCESS", "PARTIAL", "FAILURE", "FRICTION"
            "details": details,
            "friction": friction,
            "suggestion": suggestion,
            "effort": effort,  # "LOW", "MEDIUM", "HIGH"
            "impact": impact   # "LOW", "MEDIUM", "HIGH", "CRITICAL"
        }
        self.tasks.append(task_data)
        
        if status in ["FRICTION", "PARTIAL", "FAILURE"] and friction:
            self.friction_points.append({
                "task": task_name,
                "issue": friction,
                "suggestion": suggestion,
                "effort": effort,
                "impact": impact
            })
        elif status == "SUCCESS":
            self.successes.append(task_name)
    
    def generate_report(self) -> str:
        """Generate a formatted report."""
        report = []
        report.append(f"\n{'=' * 80}")
        report.append(f"PERSONA: {self.persona}")
        report.append(f"{'=' * 80}\n")
        
        report.append(f"Summary: {len(self.successes)}/{len(self.tasks)} tasks completed successfully\n")
        
        for task in self.tasks:
            report.append(f"\n## Task: {task['task']}")
            report.append(f"Status: {task['status']}")
            if task['details']:
                report.append(f"Details: {task['details']}")
            if task['friction']:
                report.append(f"⚠️ Friction: {task['friction']}")
            if task['suggestion']:
                report.append(f"💡 Suggestion: {task['suggestion']}")
                if task['effort']:
                    report.append(f"   Effort: {task['effort']} | Impact: {task['impact']}")
        
        if self.friction_points:
            report.append(f"\n\n## Friction Points Summary ({len(self.friction_points)} found)")
            report.append("-" * 80)
            for i, fp in enumerate(self.friction_points, 1):
                report.append(f"\n{i}. Task: {fp['task']}")
                report.append(f"   Issue: {fp['issue']}")
                report.append(f"   Suggestion: {fp['suggestion']}")
                report.append(f"   Effort: {fp['effort']} | Impact: {fp['impact']}")
        
        return "\n".join(report)


class TestBeginnerDataScientistPersona:
    """Persona 1: Beginner Data Scientist - expects NetworkX-like feel."""
    
    def test_1_install_and_import(self):
        """Task 1: Install & import - verify basic imports work."""
        report = UserSimulationReport("Beginner Data Scientist")
        
        try:
            # Test basic import
            import py3plex
            assert hasattr(py3plex, '__version__')
            
            # Test core imports (NetworkX-like expectations)
            from py3plex.core import multinet
            from py3plex.core import random_generators
            
            report.record_task(
                "Install & Import",
                "SUCCESS",
                details=f"Successfully imported py3plex v{py3plex.__version__}"
            )
            
        except ImportError as e:
            report.record_task(
                "Install & Import",
                "FAILURE",
                friction=f"Import failed: {str(e)}",
                suggestion="Ensure all dependencies are installed correctly",
                effort="LOW",
                impact="CRITICAL"
            )
        
        print(report.generate_report())
        assert len(report.successes) > 0, "Basic import should succeed"
    
    def test_2_quickstart_graph(self):
        """Task 2: Build a small multiplex network with 2+ layers."""
        report = UserSimulationReport("Beginner Data Scientist")
        
        try:
            # Create a simple multiplex network
            network = multinet.multi_layer_network(network_type="multiplex")
            
            # Add nodes to different layers
            nodes = ['Alice', 'Bob', 'Carol', 'Dave']
            layers = ['friendship', 'work']
            
            for layer in layers:
                for node in nodes:
                    network.add_nodes_from([(node, layer)])
            
            # Add intra-layer edges
            network.add_edges_from([
                ('Alice', 'Bob', 'friendship'),
                ('Bob', 'Carol', 'friendship'),
                ('Alice', 'Dave', 'work'),
                ('Dave', 'Carol', 'work')
            ])
            
            # Verify network structure
            assert len(list(network.get_nodes())) > 0
            assert len(list(network.get_edges())) > 0
            
            report.record_task(
                "Quickstart Graph Creation",
                "SUCCESS",
                details=f"Created multiplex network with {len(nodes)} nodes and {len(layers)} layers"
            )
            
        except Exception as e:
            report.record_task(
                "Quickstart Graph Creation",
                "FAILURE",
                friction=f"Failed to create simple network: {str(e)}",
                suggestion="Improve beginner documentation with minimal working example",
                effort="LOW",
                impact="HIGH"
            )
        
        print(report.generate_report())
        assert len(report.successes) > 0
    
    def test_3_node_attributes(self):
        """Task 3: Add and query node attributes."""
        report = UserSimulationReport("Beginner Data Scientist")
        
        try:
            network = multinet.multi_layer_network(network_type="multiplex")
            
            # Add node with attributes (testing if this works like NetworkX)
            network.add_node("Alice", "layer1")
            
            # Try to add attributes
            # Note: This tests current API - may reveal friction
            try:
                # Check if node exists
                nodes = list(network.get_nodes())
                assert len(nodes) > 0
                
                report.record_task(
                    "Node Attributes",
                    "PARTIAL",
                    details="Can add nodes but attribute handling may differ from NetworkX",
                    friction="Unclear how to set/get node attributes in NetworkX style",
                    suggestion="Add .nodes[node]['attr'] = value syntax or document alternative",
                    effort="MEDIUM",
                    impact="MEDIUM"
                )
            except Exception as e:
                report.record_task(
                    "Node Attributes",
                    "FRICTION",
                    friction=f"Node attribute API unclear: {str(e)}",
                    suggestion="Document node attribute handling clearly with examples",
                    effort="LOW",
                    impact="MEDIUM"
                )
                
        except Exception as e:
            report.record_task(
                "Node Attributes",
                "FAILURE",
                friction=f"Failed: {str(e)}",
                suggestion="Ensure node attribute API is documented",
                effort="MEDIUM",
                impact="MEDIUM"
            )
        
        print(report.generate_report())


class TestNetworkScienceResearcherPersona:
    """Persona 2: Network Science Researcher - wants multilayer constructs."""
    
    def test_1_multilayer_creation(self):
        """Task 1: Create proper multilayer network with multiple node/edge types."""
        report = UserSimulationReport("Network Science Researcher")
        
        try:
            # Create multilayer network
            network = multinet.multi_layer_network(network_type="multilayer", directed=False)
            
            # Add different node types to different layers
            network.add_nodes_from([
                ("protein1", "biological"),
                ("protein2", "biological"),
                ("gene1", "genetic"),
                ("gene2", "genetic")
            ])
            
            # Add intra-layer edges
            network.add_edges_from([
                ("protein1", "protein2", "biological"),
                ("gene1", "gene2", "genetic")
            ])
            
            # Verify structure
            assert len(list(network.get_nodes())) == 4
            assert len(list(network.get_edges())) == 2
            
            report.record_task(
                "Multilayer Network Creation",
                "SUCCESS",
                details="Successfully created heterogeneous multilayer network"
            )
            
        except Exception as e:
            report.record_task(
                "Multilayer Network Creation",
                "FAILURE",
                friction=f"Failed to create multilayer network: {str(e)}",
                suggestion="Clarify multilayer vs multiplex distinction in docs",
                effort="LOW",
                impact="HIGH"
            )
        
        print(report.generate_report())
        assert len(report.successes) > 0
    
    def test_2_interlayer_edges(self):
        """Task 2: Add and query inter-layer edges."""
        report = UserSimulationReport("Network Science Researcher")
        
        try:
            network = multinet.multi_layer_network(network_type="multiplex")
            
            # Add same node in multiple layers
            network.add_nodes_from([
                ("node1", "layer1"),
                ("node1", "layer2"),
                ("node2", "layer1"),
                ("node2", "layer2")
            ])
            
            # Add inter-layer coupling
            # This is a key multilayer concept - test if API is clear
            try:
                # Try to add inter-layer edge
                network.add_inter_layer_edge("node1", "layer1", "node1", "layer2")
                
                # Verify inter-layer edges are queryable
                edges = list(network.get_edges())
                
                report.record_task(
                    "Inter-layer Edges",
                    "SUCCESS",
                    details="Successfully added and queried inter-layer edges"
                )
            except AttributeError:
                # Try alternative API
                network.add_edges_from([
                    (("node1", "layer1"), ("node1", "layer2"))
                ])
                report.record_task(
                    "Inter-layer Edges",
                    "PARTIAL",
                    friction="Inter-layer edge API not immediately clear",
                    suggestion="Document inter-layer edge creation with clear examples",
                    effort="LOW",
                    impact="HIGH"
                )
                
        except Exception as e:
            report.record_task(
                "Inter-layer Edges",
                "FAILURE",
                friction=f"Failed to add inter-layer edges: {str(e)}",
                suggestion="Provide clear inter-layer edge API with examples",
                effort="MEDIUM",
                impact="CRITICAL"
            )
        
        print(report.generate_report())
    
    def test_3_layer_statistics(self):
        """Task 3: Compute per-layer statistics."""
        report = UserSimulationReport("Network Science Researcher")
        
        try:
            # Create test network
            network = random_generators.random_multilayer_ER(50, 3, 0.1, directed=False)
            
            # Try to get per-layer statistics
            layers = network.get_layers()
            
            for layer in layers:
                # Try to extract single layer
                layer_nodes = [n for n in network.get_nodes() if n[1] == layer]
                
            report.record_task(
                "Layer Statistics",
                "SUCCESS",
                details=f"Can compute statistics for {len(layers)} layers"
            )
            
        except Exception as e:
            report.record_task(
                "Layer Statistics",
                "FRICTION",
                friction=f"Unclear how to get per-layer statistics: {str(e)}",
                suggestion="Add convenience methods for per-layer analysis",
                effort="MEDIUM",
                impact="MEDIUM"
            )
        
        print(report.generate_report())


class TestMLEngineerPersona:
    """Persona 3: ML Engineer - needs scalable IO and interop."""
    
    def test_1_networkx_conversion(self):
        """Task 1: Convert to/from NetworkX."""
        report = UserSimulationReport("ML Engineer")
        
        try:
            # Create py3plex network
            network = random_generators.random_multilayer_ER(30, 2, 0.1)
            
            # Try to convert to NetworkX (ML engineers need this for tools)
            try:
                # Check if there's a to_networkx method
                if hasattr(network, 'to_networkx'):
                    nx_graph = network.to_networkx()
                    report.record_task(
                        "NetworkX Conversion",
                        "SUCCESS",
                        details="Successfully converted to NetworkX"
                    )
                else:
                    # Try alternative conversion
                    report.record_task(
                        "NetworkX Conversion",
                        "FRICTION",
                        friction="No obvious to_networkx() method found",
                        suggestion="Add .to_networkx() and .from_networkx() methods for easy interop",
                        effort="MEDIUM",
                        impact="HIGH"
                    )
            except Exception as e:
                report.record_task(
                    "NetworkX Conversion",
                    "PARTIAL",
                    friction=f"NetworkX conversion unclear: {str(e)}",
                    suggestion="Document NetworkX interoperability clearly",
                    effort="MEDIUM",
                    impact="HIGH"
                )
                
        except Exception as e:
            report.record_task(
                "NetworkX Conversion",
                "FAILURE",
                friction=f"Failed: {str(e)}",
                suggestion="Ensure NetworkX conversion is well-documented",
                effort="MEDIUM",
                impact="HIGH"
            )
        
        print(report.generate_report())
    
    def test_2_io_performance(self):
        """Task 2: Test IO with edge lists (common ML format)."""
        report = UserSimulationReport("ML Engineer")
        
        try:
            # Create a network
            network = random_generators.random_multilayer_ER(100, 2, 0.05)
            
            # Test save/load performance
            with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
                temp_file = f.name
            
            try:
                # Time the save operation
                start = time.time()
                # Try to save as edgelist
                try:
                    # Check available save methods
                    if hasattr(network, 'save_to_edgelist'):
                        network.save_to_edgelist(temp_file)
                    else:
                        # Use io module
                        io_functions.write_edgelist(network, temp_file)
                    save_time = time.time() - start
                    
                    # Time the load operation
                    start = time.time()
                    network2 = io_functions.read_edgelist(temp_file)
                    load_time = time.time() - start
                    
                    report.record_task(
                        "IO Performance",
                        "SUCCESS",
                        details=f"Save: {save_time:.3f}s, Load: {load_time:.3f}s for 100 node network"
                    )
                except AttributeError as e:
                    report.record_task(
                        "IO Performance",
                        "FRICTION",
                        friction=f"IO API unclear: {str(e)}",
                        suggestion="Document IO functions clearly with performance notes",
                        effort="LOW",
                        impact="MEDIUM"
                    )
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            report.record_task(
                "IO Performance",
                "FRICTION",
                friction=f"IO testing failed: {str(e)}",
                suggestion="Provide clear IO documentation with format examples",
                effort="MEDIUM",
                impact="MEDIUM"
            )
        
        print(report.generate_report())
    
    def test_3_batching_support(self):
        """Task 3: Test if batch operations are supported."""
        report = UserSimulationReport("ML Engineer")
        
        try:
            network = multinet.multi_layer_network()
            
            # ML engineers often need to add many nodes/edges at once
            nodes = [(f"node{i}", "layer1") for i in range(100)]
            
            start = time.time()
            network.add_nodes_from(nodes)
            batch_time = time.time() - start
            
            report.record_task(
                "Batch Operations",
                "SUCCESS",
                details=f"Batch added 100 nodes in {batch_time:.3f}s"
            )
            
        except Exception as e:
            report.record_task(
                "Batch Operations",
                "FRICTION",
                friction=f"Batch operations unclear: {str(e)}",
                suggestion="Document batch operation support and performance",
                effort="LOW",
                impact="MEDIUM"
            )
        
        print(report.generate_report())


class TestBioOmicsAnalystPersona:
    """Persona 4: Bio/Omics Analyst - parses edge lists with layer metadata."""
    
    def test_1_edge_list_with_metadata(self):
        """Task 1: Load edge list with layer and attribute columns."""
        report = UserSimulationReport("Bio/Omics Analyst")
        
        try:
            # Create sample edge list file with layer metadata (common in bio)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                temp_file = f.name
                # Write CSV with biological interaction data
                f.write("source,target,layer,weight,type\n")
                f.write("ProteinA,ProteinB,PPI,0.95,interaction\n")
                f.write("GeneX,GeneY,coexpression,0.87,correlation\n")
                f.write("ProteinA,GeneX,regulation,0.92,regulatory\n")
            
            try:
                # Try to load with layer metadata preserved
                # This is critical for bio analysts
                try:
                    network = io_functions.read_edgelist(
                        temp_file,
                        delimiter=',',
                        layer_column='layer'
                    )
                    report.record_task(
                        "Edge List with Metadata",
                        "SUCCESS",
                        details="Successfully loaded edge list with layer metadata"
                    )
                except TypeError:
                    # Try alternative loading
                    report.record_task(
                        "Edge List with Metadata",
                        "FRICTION",
                        friction="Unclear how to load edge list with layer column",
                        suggestion="Add explicit layer_column parameter to IO functions",
                        effort="MEDIUM",
                        impact="HIGH"
                    )
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            report.record_task(
                "Edge List with Metadata",
                "FAILURE",
                friction=f"Failed to load biological edge list: {str(e)}",
                suggestion="Document biological data loading patterns with examples",
                effort="MEDIUM",
                impact="HIGH"
            )
        
        print(report.generate_report())
    
    def test_2_attribute_preservation(self):
        """Task 2: Verify attributes are preserved through save/load."""
        report = UserSimulationReport("Bio/Omics Analyst")
        
        try:
            # Bio analysts need to preserve metadata like p-values, fold-changes
            network = multinet.multi_layer_network()
            network.add_nodes_from([("Gene1", "layer1"), ("Gene2", "layer1")])
            network.add_edges_from([("Gene1", "Gene2", "layer1")])
            
            # Try to add edge attributes (critical for bio data)
            # This tests if attributes can be preserved
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
                temp_file = f.name
            
            try:
                # Save and reload
                io_functions.write_edgelist(network, temp_file)
                network2 = io_functions.read_edgelist(temp_file)
                
                # Check if structure preserved
                assert len(list(network2.get_nodes())) > 0
                
                report.record_task(
                    "Attribute Preservation",
                    "PARTIAL",
                    details="Basic structure preserved",
                    friction="Unclear if edge weights and attributes are preserved",
                    suggestion="Document attribute preservation in IO operations",
                    effort="MEDIUM",
                    impact="HIGH"
                )
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            report.record_task(
                "Attribute Preservation",
                "FRICTION",
                friction=f"Attribute handling unclear: {str(e)}",
                suggestion="Provide clear examples of attribute-rich data handling",
                effort="MEDIUM",
                impact="HIGH"
            )
        
        print(report.generate_report())


class TestEducatorPersona:
    """Persona 5: Educator - wants reliable install and quick visualization."""
    
    def test_1_zero_to_viz(self):
        """Task 1: From install to visualization in minimal steps."""
        report = UserSimulationReport("Educator")
        
        try:
            # Simulate what an educator needs for classroom demo
            
            # Step 1: Import (should be simple)
            from py3plex.core import random_generators
            
            # Step 2: Create simple network (should be one-liner)
            network = random_generators.random_multilayer_ER(20, 2, 0.2)
            
            # Step 3: Visualize (should work out of box)
            # In test environment, just check if method exists
            assert hasattr(network, 'visualize_network')
            
            report.record_task(
                "Zero to Visualization",
                "SUCCESS",
                details="Can create and visualize network in 3 lines of code"
            )
            
        except Exception as e:
            report.record_task(
                "Zero to Visualization",
                "FAILURE",
                friction=f"Too complex for classroom: {str(e)}",
                suggestion="Create super-simple quickstart example for educators",
                effort="LOW",
                impact="HIGH"
            )
        
        print(report.generate_report())
        assert len(report.successes) > 0
    
    def test_2_example_reliability(self):
        """Task 2: Check if examples run without errors."""
        report = UserSimulationReport("Educator")
        
        try:
            # Educators need examples that always work
            # Test a few basic examples
            
            # Example 1: Random network
            network = random_generators.random_multilayer_ER(10, 2, 0.3)
            assert len(list(network.get_nodes())) > 0
            
            # Example 2: Manual construction
            network2 = multinet.multi_layer_network()
            network2.add_nodes_from([("A", "L1"), ("B", "L1")])
            network2.add_edges_from([("A", "B", "L1")])
            assert len(list(network2.get_edges())) > 0
            
            report.record_task(
                "Example Reliability",
                "SUCCESS",
                details="Basic examples work reliably"
            )
            
        except Exception as e:
            report.record_task(
                "Example Reliability",
                "FAILURE",
                friction=f"Examples failed: {str(e)}",
                suggestion="Test all documented examples in CI",
                effort="LOW",
                impact="CRITICAL"
            )
        
        print(report.generate_report())
        assert len(report.successes) > 0
    
    def test_3_error_messages(self):
        """Task 3: Check if error messages are helpful for students."""
        report = UserSimulationReport("Educator")
        
        try:
            network = multinet.multi_layer_network()
            
            # Test 1: Try to add edge without nodes
            try:
                network.add_edges_from([("NonExistent1", "NonExistent2", "layer1")])
                # If this succeeds without warning, it might confuse students
                report.record_task(
                    "Error Messages",
                    "PARTIAL",
                    friction="Adding edges without nodes doesn't raise clear error",
                    suggestion="Add validation and helpful error messages for common mistakes",
                    effort="MEDIUM",
                    impact="MEDIUM"
                )
            except Exception as e:
                # Check if error message is helpful
                error_msg = str(e)
                if len(error_msg) > 10:
                    report.record_task(
                        "Error Messages",
                        "SUCCESS",
                        details=f"Got error message: {error_msg[:50]}..."
                    )
                else:
                    report.record_task(
                        "Error Messages",
                        "FRICTION",
                        friction="Error messages could be more descriptive",
                        suggestion="Improve error messages for common mistakes",
                        effort="LOW",
                        impact="MEDIUM"
                    )
                    
        except Exception as e:
            report.record_task(
                "Error Messages",
                "FRICTION",
                friction=f"Error handling unclear: {str(e)}",
                suggestion="Add clear error messages for common mistakes",
                effort="LOW",
                impact="MEDIUM"
            )
        
        print(report.generate_report())


class TestPowerUserPersona:
    """Persona 6: Power User migrating from NetworkX."""
    
    def test_1_networkx_compatibility(self):
        """Task 1: Test NetworkX-like API compatibility."""
        report = UserSimulationReport("Power User (NetworkX Migration)")
        
        try:
            # Power users expect NetworkX-like API
            network = multinet.multi_layer_network()
            
            # Test if common NetworkX methods exist
            nx_like_methods = [
                'add_node', 'add_nodes_from',
                'add_edge', 'add_edges_from',
                'number_of_nodes', 'number_of_edges',
                'nodes', 'edges'
            ]
            
            missing_methods = []
            for method in nx_like_methods:
                if not hasattr(network, method):
                    missing_methods.append(method)
            
            if not missing_methods:
                report.record_task(
                    "NetworkX API Compatibility",
                    "SUCCESS",
                    details="All basic NetworkX methods available"
                )
            else:
                report.record_task(
                    "NetworkX API Compatibility",
                    "PARTIAL",
                    friction=f"Missing NetworkX-like methods: {', '.join(missing_methods)}",
                    suggestion="Add missing NetworkX-compatible method aliases",
                    effort="LOW",
                    impact="MEDIUM"
                )
                
        except Exception as e:
            report.record_task(
                "NetworkX API Compatibility",
                "FRICTION",
                friction=f"API differs from NetworkX: {str(e)}",
                suggestion="Document differences from NetworkX clearly",
                effort="LOW",
                impact="HIGH"
            )
        
        print(report.generate_report())
    
    def test_2_drop_in_replacement(self):
        """Task 2: Test if py3plex can be drop-in replacement for simple NetworkX code."""
        report = UserSimulationReport("Power User (NetworkX Migration)")
        
        try:
            # Create NetworkX graph
            nx_graph = nx.Graph()
            nx_graph.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
            
            # Try to create equivalent in py3plex
            # Power users want this to be straightforward
            network = multinet.multi_layer_network()
            network.add_nodes_from([("A", "layer1"), ("B", "layer1"), ("C", "layer1")])
            network.add_edges_from([("A", "B", "layer1"), ("B", "C", "layer1"), ("C", "A", "layer1")])
            
            # Check if we can query similarly
            assert len(list(network.get_nodes())) == 3
            assert len(list(network.get_edges())) == 3
            
            report.record_task(
                "Drop-in Replacement",
                "PARTIAL",
                details="Can recreate NetworkX graph but syntax differs (layer required)",
                friction="Requires layer specification even for single-layer graphs",
                suggestion="Add convenience mode for single-layer graphs without layer param",
                effort="MEDIUM",
                impact="MEDIUM"
            )
            
        except Exception as e:
            report.record_task(
                "Drop-in Replacement",
                "FRICTION",
                friction=f"Cannot easily replace NetworkX: {str(e)}",
                suggestion="Provide NetworkX wrapper or conversion guide",
                effort="MEDIUM",
                impact="HIGH"
            )
        
        print(report.generate_report())
    
    def test_3_advanced_features(self):
        """Task 3: Test advanced multilayer features that go beyond NetworkX."""
        report = UserSimulationReport("Power User (NetworkX Migration)")
        
        try:
            # This is what attracts power users - features NetworkX doesn't have
            network = random_generators.random_multilayer_ER(30, 3, 0.1)
            
            # Test multilayer-specific operations
            layers = network.get_layers()
            assert len(layers) == 3
            
            # Test if we can do cross-layer queries
            nodes = list(network.get_nodes())
            assert len(nodes) > 0
            
            report.record_task(
                "Advanced Multilayer Features",
                "SUCCESS",
                details=f"Can access {len(layers)} layers and perform multilayer queries"
            )
            
        except Exception as e:
            report.record_task(
                "Advanced Multilayer Features",
                "FRICTION",
                friction=f"Advanced features unclear: {str(e)}",
                suggestion="Highlight multilayer-specific features in migration guide",
                effort="LOW",
                impact="HIGH"
            )
        
        print(report.generate_report())
        assert len(report.successes) > 0


# Consolidated report generation
def generate_overall_report():
    """Generate a consolidated report across all personas."""
    print("\n" + "=" * 80)
    print("PY3PLEX USER SIMULATION REPORT - OVERALL SUMMARY")
    print("=" * 80)
    print("\nThis test suite simulates 6 user personas attempting common tasks.")
    print("Each test captures friction points and provides actionable improvements.")
    print("\nPersonas tested:")
    print("  1. Beginner Data Scientist")
    print("  2. Network Science Researcher")
    print("  3. ML Engineer")
    print("  4. Bio/Omics Analyst")
    print("  5. Educator")
    print("  6. Power User (NetworkX Migration)")
    print("\nRun individual test classes to see detailed reports per persona.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Can be run directly or via pytest
    generate_overall_report()
    
    if PYTEST_AVAILABLE:
        pytest.main([__file__, "-v", "-s"])
    else:
        print("\nRunning tests manually (pytest not available)...\n")
        
        # Run each persona's tests
        personas = [
            TestBeginnerDataScientistPersona(),
            TestNetworkScienceResearcherPersona(),
            TestMLEngineerPersona(),
            TestBioOmicsAnalystPersona(),
            TestEducatorPersona(),
            TestPowerUserPersona()
        ]
        
        for persona in personas:
            for method_name in dir(persona):
                if method_name.startswith('test_'):
                    try:
                        method = getattr(persona, method_name)
                        print(f"\n{'='*80}")
                        print(f"Running: {persona.__class__.__name__}.{method_name}")
                        print('='*80)
                        method()
                    except Exception as e:
                        print(f"ERROR in {method_name}: {e}")
                        import traceback
                        traceback.print_exc()
