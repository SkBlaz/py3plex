## entanglement: By. Benjamin Renoust and Blaz Skrlj, 2019
## load an example multilayer network

from py3plex.core import multinet
from py3plex.algorithms.multilayer_algorithms.entanglement import *

## visualization from a simple file
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/multiL.txt", directed=True, input_type="multiedgelist")
multilayer_network.basic_stats()

analysis = compute_entanglement_analysis(multilayer_network)

print("%d connected components of layers" % len(analysis))
for i, b in enumerate(analysis):
    print('--- block %d' % i)
    layer_labels = b['Layer entanglement'].keys()
    print('Covering layers: %s' % layer_labels)

    print('Entanglement intensity: %f' % b['Entanglement intensity'])
    print('Layer entanglement: %s' % b['Layer entanglement'])
    print('Entanglement homogeneity: %f' % b['Entanglement homogeneity'])
    print('Normalized homogeneity: %f' % b['Normalized homogeneity'])
