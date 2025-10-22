# wrapper for the C++ version of the Node2Vec algorithm
import ast
import multiprocessing as mp
import os
import time
from subprocess import call
from typing import Any, Dict, List, Optional, Tuple

from sklearn import linear_model
from sklearn.multiclass import OneVsRestClassifier

from py3plex.core.nx_compat import nx_info

from ..logging_config import get_logger
from .benchmark_nodes import benchmark_node_classification

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
    Call the Node2Vec C++ binary with specified parameters.
    
    Args:
        input_graph: Path to input graph file
        output_graph: Path to output embedding file
        p: Return parameter
        q: In-out parameter
        dimension: Embedding dimension
        directed: Whether graph is directed
        weighted: Whether graph is weighted
        binary: Path to node2vec binary
    """
    input_params: List[str] = []
    input_params.append(binary)
    input_params.append("-i:" + input_graph)
    input_params.append("-o:" + output_graph)
    input_params.append("-d:" + str(dimension))
    input_params.append("-p:" + str(p))
    input_params.append("-q:" + str(q))
    input_params.append("-v")
    logger.info("Node2vec parameters: %s", " ".join(input_params))
    if directed:
        input_params.append("-d")
    if weighted:
        input_params.append("-w")
    call(input_params)


def n2v_embedding(
    G: Any,
    targets: Any,
    verbose: bool = False,
    sample_size: float = 0.5,
    outfile_name: str = "test.emb",
    p: float = -100,
    q: float = -100,
    binary_path: str = "./node2vec",
    parameter_range: Optional[List[float]] = None,
    embedding_dimension: int = 128,
) -> None:
    """
    Train Node2Vec embeddings with parameter optimization.
    
    Args:
        G: NetworkX graph
        targets: Target labels for nodes
        verbose: Whether to print verbose output
        sample_size: Sample size for training
        outfile_name: Output embedding file name
        p: Return parameter (negative value triggers grid search)
        q: In-out parameter (negative value triggers grid search)
        binary_path: Path to node2vec binary
        parameter_range: Range of parameters to search
        embedding_dimension: Dimension of embeddings
    """

    # construct the embedding and return the binary..
    # ./node2vec -i:graph/karate.edgelist -o:emb/karate.emb -l:3 -d:24 -p:0.3 -dr -v

    if parameter_range is None:
        parameter_range = [0.25, 0.5, 1, 2, 4]
    OneVsRestClassifier(linear_model.LogisticRegression(), n_jobs=mp.cpu_count())
    if verbose:
        logger.info("Graph info:\n%s", nx_info(G))

    len(G.nodes())

    # get the graph..
    if not os.path.exists("tmp"):
        os.makedirs("tmp")

    tmp_graph = "tmp/tmpgraph.edges"

    number_of_nodes = len(G.nodes())
    number_of_edges = len(G.edges())

    if verbose:
        logger.info(
            "Graph has %d edges and %d nodes.", number_of_edges, number_of_nodes
        )

    f = open(tmp_graph, "w+")

    # f.write(str(number_of_nodes)+" "+str(number_of_edges)+"\n")
    for e in G.edges(data=True):
        f.write(str(e[0]) + " " + str(e[1]) + " " + str(float(e[2]["weight"])) + "\n")
    f.close()

    if verbose:
        logger.info("N2V training phase..")

    vals = parameter_range
    copt = 0
    cset: List[float] = [0.0, 0.0]

    if float(p) > -100 and float(q) > -100:
        logger.info("Running specific config of N2V.")
        call_node2vec_binary(
            tmp_graph, outfile_name, p=p, q=q, directed=False, weighted=True
        )

    else:

        # commence the grid search
        for x in vals:
            for y in vals:
                call_node2vec_binary(
                    tmp_graph,
                    outfile_name,
                    p=x,
                    q=y,
                    directed=False,
                    weighted=True,
                    binary=binary_path,
                )
                logger.debug("Parsing %s", outfile_name)
                rdict = benchmark_node_classification(
                    outfile_name, G, targets, percent=float(sample_size)
                )

                mi, ma, misd, masd = rdict[float(sample_size)]
                if ma > copt:
                    if verbose:
                        logger.info("Updating the parameters: %s %s", ma, cset)

                    cset = [x, y]
                    copt = ma
                else:
                    logger.debug("Current optimum %s", ma)

                call(["rm", "-rf", outfile_name])  # when updatedin delete the file

        logger.info("Final iteration phase..")

        call_node2vec_binary(
            tmp_graph,
            outfile_name,
            p=cset[0],
            q=cset[1],
            directed=False,
            weighted=True,
            binary="./node2vec",
        )

        with open(outfile_name) as f:
            fl = f.readline()
            logger.info("Resulting dimensions: %s", fl)

        call(["rm", "-rf", "tmp"])


def learn_embedding(
    core_network: Any,
    labels: Optional[List[Any]] = None,
    ssize: float = 0.5,
    embedding_outfile: str = "out.emb",
    p: float = 0.1,
    q: float = 0.1,
    binary_path: str = "./node2vec",
    parameter_range: str = "[0.25,0.50,1,2,4]",
) -> Tuple[str, float]:
    """
    Learn node embeddings for a network.
    
    Args:
        core_network: NetworkX graph
        labels: Node labels
        ssize: Sample size
        embedding_outfile: Output file for embeddings
        p: Return parameter
        q: In-out parameter
        binary_path: Path to node2vec binary
        parameter_range: String representation of parameter range list
        
    Returns:
        Tuple of (method_name, elapsed_time)
    """
    if labels is None:
        labels = []
    start = time.time()
    parameter_range_list = ast.literal_eval(parameter_range)
    # Note: This function appears to be incomplete - self.method and self.vb are undefined
    # This seems to be a method that was extracted from a class but not properly refactored
    method = "default_n2v"  # Default value since self.method is not available
    verbose = True  # Default value since self.vb is not available
    
    if method == "default_n2v":
        n2v_embedding(
            core_network,
            targets=labels,
            sample_size=ssize,
            verbose=verbose,
            outfile_name=embedding_outfile,
            p=p,
            q=q,
            binary_path=binary_path,
            parameter_range=parameter_range_list,
        )
    end = time.time()
    elapsed = end - start
    return (method, elapsed)
