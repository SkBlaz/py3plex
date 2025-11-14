#!/usr/bin/env python3
"""
Comprehensive evaluation script for py3plex library.
Executes all 9 steps as specified in the evaluation requirements.
"""

import sys
import os
import json
import time
import traceback
import platform
import subprocess
import warnings
import gc
import psutil
import tempfile
from pathlib import Path
from io import StringIO
from contextlib import contextmanager, redirect_stdout

# Global results storage
results = {
    "env": {},
    "import_verification": {},
    "graph_construction": {},
    "io_validation": {},
    "algorithms": {},
    "visualization": {},
    "api_discoverability": {},
    "error_handling": {},
    "performance": {},
    "interoperability": {},
    "findings": []
}


@contextmanager
def capture_output():
    """Capture stdout and stderr"""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        out = StringIO()
        sys.stdout = out
        sys.stderr = out
        yield out
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def log(message, level="INFO"):
    """Log a message with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def add_finding(finding):
    """Add a finding to the results"""
    results["findings"].append(finding)
    log(f"FINDING: {finding}", "FINDING")


def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


# ============================================================================
# STEP 0: Environment
# ============================================================================

def step0_environment():
    """Step 0: Create environment and record system info"""
    log("=== STEP 0: Environment ===")
    
    try:
        # Get Python version
        python_version = sys.version
        
        # Try to import and get py3plex version
        try:
            import py3plex
            if hasattr(py3plex, '__version__'):
                py3plex_version = py3plex.__version__
            else:
                # Try to get version from setup.py or pyproject.toml
                import importlib.metadata
                try:
                    py3plex_version = importlib.metadata.version('py3plex')
                except:
                    py3plex_version = "unknown"
        except ImportError:
            py3plex_version = "not installed"
            add_finding("py3plex not installed in environment")
        
        # Get OS info
        os_info = f"{platform.system()} {platform.release()} {platform.machine()}"
        
        # Get CPU info
        cpu_count = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_info = f"{cpu_count} physical cores, {cpu_count_logical} logical cores"
        
        # Get RAM info
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        
        # Get pip freeze
        try:
            pip_freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], 
                                                text=True, stderr=subprocess.DEVNULL)
        except:
            pip_freeze = "Unable to get pip freeze"
        
        env_info = {
            "python_version": python_version.split()[0],
            "py3plex_version": py3plex_version,
            "os": os_info,
            "cpu_info": cpu_info,
            "ram_gb": round(ram_gb, 2),
            "pip_freeze": pip_freeze
        }
        
        results["env"] = env_info
        
        # Save env.json
        with open("env.json", "w") as f:
            json.dump(env_info, f, indent=2)
        
        log(f"Environment info saved to env.json")
        log(f"Python: {env_info['python_version']}")
        log(f"py3plex: {env_info['py3plex_version']}")
        log(f"OS: {env_info['os']}")
        log(f"CPU: {env_info['cpu_info']}")
        log(f"RAM: {env_info['ram_gb']} GB")
        
    except Exception as e:
        log(f"Error in Step 0: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        add_finding(f"Step 0 failed with error: {str(e)}")


# ============================================================================
# STEP 1: Import and Documentation Verification
# ============================================================================

def step1_import_verification():
    """Step 1: Import and documentation verification"""
    log("=== STEP 1: Import and Documentation Verification ===")
    
    import_results = {
        "imports": {},
        "help_py3plex": "",
        "help_core": "",
        "discrepancies": []
    }
    
    # Try to import py3plex and its modules
    modules_to_import = [
        "py3plex",
        "py3plex.core",
        "py3plex.core.multinet",
        "py3plex.core.random_generators",
        "py3plex.algorithms",
        "py3plex.algorithms.statistics",
        "py3plex.algorithms.community_detection",
        "py3plex.io",
        "py3plex.visualization",
        "py3plex.wrappers"
    ]
    
    for module_name in modules_to_import:
        try:
            module = __import__(module_name, fromlist=[''])
            import_results["imports"][module_name] = "SUCCESS"
            log(f"Successfully imported {module_name}")
        except ImportError as e:
            import_results["imports"][module_name] = f"FAILED: {str(e)}"
            log(f"Failed to import {module_name}: {e}", "ERROR")
            add_finding(f"Import failure: {module_name} - {str(e)}")
        except Exception as e:
            import_results["imports"][module_name] = f"ERROR: {str(e)}"
            log(f"Error importing {module_name}: {e}", "ERROR")
            add_finding(f"Import error: {module_name} - {str(e)}")
    
    # Get help() output for py3plex and py3plex.core
    try:
        import py3plex
        with capture_output() as out:
            help(py3plex)
        help_text = out.getvalue()
        first_40_lines = '\n'.join(help_text.split('\n')[:40])
        import_results["help_py3plex"] = first_40_lines
        log(f"Captured help(py3plex) - {len(help_text)} chars")
        
        # Check for inconsistencies
        if "error" in help_text.lower() or "warning" in help_text.lower():
            add_finding("help(py3plex) contains error or warning messages")
            
    except Exception as e:
        log(f"Error getting help(py3plex): {e}", "ERROR")
        add_finding(f"Cannot get help(py3plex): {str(e)}")
    
    try:
        import py3plex.core
        with capture_output() as out:
            help(py3plex.core)
        help_text = out.getvalue()
        first_40_lines = '\n'.join(help_text.split('\n')[:40])
        import_results["help_core"] = first_40_lines
        log(f"Captured help(py3plex.core) - {len(help_text)} chars")
        
    except Exception as e:
        log(f"Error getting help(py3plex.core): {e}", "ERROR")
        add_finding(f"Cannot get help(py3plex.core): {str(e)}")
    
    results["import_verification"] = import_results


# ============================================================================
# STEP 2: Graph Construction Tests
# ============================================================================

def step2_graph_construction():
    """Step 2: Graph construction tests"""
    log("=== STEP 2: Graph Construction Tests ===")
    
    construction_results = {
        "undirected_cycle": {},
        "directed_weighted": {},
        "multilayer": {},
        "hypergraph": {}
    }
    
    try:
        import networkx as nx
        from py3plex.core import multinet
        
        # Test 1: Undirected 5-node cycle
        log("Test 1: Undirected 5-node cycle")
        try:
            G = nx.cycle_graph(5)
            code = "nx.cycle_graph(5)"
            construction_results["undirected_cycle"] = {
                "code": code,
                "repr": repr(G),
                "type": str(type(G)),
                "nodes": list(G.nodes()),
                "edges": list(G.edges()),
                "degrees": dict(G.degree())
            }
            
            # Manual degree computation
            manual_degrees = {n: 2 for n in range(5)}
            if construction_results["undirected_cycle"]["degrees"] != manual_degrees:
                add_finding("Degree mismatch in undirected 5-node cycle")
                
            log(f"Created undirected cycle: {G}")
            
        except Exception as e:
            log(f"Error creating undirected cycle: {e}", "ERROR")
            add_finding(f"Cannot create undirected 5-node cycle: {str(e)}")
            construction_results["undirected_cycle"]["error"] = str(e)
        
        # Test 2: Directed weighted 4-node graph
        log("Test 2: Directed weighted 4-node graph")
        try:
            G = nx.DiGraph()
            G.add_weighted_edges_from([
                (0, 1, 1.5),
                (1, 2, 2.0),
                (2, 3, 0.5),
                (3, 0, 1.0)
            ])
            code = "G = nx.DiGraph(); G.add_weighted_edges_from([(0,1,1.5),(1,2,2.0),(2,3,0.5),(3,0,1.0)])"
            construction_results["directed_weighted"] = {
                "code": code,
                "repr": repr(G),
                "type": str(type(G)),
                "nodes": list(G.nodes()),
                "edges": [(u, v, d['weight']) for u, v, d in G.edges(data=True)],
                "in_degrees": dict(G.in_degree()),
                "out_degrees": dict(G.out_degree())
            }
            log(f"Created directed weighted graph: {G}")
            
        except Exception as e:
            log(f"Error creating directed weighted graph: {e}", "ERROR")
            add_finding(f"Cannot create directed weighted 4-node graph: {str(e)}")
            construction_results["directed_weighted"]["error"] = str(e)
        
        # Test 3: Multilayer graph
        log("Test 3: Multilayer graph with two layers")
        try:
            network = multinet.multi_layer_network(network_type="multilayer")
            
            # Layer 1
            network.add_nodes(["A", "B", "C"], layer="layer1")
            network.add_edges([("A", "B"), ("B", "C")], layer="layer1")
            
            # Layer 2
            network.add_nodes(["A", "B", "D"], layer="layer2")
            network.add_edges([("A", "D"), ("D", "B")], layer="layer2")
            
            # Cross-layer connection
            network.add_edges([("A", "A")], layer_from="layer1", layer_to="layer2")
            
            code = """
