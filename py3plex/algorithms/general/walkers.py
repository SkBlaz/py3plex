## different random walk implementations
import networkx as nx
import numpy as np
import random
import itertools


def __random_number_set_generator(number):
    choices = np.random.rand(number)
    for x in choices:
        yield x


def general_random_walk(G, start_node, iterations=1000, teleportation_prob=0):

    ## possibly create the transition bias, based on one of many possible approaches.
    ## mean_degree = np.mean([y for x,y in G.degree()])

    random_number_generator = __random_number_set_generator(int(1e6))
    x = 0
    trace = []

    while x < iterations:
        neighbors = list(G.neighbors(start_node))
        num_neighbors = len(neighbors)
        probabilities = np.array(
            list(itertools.islice(random_number_generator, num_neighbors + 1)))
        teleport = probabilities[-1]
        if teleport > (1 - teleportation_prob):
            probabilities = np.array(
                list(itertools.islice(random_number_generator, len(trace))))
            ind = np.unravel_index(np.argmax(probabilities, axis=None),
                                   probabilities.shape)
            new_pivot = trace[ind[0]]
            start_node = new_pivot
            continue
        probabilities = probabilities[0:num_neighbors]
        ind = np.unravel_index(np.argmax(probabilities, axis=None),
                               probabilities.shape)
        new_pivot = neighbors[ind[0]]
        trace.append(new_pivot)
        start_node = new_pivot
        x += 1

    return trace


def layer_specific_random_walk(G, start_node, iterations=1000):

    ## get the node's layer and walk there + cout possible exits

    pass


if __name__ == "__main__":

    graph = nx.erdos_renyi_graph(1000, 0.01)
    print(nx.info(graph))

    trace = general_random_walk(graph, 5)
    print(trace)
