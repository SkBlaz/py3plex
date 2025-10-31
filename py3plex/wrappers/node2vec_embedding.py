# wrapper for the C++ version of the Node2Vec algorithm
import ast
import multiprocessing as mp
import os
import time
from subprocess import call
from typing import Any, List, Optional

from sklearn import linear_model
from sklearn.multiclass import OneVsRestClassifier

from py3plex.core.nx_compat import nx_info

from ..logging_config import get_logger
from .benchmark_nodes import benchmark_node_classification
from .node2vec_utils import call_node2vec_binary

logger = get_logger(__name__)


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
) -> Any:
    """
    Generate node2vec embeddings and benchmark them.

    Args:
        G: NetworkX graph
        targets: Target labels for nodes
        verbose: Whether to print verbose output (default: False)
        sample_size: Sample size for training (default: 0.5)
        outfile_name: Output file name (default: "test.emb")
        p: Return parameter (default: -100, will be auto-tuned)
        q: In-out parameter (default: -100, will be auto-tuned)
        binary_path: Path to node2vec binary (default: "./node2vec")
        parameter_range: Range of parameters to try (optional)
        embedding_dimension: Dimension of embeddings (default: 128)

    Returns:
        Benchmark results
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

    with open(tmp_graph, "w+") as f:
        # f.write(str(number_of_nodes)+" "+str(number_of_edges)+"\n")
        for e in G.edges(data=True):
            f.write(str(e[0]) + " " + str(e[1]) + " " + str(float(e[2]["weight"])) + "\n")

    if verbose:
        logger.info("N2V training phase..")

    vals = parameter_range
    copt = 0
    cset = [0, 0]

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

                    cset = [int(x), int(y)]
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
) -> tuple:
    """
    Learn node embeddings using Node2Vec.

    Args:
        core_network: NetworkX graph
        labels: Optional node labels for evaluation
        ssize: Sample size for training
        embedding_outfile: Path to output embedding file
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
    n2v_embedding(
        core_network,
        targets=labels,
        sample_size=ssize,
        verbose=False,
        outfile_name=embedding_outfile,
        p=p,
        q=q,
        binary_path=binary_path,
        parameter_range=parameter_range_list,
    )
    end = time.time()
    elapsed = end - start
    return ("default_n2v", elapsed)