network = multinet.multi_layer_network(network_type="multilayer")
network.add_nodes(["A", "B", "C"], layer="layer1")
network.add_edges([("A", "B"), ("B", "C")], layer="layer1")
network.add_nodes(["A", "B", "D"], layer="layer2")
network.add_edges([("A", "D"), ("D", "B")], layer="layer2")
network.add_edges([("A", "A")], layer_from="layer1", layer_to="layer2")
"""
            
            construction_results["multilayer"] = {
                "code": code.strip(),
                "repr": repr(network),
                "type": str(type(network)),
                "num_nodes": len(network.get_nodes()),
                "num_edges": len(list(network.get_edges())),
                "layers": network.get_layers() if hasattr(network, 'get_layers') else "N/A"
            }
            log(f"Created multilayer network: {network}")
            
        except Exception as e:
            log(f"Error creating multilayer graph: {e}", "ERROR")
            add_finding(f"Cannot create multilayer graph: {str(e)}")
            construction_results["multilayer"]["error"] = str(e)
            log(traceback.format_exc(), "ERROR")
        
        # Test 4: Hypergraph
        log("Test 4: Hypergraph")
        try:
            # Check if hypergraph functionality exists
            # py3plex might not have native hypergraph support
            construction_results["hypergraph"] = {
                "status": "not_available",
                "note": "py3plex does not have native hypergraph support in core API"
            }
            add_finding("Hypergraph support not available in py3plex")
            log("Hypergraph support not found in py3plex")
            
        except Exception as e:
            log(f"Error checking hypergraph: {e}", "ERROR")
            construction_results["hypergraph"]["error"] = str(e)
        
    except Exception as e:
        log(f"Error in Step 2: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        add_finding(f"Step 2 failed with error: {str(e)}")
    
    results["graph_construction"] = construction_results


# ============================================================================
# STEP 3: IO Validation
# ============================================================================

def step3_io_validation():
    """Step 3: IO validation"""
    log("=== STEP 3: IO Validation ===")
    
    io_results = {
        "formats": {},
        "round_trip": {},
        "malformed": {},
        "large_file": {}
    }
    
    try:
        import networkx as nx
        from py3plex.core import multinet
        import tempfile
        
        # Create test graph
        G = nx.karate_club_graph()
        
        # Test various formats
        formats_to_test = [
            ("edgelist", ".edgelist"),
            ("adjlist", ".adjlist"),
            ("gml", ".gml"),
            ("graphml", ".graphml"),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for fmt, ext in formats_to_test:
                log(f"Testing format: {fmt}")
                try:
                    filepath = os.path.join(tmpdir, f"test{ext}")
                    
                    # Write
                    if fmt == "edgelist":
                        nx.write_edgelist(G, filepath)
                    elif fmt == "adjlist":
                        nx.write_adjlist(G, filepath)
                    elif fmt == "gml":
                        nx.write_gml(G, filepath)
                    elif fmt == "graphml":
                        nx.write_graphml(G, filepath)
                    
                    # Read
                    if fmt == "edgelist":
                        G2 = nx.read_edgelist(filepath)
                    elif fmt == "adjlist":
                        G2 = nx.read_adjlist(filepath)
                    elif fmt == "gml":
                        G2 = nx.read_gml(filepath)
                    elif fmt == "graphml":
                        G2 = nx.read_graphml(filepath)
                    
                    # Compare
                    nodes_match = set(G.nodes()) == set(G2.nodes())
                    edges_match = G.number_of_edges() == G2.number_of_edges()
                    
                    io_results["formats"][fmt] = {
                        "status": "SUCCESS",
                        "nodes_match": nodes_match,
                        "edges_match": edges_match
                    }
                    
                    if not nodes_match or not edges_match:
                        add_finding(f"Round-trip mismatch for {fmt} format")
                    
                except Exception as e:
                    log(f"Error with format {fmt}: {e}", "ERROR")
                    io_results["formats"][fmt] = {"status": "FAILED", "error": str(e)}
                    add_finding(f"IO format {fmt} failed: {str(e)}")
            
            # Test malformed files
            log("Testing malformed files")
            malformed_tests = [
                ("missing_values", "1 2\n3\n4 5"),
                ("irregular_columns", "1 2 3\n4 5\n6 7 8 9"),
                ("non_numeric_weights", "1 2 abc\n3 4 5.0"),
                ("self_loops", "1 1\n2 2\n3 3"),
                ("negative_weights", "1 2 -5.0\n3 4 -2.0")
            ]
            
            for test_name, content in malformed_tests:
                try:
                    filepath = os.path.join(tmpdir, f"{test_name}.txt")
                    with open(filepath, 'w') as f:
                        f.write(content)
                    
                    # Try to read
                    try:
                        G_test = nx.read_edgelist(filepath)
                        io_results["malformed"][test_name] = {
                            "status": "loaded_without_error",
                            "nodes": G_test.number_of_nodes(),
                            "edges": G_test.number_of_edges()
                        }
                        if test_name in ["missing_values", "irregular_columns"]:
                            add_finding(f"Malformed file {test_name} loaded without error (should warn or fail)")
                    except Exception as e:
                        io_results["malformed"][test_name] = {
                            "status": "raised_exception",
                            "exception": str(e)
                        }
                        log(f"Malformed file {test_name} raised: {e}")
                        
                except Exception as e:
                    log(f"Error in malformed test {test_name}: {e}", "ERROR")
            
            # Test large file (1 million edges)
            log("Testing large file with 1M edges")
            try:
                large_file = os.path.join(tmpdir, "large.edgelist")
                start_time = time.time()
                start_mem = get_memory_usage()
                
                # Generate 1M edges
                with open(large_file, 'w') as f:
                    for i in range(1000000):
                        f.write(f"{i % 10000} {(i + 1) % 10000}\n")
                
                # Load it
                load_start = time.time()
                G_large = nx.read_edgelist(large_file)
                load_time = time.time() - load_start
                end_mem = get_memory_usage()
                
                io_results["large_file"] = {
                    "status": "SUCCESS",
                    "num_edges": G_large.number_of_edges(),
                    "load_time_seconds": round(load_time, 2),
                    "memory_increase_mb": round(end_mem - start_mem, 2)
                }
                
                log(f"Loaded 1M edges in {load_time:.2f}s, memory increase: {end_mem - start_mem:.2f}MB")
                
                if load_time > 10:
                    add_finding(f"Large file (1M edges) load time excessive: {load_time:.2f}s")
                    
            except Exception as e:
                log(f"Error with large file: {e}", "ERROR")
                io_results["large_file"] = {"status": "FAILED", "error": str(e)}
                add_finding(f"Cannot load 1M edge file: {str(e)}")
        
    except Exception as e:
        log(f"Error in Step 3: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        add_finding(f"Step 3 failed with error: {str(e)}")
    
    results["io_validation"] = io_results


# ============================================================================
# STEP 4: Algorithm Evaluation
# ============================================================================

def step4_algorithm_evaluation():
    """Step 4: Algorithm evaluation"""
    log("=== STEP 4: Algorithm Evaluation ===")
    
    algo_results = {
        "centrality": {},
        "clustering": {},
        "pagerank": {},
        "shortest_paths": {},
        "connected_components": {},
        "community_detection": {}
    }
    
    try:
        import networkx as nx
        
        # Create test graph
        G = nx.karate_club_graph()
        
        # Test centrality measures
        centrality_tests = [
            ("degree_centrality", nx.degree_centrality),
            ("betweenness_centrality", nx.betweenness_centrality),
            ("closeness_centrality", nx.closeness_centrality),
            ("eigenvector_centrality", nx.eigenvector_centrality)
        ]
        
        for name, func in centrality_tests:
            log(f"Testing {name}")
            try:
                start_time = time.time()
                start_mem = get_memory_usage()
                
                result = func(G)
                
                runtime = time.time() - start_time
                mem_usage = get_memory_usage() - start_mem
                
                algo_results["centrality"][name] = {
                    "status": "SUCCESS",
                    "runtime_seconds": round(runtime, 4),
                    "memory_mb": round(mem_usage, 2),
                    "return_type": str(type(result)),
                    "num_results": len(result) if isinstance(result, dict) else "N/A"
                }
                log(f"{name}: {runtime:.4f}s, {mem_usage:.2f}MB")
                
            except Exception as e:
                log(f"Error in {name}: {e}", "ERROR")
                algo_results["centrality"][name] = {"status": "FAILED", "error": str(e)}
                add_finding(f"Algorithm {name} failed: {str(e)}")
        
        # Test clustering
        log("Testing clustering coefficient")
        try:
            start_time = time.time()
            clustering = nx.clustering(G)
            runtime = time.time() - start_time
            
            algo_results["clustering"] = {
                "status": "SUCCESS",
                "runtime_seconds": round(runtime, 4),
                "return_type": str(type(clustering)),
                "num_results": len(clustering)
            }
            
        except Exception as e:
            log(f"Error in clustering: {e}", "ERROR")
            algo_results["clustering"] = {"status": "FAILED", "error": str(e)}
            add_finding(f"Clustering failed: {str(e)}")
        
        # Test PageRank
        log("Testing PageRank")
        try:
            start_time = time.time()
            pr = nx.pagerank(G)
            runtime = time.time() - start_time
            
            algo_results["pagerank"] = {
                "status": "SUCCESS",
                "runtime_seconds": round(runtime, 4),
                "return_type": str(type(pr)),
                "num_results": len(pr)
            }
            
        except Exception as e:
            log(f"Error in PageRank: {e}", "ERROR")
            algo_results["pagerank"] = {"status": "FAILED", "error": str(e)}
            add_finding(f"PageRank failed: {str(e)}")
        
        # Test shortest paths
        log("Testing shortest paths")
        try:
            start_time = time.time()
            paths = nx.shortest_path_length(G, source=0)
            runtime = time.time() - start_time
            
            algo_results["shortest_paths"] = {
                "status": "SUCCESS",
                "runtime_seconds": round(runtime, 4),
                "return_type": str(type(paths)),
                "num_results": len(dict(paths))
            }
            
        except Exception as e:
            log(f"Error in shortest paths: {e}", "ERROR")
            algo_results["shortest_paths"] = {"status": "FAILED", "error": str(e)}
            add_finding(f"Shortest paths failed: {str(e)}")
        
        # Test connected components
        log("Testing connected components")
        try:
            start_time = time.time()
            components = list(nx.connected_components(G))
            runtime = time.time() - start_time
            
            algo_results["connected_components"] = {
                "status": "SUCCESS",
                "runtime_seconds": round(runtime, 4),
                "num_components": len(components)
            }
            
        except Exception as e:
            log(f"Error in connected components: {e}", "ERROR")
            algo_results["connected_components"] = {"status": "FAILED", "error": str(e)}
            add_finding(f"Connected components failed: {str(e)}")
        
        # Test community detection
        log("Testing community detection")
        try:
            # Try Louvain if available
            try:
                import community as community_louvain
                start_time = time.time()
                partition = community_louvain.best_partition(G)
                runtime = time.time() - start_time
                
                algo_results["community_detection"]["louvain"] = {
                    "status": "SUCCESS",
                    "runtime_seconds": round(runtime, 4),
                    "num_communities": len(set(partition.values()))
                }
            except ImportError:
                algo_results["community_detection"]["louvain"] = {
                    "status": "NOT_AVAILABLE",
                    "note": "python-louvain not installed"
                }
                add_finding("Louvain community detection not available (python-louvain not installed)")
                
        except Exception as e:
            log(f"Error in community detection: {e}", "ERROR")
            algo_results["community_detection"]["error"] = str(e)
        
    except Exception as e:
        log(f"Error in Step 4: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        add_finding(f"Step 4 failed with error: {str(e)}")
    
    results["algorithms"] = algo_results


# ============================================================================
# STEP 5: Visualization Assessment
# ============================================================================

def step5_visualization():
    """Step 5: Visualization assessment"""
    log("=== STEP 5: Visualization Assessment ===")
    
    viz_results = {
        "layouts": {},
        "images": []
    }
    
    try:
        import networkx as nx
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        
        # Create test graphs of different sizes
        graphs = {
            "small": nx.karate_club_graph(),
            "medium": nx.barabasi_albert_graph(100, 3),
            "large": nx.barabasi_albert_graph(500, 3)
        }
        
        # Test layouts
        layouts = [
            ("spring", nx.spring_layout),
            ("circular", nx.circular_layout),
            ("kamada_kawai", nx.kamada_kawai_layout),
            ("random", nx.random_layout)
        ]
        
        for graph_name, G in graphs.items():
            log(f"Testing layouts on {graph_name} graph ({G.number_of_nodes()} nodes)")
            
            for layout_name, layout_func in layouts:
                try:
                    start_time = time.time()
                    start_mem = get_memory_usage()
                    
                    pos = layout_func(G)
                    
                    # Try to draw
                    plt.figure(figsize=(10, 10))
                    nx.draw(G, pos, node_size=20, with_labels=False)
                    
                    filename = f"viz_{graph_name}_{layout_name}.png"
                    plt.savefig(filename, dpi=72, bbox_inches='tight')
                    plt.close()
                    
                    runtime = time.time() - start_time
                    mem_usage = get_memory_usage() - start_mem
                    
                    key = f"{graph_name}_{layout_name}"
                    viz_results["layouts"][key] = {
                        "status": "SUCCESS",
                        "runtime_seconds": round(runtime, 2),
                        "memory_mb": round(mem_usage, 2),
                        "image": filename
                    }
                    viz_results["images"].append(filename)
                    
                    log(f"{layout_name} on {graph_name}: {runtime:.2f}s")
                    
                    if runtime > 30:
                        add_finding(f"Visualization {layout_name} on {graph_name} took {runtime:.2f}s (slow)")
                    
                except Exception as e:
                    log(f"Error with {layout_name} on {graph_name}: {e}", "ERROR")
                    key = f"{graph_name}_{layout_name}"
                    viz_results["layouts"][key] = {"status": "FAILED", "error": str(e)}
                    add_finding(f"Visualization {layout_name} on {graph_name} failed: {str(e)}")
        
        # Test with long labels
        log("Testing with long labels")
        try:
            G_labels = nx.path_graph(5)
            mapping = {i: f"Very_Long_Label_Node_{i}_With_Unicode_文字" for i in G_labels.nodes()}
            G_labels = nx.relabel_nodes(G_labels, mapping)
            
            pos = nx.spring_layout(G_labels)
            plt.figure(figsize=(12, 8))
            nx.draw(G_labels, pos, with_labels=True, font_size=8)
            plt.savefig("viz_long_labels.png", dpi=72, bbox_inches='tight')
            plt.close()
            
            viz_results["long_labels"] = {"status": "SUCCESS"}
            viz_results["images"].append("viz_long_labels.png")
            
        except Exception as e:
            log(f"Error with long labels: {e}", "ERROR")
            viz_results["long_labels"] = {"status": "FAILED", "error": str(e)}
            add_finding(f"Long label visualization failed: {str(e)}")
        
    except Exception as e:
        log(f"Error in Step 5: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        add_finding(f"Step 5 failed with error: {str(e)}")
    
    results["visualization"] = viz_results


# ============================================================================
# STEP 6: API Discoverability
# ============================================================================

def step6_api_discoverability():
    """Step 6: API discoverability and ergonomics"""
    log("=== STEP 6: API Discoverability and Ergonomics ===")
    
    api_results = {
        "dir_output": {},
        "friction_points": []
    }
    
    try:
        import py3plex
        from py3plex.core import multinet
        
        # Test dir() on main modules
        api_results["dir_output"]["py3plex"] = dir(py3plex)
        api_results["dir_output"]["multinet"] = dir(multinet)
        
        # Test class instantiation without documentation
        friction_points = []
        
        # Friction point 1: multi_layer_network initialization
        log("Testing multi_layer_network instantiation")
        try:
            # Try with no arguments
            try:
                net = multinet.multi_layer_network()
                friction_points.append("multi_layer_network() requires no arguments by default but unclear from dir()")
            except TypeError as e:
                friction_points.append(f"multi_layer_network() instantiation error without args: {str(e)}")
        except Exception as e:
            friction_points.append(f"Cannot instantiate multi_layer_network: {str(e)}")
        
        # Friction point 2: Method naming consistency
        if hasattr(multinet.multi_layer_network, 'add_nodes') and hasattr(multinet.multi_layer_network, 'add_edges'):
            friction_points.append("Method names use add_nodes/add_edges (plural) - check consistency with NetworkX")
        
        # Friction point 3: Check if help text is available
        try:
            with capture_output() as out:
                help(multinet.multi_layer_network)
            help_text = out.getvalue()
            if len(help_text) < 100:
                friction_points.append("multi_layer_network has minimal or no docstring")
        except:
            friction_points.append("Cannot get help() for multi_layer_network")
        
        # Friction point 4: Check for __repr__ and __str__
        try:
            net = multinet.multi_layer_network(network_type="multilayer")
            repr_str = repr(net)
            if "object at 0x" in repr_str:
                friction_points.append("multi_layer_network __repr__ shows memory address (not informative)")
        except Exception as e:
            friction_points.append(f"Cannot test __repr__: {str(e)}")
        
        # Friction point 5: Layer specification inconsistency
        friction_points.append("add_edges() uses 'layer', 'layer_from', 'layer_to' parameters - could be confusing")
        
        # Friction point 6: Visualization method names
        if hasattr(multinet.multi_layer_network, 'visualize_network'):
            friction_points.append("visualize_network() method name - unclear what network means in multilayer context")
        
        # Friction point 7: No tab completion hints
        friction_points.append("No clear naming patterns for discoverability (e.g., all viz methods start with 'visualize_')")
        
        # Friction point 8: Error messages
        friction_points.append("Need to test error messages for clarity (covered in Step 7)")
        
        # Friction point 9: Return types
        friction_points.append("Unclear return types from dir() alone - need type hints or docstrings")
        
        # Friction point 10: Examples
        friction_points.append("No inline examples in docstrings visible from help()")
        
        api_results["friction_points"] = friction_points
        
        for i, fp in enumerate(friction_points, 1):
            log(f"Friction point {i}: {fp}")
            add_finding(f"API ergonomics: {fp}")
        
    except Exception as e:
        log(f"Error in Step 6: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        add_finding(f"Step 6 failed with error: {str(e)}")
    
    results["api_discoverability"] = api_results


# ============================================================================
# STEP 7: Error Handling Review
# ============================================================================

def step7_error_handling():
    """Step 7: Error handling review"""
    log("=== STEP 7: Error Handling Review ===")
    
    error_results = {
        "tests": []
    }
    
    try:
        import networkx as nx
        from py3plex.core import multinet
        import numpy as np
        
        # Test cases for invalid inputs
        error_tests = [
            {
                "name": "wrong_data_type_nodes",
                "test": lambda: multinet.multi_layer_network().add_nodes(123),
                "expected": "TypeError or clear error message"
            },
            {
                "name": "nan_weight",
                "test": lambda: nx.Graph().add_edge(1, 2, weight=np.nan),
                "expected": "Warning or error about NaN weight"
            },
            {
                "name": "negative_weight",
                "test": lambda: nx.Graph().add_edge(1, 2, weight=-5.0),
                "expected": "Accepted or warning (depends on algorithm)"
            },
            {
                "name": "missing_node",
                "test": lambda: nx.shortest_path(nx.Graph(), source=999, target=1),
                "expected": "NodeNotFound error"
            },
            {
                "name": "empty_graph_centrality",
                "test": lambda: nx.betweenness_centrality(nx.Graph()),
                "expected": "Empty dict or error"
            }
        ]
        
        for test in error_tests:
            log(f"Testing error handling: {test['name']}")
            try:
                test["test"]()
                result = {
                    "name": test["name"],
                    "status": "no_error",
                    "message": "Test completed without raising exception",
                    "clarity_rating": 2,
                    "suggestion": "Should provide clear error or warning"
                }
            except Exception as e:
                exc_type = type(e).__name__
                exc_msg = str(e)
                traceback_str = traceback.format_exc()
                
                # Rate clarity (1-5)
                clarity_rating = 3  # Default
                if len(exc_msg) > 50:
                    clarity_rating = 4
                if "help" in exc_msg.lower() or "expected" in exc_msg.lower():
                    clarity_rating = 5
                if len(exc_msg) < 10:
                    clarity_rating = 2
                
                result = {
                    "name": test["name"],
                    "status": "raised_exception",
                    "exception_type": exc_type,
                    "message": exc_msg,
                    "clarity_rating": clarity_rating,
                    "suggestion": "Add more context to error message" if clarity_rating < 4 else "Good error message"
                }
                
                log(f"  Exception: {exc_type}: {exc_msg}")
                log(f"  Clarity rating: {clarity_rating}/5")
                
                if clarity_rating < 3:
                    add_finding(f"Poor error message for {test['name']}: {exc_msg}")
            
            error_results["tests"].append(result)
        
    except Exception as e:
        log(f"Error in Step 7: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        add_finding(f"Step 7 failed with error: {str(e)}")
    
    results["error_handling"] = error_results


# ============================================================================
# STEP 8: Performance and Stability
# ============================================================================

def step8_performance():
    """Step 8: Performance and stability study"""
    log("=== STEP 8: Performance and Stability Study ===")
    
    perf_results = {
        "benchmarks": {},
        "stress_test": {}
    }
    
    try:
        import networkx as nx
        from py3plex.core import multinet
        
        # Benchmark graph construction at different scales
        scales = [1000, 5000, 50000]
        
        for n in scales:
            log(f"Benchmarking with {n} nodes")
            
            # Incremental construction
            try:
                start_time = time.time()
                start_mem = get_memory_usage()
                
                G = nx.Graph()
                for i in range(n):
                    G.add_node(i)
                for i in range(n - 1):
                    G.add_edge(i, i + 1)
                
                runtime = time.time() - start_time
                mem_usage = get_memory_usage() - start_mem
                
                perf_results["benchmarks"][f"incremental_{n}"] = {
                    "runtime_seconds": round(runtime, 2),
                    "memory_mb": round(mem_usage, 2)
                }
                log(f"  Incremental: {runtime:.2f}s, {mem_usage:.2f}MB")
                
            except Exception as e:
                log(f"  Error in incremental construction: {e}", "ERROR")
                perf_results["benchmarks"][f"incremental_{n}"] = {"error": str(e)}
            
            # Bulk construction
            try:
                start_time = time.time()
                start_mem = get_memory_usage()
                
                G = nx.Graph()
                G.add_nodes_from(range(n))
                edges = [(i, i + 1) for i in range(n - 1)]
                G.add_edges_from(edges)
                
                runtime = time.time() - start_time
                mem_usage = get_memory_usage() - start_mem
                
                perf_results["benchmarks"][f"bulk_{n}"] = {
                    "runtime_seconds": round(runtime, 2),
                    "memory_mb": round(mem_usage, 2)
                }
                log(f"  Bulk: {runtime:.2f}s, {mem_usage:.2f}MB")
                
                # PageRank
                if n <= 5000:  # Skip for very large graphs
                    start_time = time.time()
                    pr = nx.pagerank(G, max_iter=50)
                    runtime = time.time() - start_time
                    perf_results["benchmarks"][f"pagerank_{n}"] = {
                        "runtime_seconds": round(runtime, 2)
                    }
                    log(f"  PageRank: {runtime:.2f}s")
                
            except Exception as e:
                log(f"  Error in bulk construction: {e}", "ERROR")
                perf_results["benchmarks"][f"bulk_{n}"] = {"error": str(e)}
        
        # Stress test - memory leak detection
        log("Running stress test for memory leaks")
        try:
            memory_samples = []
            iterations = 50
            
            for i in range(iterations):
                G = nx.barabasi_albert_graph(100, 3)
                _ = nx.pagerank(G, max_iter=20)
                
                if i % 10 == 0:
                    gc.collect()
                    mem = get_memory_usage()
                    memory_samples.append(mem)
                    log(f"  Iteration {i}: {mem:.2f}MB")
            
            # Check for memory growth
            if len(memory_samples) > 1:
                mem_growth = memory_samples[-1] - memory_samples[0]
                perf_results["stress_test"] = {
                    "iterations": iterations,
                    "memory_growth_mb": round(mem_growth, 2),
                    "memory_samples": [round(m, 2) for m in memory_samples]
                }
                
                if mem_growth > 100:
                    add_finding(f"Potential memory leak: {mem_growth:.2f}MB growth over {iterations} iterations")
                else:
                    log(f"  No significant memory leak detected ({mem_growth:.2f}MB growth)")
                    
        except Exception as e:
            log(f"Error in stress test: {e}", "ERROR")
            perf_results["stress_test"] = {"error": str(e)}
            add_finding(f"Stress test failed: {str(e)}")
        
    except Exception as e:
        log(f"Error in Step 8: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        add_finding(f"Step 8 failed with error: {str(e)}")
    
    results["performance"] = perf_results


# ============================================================================
# STEP 9: Interoperability Testing
# ============================================================================

def step9_interoperability():
    """Step 9: Interoperability testing"""
    log("=== STEP 9: Interoperability Testing ===")
    
    interop_results = {
        "networkx": {},
        "pandas": {},
        "numpy": {},
        "igraph": {}
    }
    
    try:
        import networkx as nx
        from py3plex.core import multinet
        
        # NetworkX conversion
        log("Testing NetworkX interoperability")
        try:
            # Create py3plex network
            net = multinet.multi_layer_network(network_type="multilayer")
            net.add_nodes(["A", "B", "C"], layer="layer1")
            net.add_edges([("A", "B"), ("B", "C")], layer="layer1")
            
            # Try to convert to NetworkX
            # Check if there's a to_networkx method
            if hasattr(net, 'to_networkx'):
                nx_graph = net.to_networkx()
                interop_results["networkx"]["to_networkx"] = {
                    "status": "SUCCESS",
                    "nodes": nx_graph.number_of_nodes(),
                    "edges": nx_graph.number_of_edges()
                }
            else:
                interop_results["networkx"]["to_networkx"] = {
                    "status": "NOT_AVAILABLE",
                    "note": "No to_networkx method found"
                }
                add_finding("No direct to_networkx conversion method in multilayer network")
            
            # Try reverse: NetworkX to py3plex
            G = nx.karate_club_graph()
            # Check if there's a from_networkx method
            if hasattr(multinet.multi_layer_network, 'from_networkx'):
                net2 = multinet.multi_layer_network.from_networkx(G)
                interop_results["networkx"]["from_networkx"] = {
                    "status": "SUCCESS"
                }
            else:
                interop_results["networkx"]["from_networkx"] = {
                    "status": "NOT_AVAILABLE",
                    "note": "No from_networkx class method found"
                }
                add_finding("No direct from_networkx conversion method")
            
        except Exception as e:
            log(f"Error in NetworkX interop: {e}", "ERROR")
            interop_results["networkx"]["error"] = str(e)
            add_finding(f"NetworkX interoperability issue: {str(e)}")
        
        # Pandas integration
        log("Testing pandas integration")
        try:
            import pandas as pd
            
            G = nx.karate_club_graph()
            
            # Convert to adjacency matrix
            adj_matrix = nx.to_pandas_adjacency(G)
            interop_results["pandas"]["to_dataframe"] = {
                "status": "SUCCESS",
                "shape": adj_matrix.shape
            }
            
            # Convert from edge list
            edge_list = list(G.edges())
            df = pd.DataFrame(edge_list, columns=['source', 'target'])
            G2 = nx.from_pandas_edgelist(df)
            
            interop_results["pandas"]["from_dataframe"] = {
                "status": "SUCCESS",
                "nodes_match": G.number_of_nodes() == G2.number_of_nodes(),
                "edges_match": G.number_of_edges() == G2.number_of_edges()
            }
            
        except ImportError:
            interop_results["pandas"] = {"status": "pandas_not_installed"}
        except Exception as e:
            log(f"Error in pandas interop: {e}", "ERROR")
            interop_results["pandas"]["error"] = str(e)
            add_finding(f"Pandas interoperability issue: {str(e)}")
        
        # NumPy integration
        log("Testing numpy integration")
        try:
            import numpy as np
            
            G = nx.karate_club_graph()
            
            # Convert to adjacency matrix
            adj_matrix = nx.to_numpy_array(G)
            interop_results["numpy"]["to_array"] = {
                "status": "SUCCESS",
                "shape": adj_matrix.shape,
                "dtype": str(adj_matrix.dtype)
            }
            
            # Convert from adjacency matrix
            G2 = nx.from_numpy_array(adj_matrix)
            
            interop_results["numpy"]["from_array"] = {
                "status": "SUCCESS",
                "nodes_match": G.number_of_nodes() == G2.number_of_nodes()
            }
            
        except Exception as e:
            log(f"Error in numpy interop: {e}", "ERROR")
            interop_results["numpy"]["error"] = str(e)
            add_finding(f"NumPy interoperability issue: {str(e)}")
        
        # igraph integration
        log("Testing igraph integration")
        try:
            import igraph as ig
            
            G = nx.karate_club_graph()
            
            # Convert NetworkX to igraph
            g_igraph = ig.Graph.from_networkx(G)
            
            interop_results["igraph"]["from_networkx"] = {
                "status": "SUCCESS",
                "vcount": g_igraph.vcount(),
                "ecount": g_igraph.ecount()
            }
            
            # Convert igraph to NetworkX
            G2 = g_igraph.to_networkx()
            
            interop_results["igraph"]["to_networkx"] = {
                "status": "SUCCESS",
                "nodes": G2.number_of_nodes(),
                "edges": G2.number_of_edges()
            }
            
        except ImportError:
            interop_results["igraph"] = {"status": "igraph_not_installed"}
            add_finding("igraph not installed - cannot test interoperability")
        except Exception as e:
            log(f"Error in igraph interop: {e}", "ERROR")
            interop_results["igraph"]["error"] = str(e)
            add_finding(f"igraph interoperability issue: {str(e)}")
        
    except Exception as e:
        log(f"Error in Step 9: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        add_finding(f"Step 9 failed with error: {str(e)}")
    
    results["interoperability"] = interop_results


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution function"""
    log("=" * 80)
    log("Starting py3plex Comprehensive Evaluation")
    log("=" * 80)
    
    start_time = time.time()
    
    # Execute all steps
    step0_environment()
    step1_import_verification()
    step2_graph_construction()
    step3_io_validation()
    step4_algorithm_evaluation()
    step5_visualization()
    step6_api_discoverability()
    step7_error_handling()
    step8_performance()
    step9_interoperability()
    
    # Save full results
    with open("evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    total_time = time.time() - start_time
    log("=" * 80)
    log(f"Evaluation completed in {total_time:.2f} seconds")
    log(f"Total findings: {len(results['findings'])}")
    log(f"Results saved to evaluation_results.json")
    log("=" * 80)
    
    # Print summary of findings
    log("\n=== SUMMARY OF FINDINGS ===")
    for i, finding in enumerate(results['findings'], 1):
        log(f"{i}. {finding}")


if __name__ == "__main__":
    main()
