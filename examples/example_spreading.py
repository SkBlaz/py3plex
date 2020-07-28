## simple spreading process on multilayers

from py3plex.core import multinet
from py3plex.core import random_generators
import numpy as np
import queue
import matplotlib.pyplot as plt
import seaborn as sns

## some random graph
ER_multilayer = random_generators.random_multilayer_ER(5000,
                                                       15,
                                                       0.05,
                                                       directed=False)

## seed node
all_nodes = list(ER_multilayer.get_nodes())
all_nodes_indexed = {x: en for en, x in enumerate(all_nodes)}

## spread from a random node

for j in range(5):
    random_init = np.random.randint(len(all_nodes))
    random_node = all_nodes[random_init]
    spread_vector = np.zeros(len(ER_multilayer.core_network))
    Q = queue.Queue(maxsize=300000)
    Q.put(random_node)
    layer_visit_sequence = []
    node_visit_sequence = []
    iterations = 0
    while True:
        if not Q.empty():
            candidate = Q.get()
            iterations += 1
            if iterations % 100 == 0:
                print("Iterations: {}".format(iterations))
            for neighbor in ER_multilayer.get_neighbors(
                    candidate[0], candidate[1]):
                idx = all_nodes_indexed[neighbor]
                if spread_vector[idx] != 1:
                    layer_visit_sequence.append(candidate[1])
                    node_visit_sequence.append((neighbor, iterations))
                    Q.put(neighbor)
                    spread_vector[idx] = 1
        else:
            break

    sns.distplot(layer_visit_sequence,
                 bins=10,
                 kde=True,
                 label="Walker {}".format(j + 1),
                 hist_kws={
                     "linewidth": 3,
                     "alpha": 0.2
                 })
plt.xlabel("Layer")
plt.ylabel("Visit density")
plt.xlim(0, 14)
plt.legend()
plt.show()
