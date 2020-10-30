# high level interface for community detection algorithms
from .community_louvain import *
try:
    from .NoRC import *
except:
    pass


def run_infomap(infile,
                multiplex=True,
                overlapping=False,
                binary="./infomap",
                verbose=True,
                iterations=1000):

    from subprocess import call
    if verbose:
        if multiplex:
            call([
                binary, infile, "out/", "-i multiplex",
                "-N " + str(iterations), "-z"
            ])
        else:
            if overlapping == True:
                call([
                    binary, infile, "out/", "-N " + str(iterations),
                    "--overlapping", "-z"
                ])
            else:
                call([binary, infile, "out/", "-N " + str(iterations), "-z"])
    else:
        if multiplex:
            call([
                binary, infile, "out/", "-i multiplex",
                "-N " + str(iterations), "-z", "--silent"
            ])
        else:
            if overlapping == True:
                call([
                    binary, infile, "out/", "-N " + str(iterations),
                    "--overlapping", "-z", "--silent"
                ])
            else:
                call([
                    binary, infile, "out/", "-N " + str(iterations), "-z",
                    "--silent"
                ])


def infomap_communities(graph,
                        binary="./infomap",
                        edgelist_file="./tmp/tmpedgelist.txt",
                        multiplex=False,
                        verbose=False,
                        overlapping=False,
                        iterations=200,
                        output="mapping"):

    # check type of the network
    print("INFO: Infomap community detection in progress..")

    # go through individual nodes first and enumerate them., also layers
    inverse_node_map = graph.serialize_to_edgelist(edgelist_file=edgelist_file,
                                                   multiplex=multiplex)
    # run infomap
    run_infomap(edgelist_file,
                multiplex=multiplex,
                binary=binary,
                verbose=verbose,
                overlapping=overlapping,
                iterations=iterations)

    partition = parse_infomap("out/" +
                              edgelist_file.split("/")[-1].split(".")[0] +
                              ".tree")
    partition = {inverse_node_map[k]: v for k, v in partition.items()}
    non_mapped = set(list(graph.get_nodes())).difference(partition.keys())

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
            except:
                pass

    return outmap


def louvain_communities(network, output="mapping"):

    try:
        G = nx.Graph()
        for edge in network.core_network.edges():
            G.add_edge(edge[0], edge[1])
        network = G

    except Exception as es:
        print(es)

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
        community_range=[1, 3, 5, 7, 11, 20, 40, 50, 100, 200, 300],
        fine_range=3):

    try:
        network = network.core_network
    except:
        pass

    partition = NoRC_communities_main(network,
                                      verbose=True,
                                      clustering_scheme=clustering_scheme,
                                      prob_threshold=prob_threshold,
                                      parallel_step=parallel_step,
                                      community_range=community_range,
                                      fine_range=fine_range)

    if output == "mapping":
        # todo
        return None
    else:
        return partition
