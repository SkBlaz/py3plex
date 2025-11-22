# high level interface for community detection algorithms
from collections import defaultdict
from typing import Any, Dict, List, Union

import networkx as nx

from py3plex.exceptions import Py3plexIOError

from .community_louvain import best_partition

try:
    from .NoRC import NoRC_communities_main
except ImportError:
    pass


def run_infomap(
    infile: str,
    multiplex: bool = True,
    overlapping: bool = False,
    binary: str = "./infomap",
    verbose: bool = True,
    iterations: int = 1000,
    seed: int = None,
) -> None:

    import os
    import subprocess

    # Check if binary exists and is executable
    if not os.path.exists(binary):
        raise Py3plexIOError(
            f"Infomap binary not found at '{binary}'. "
            f"Please provide a valid path to the Infomap binary using the 'binary' parameter, "
            f"or install Infomap from https://www.mapequation.org/infomap/. "
            f"Alternatively, use Louvain community detection: "
            f"partition = louvain_communities(network)"
        )

    if not os.access(binary, os.X_OK):
        raise Py3plexIOError(
            f"Infomap binary at '{binary}' is not executable. "
            f"Please run: chmod +x {binary}"
        )

    # Ensure output directory exists
    os.makedirs("out", exist_ok=True)

    # Build base command with seed if provided
    seed_args = [f"--seed {seed}"] if seed is not None else []

    if verbose:
        if multiplex:
            cmd = [
                binary,
                infile,
                "out/",
                "-i multiplex",
                "-N " + str(iterations),
            ] + seed_args
            subprocess.run(cmd, check=True)
        else:
            if overlapping:
                cmd = [
                    binary,
                    infile,
                    "out/",
                    "-N " + str(iterations),
                    "--overlapping",
                ] + seed_args
                subprocess.run(cmd, check=True)
            else:
                cmd = [binary, infile, "out/", "-N " + str(iterations)] + seed_args
                subprocess.run(cmd, check=True)
    else:
        if multiplex:
            cmd = [
                binary,
                infile,
                "out/",
                "-i multiplex",
                "-N " + str(iterations),
                "--silent",
            ] + seed_args
            subprocess.run(cmd, check=True)
        else:
            if overlapping:
                cmd = [
                    binary,
                    infile,
                    "out/",
                    "-N " + str(iterations),
                    "--overlapping",
                    "--silent",
                ] + seed_args
                subprocess.run(cmd, check=True)
            else:
                cmd = [
                    binary,
                    infile,
                    "out/",
                    "-N " + str(iterations),
                    "--silent",
                ] + seed_args
                subprocess.run(cmd, check=True)


