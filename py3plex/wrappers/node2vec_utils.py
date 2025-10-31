"""Shared utilities for Node2Vec embedding wrappers."""

import os
from subprocess import call
from typing import List

from ..logging_config import get_logger

logger = get_logger(__name__)


def call_node2vec_binary(
    input_graph: str,
    output_graph: str,
    p: float = 1,
    q: float = 1,
    dimension: int = 128,
    directed: bool = False,
    weighted: bool = True,
    binary: str = "./node2vec",
) -> None:
    """
    Call the node2vec binary to generate embeddings.

    Args:
        input_graph: Path to input graph file
        output_graph: Path to output embedding file
        p: Return parameter (default: 1)
        q: In-out parameter (default: 1)
        dimension: Embedding dimension (default: 128)
        directed: Whether graph is directed (default: False)
        weighted: Whether graph is weighted (default: True)
        binary: Path to node2vec binary (default: "./node2vec")

    Raises:
        FileNotFoundError: If binary does not exist
        PermissionError: If binary is not executable
    """
    # Check if binary exists and is executable
    if not os.path.exists(binary):
        raise FileNotFoundError(
            f"Node2Vec binary not found at '{binary}'. "
            "Please provide a valid path to the Node2Vec binary, "
            "or consider using pure Python alternatives like 'node2vec' or 'pecanpy' packages: "
            "pip install node2vec"
        )

    if not os.access(binary, os.X_OK):
        raise PermissionError(
            f"Node2Vec binary at '{binary}' is not executable. "
            f"Run: chmod +x {binary}"
        )

    input_params: List[str] = []
    input_params.append(binary)
    input_params.append("-i:" + input_graph)
    input_params.append("-o:" + output_graph)
    input_params.append("-d:" + str(dimension))
    input_params.append("-p:" + str(p))
    input_params.append("-q:" + str(q))
    input_params.append("-v")
    
    if directed:
        input_params.append("-d")
    if weighted:
        input_params.append("-w")
    
    logger.info("Node2vec parameters: %s", " ".join(input_params))
    call(input_params)
    call(["rm", "-rf", "tmp/*"])