def infomap_communities(
    graph: nx.Graph,
    binary: str = "./infomap",
    edgelist_file: str = "./tmp/tmpedgelist.txt",
    multiplex: bool = False,
    verbose: bool = False,
    overlapping: bool = False,
    iterations: int = 200,
    output: str = "mapping",
    seed: int = None,
) -> Union[Dict[Any, int], Dict[Any, List[int]]]:
    """
    Detect communities using the Infomap algorithm.

    Args:
        graph: Input graph (NetworkX graph or multi_layer_network)
        binary: Path to Infomap binary (default: "./infomap")
        edgelist_file: Temporary file for edgelist (default: "./tmp/tmpedgelist.txt")
        multiplex: Whether to use multiplex mode (default: False)
        verbose: Whether to show verbose output (default: False)
        overlapping: Whether to detect overlapping communities (default: False)
        iterations: Number of iterations (default: 200)
        output: Output format - "mapping" or "partition" (default: "mapping")
        seed: Random seed for reproducibility (default: None)
            Note: Requires Infomap binary that supports --seed parameter

    Returns:
        Dict mapping nodes to community IDs (if output="mapping")
        or Dict mapping community IDs to lists of nodes (if output="partition")

    Raises:
        FileNotFoundError: If Infomap binary is not found
        PermissionError: If Infomap binary is not executable

    Examples:
        >>> # Using with seed for reproducibility
        >>> partition = infomap_communities(graph, seed=42)
        >>>
        >>> # Get partition format instead of mapping
        >>> communities = infomap_communities(graph, output="partition")
    """

    # check type of the network
    print("INFO: Infomap community detection in progress..")

    # Ensure tmp directory exists for edgelist file
    import os

    edgelist_dir = os.path.dirname(edgelist_file)
    if edgelist_dir:
        os.makedirs(edgelist_dir, exist_ok=True)

    # go through individual nodes first and enumerate them., also layers
    inverse_node_map = graph.serialize_to_edgelist(
        edgelist_file=edgelist_file, multiplex=multiplex
    )
    # run infomap
    run_infomap(
        edgelist_file,
        multiplex=multiplex,
        binary=binary,
        verbose=verbose,
        overlapping=overlapping,
        iterations=iterations,
        seed=seed,
    )

    # Construct the expected output path based on input filename
    # Infomap typically writes to: <output_dir>/<input_basename>.tree
    input_basename = os.path.splitext(os.path.basename(edgelist_file))[0]
    output_tree_path = os.path.join("out", input_basename + ".tree")

    # Verify the output file exists before parsing
    if not os.path.exists(output_tree_path):
        # Try to find any .tree file in the output directory
        import glob
        tree_files = glob.glob("out/*.tree")
        if tree_files:
            output_tree_path = tree_files[0]
            if verbose:
                print(f"INFO: Using tree file: {output_tree_path}")
        else:
            raise Py3plexIOError(
                f"Infomap output file not found at expected path: {output_tree_path}. "
                f"The Infomap binary may have failed or written output to a different location. "
                f"Please check the 'out/' directory for .tree files."
            )

    partition = parse_infomap(output_tree_path)
    partition = {inverse_node_map[k]: v for k, v in partition.items()}
    non_mapped = set(graph.get_nodes()).difference(partition.keys())

    for x in non_mapped:
        partition[x] = 1

    import shutil

    shutil.rmtree("out", ignore_errors=False, onerror=None)
    shutil.rmtree("tmp", ignore_errors=False, onerror=None)

    if output == "mapping":
        return partition
    else:
        dx_hc = defaultdict(list)
        for a, b in partition.items():
            dx_hc[b].append(a)
        return dx_hc

    return partition


def parse_infomap(outfile):

    outmap = {}
    with open(outfile) as of:
        for line in of:
            parts = line.strip().split()
            try:
                module = parts[0].split(":")[0]
                node = parts[3]
                outmap[int(node)] = int(module)
            except (IndexError, ValueError, AttributeError):
                pass

    return outmap


def louvain_communities(network, output="mapping"):

    try:
        G = nx.Graph()
        for edge in network.core_network.edges():
            G.add_edge(edge[0], edge[1])
        network = G

    except Exception:
        pass  ## nx input directly.

    partition = best_partition(network)
    if output == "partition":
        dx_hc = defaultdict(list)
        for a, b in partition.items():
            dx_hc[b].append(a)
        return dx_hc
    return partition


def NoRC_communities(
    network,
    verbose=True,
    clustering_scheme="kmeans",
    output="mapping",
    prob_threshold=0.001,
    parallel_step=8,
    community_range=None,
    fine_range=3,
):

    if community_range is None:
        community_range = [1, 3, 5, 7, 11, 20, 40, 50, 100, 200, 300]
    try:
        network = network.core_network
    except AttributeError:
        pass

    partition = NoRC_communities_main(
        network,
        verbose=True,
        clustering_scheme=clustering_scheme,
        prob_threshold=prob_threshold,
        parallel_step=parallel_step,
        community_range=community_range,
        fine_range=fine_range,
    )

    if output == "mapping":
        return None
    else:
        return partition
