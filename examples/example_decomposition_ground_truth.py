# decomposition with ground truth

from py3plex.core import multinet
#from sklearn.model_selection import StratifiedShuffleSplit

dataset = "../datasets/imdb.gpickle"

multilayer_network = multinet.multi_layer_network().load_network(
    input_file=dataset, directed=True, input_type=dataset.split(".")[-1])

print("Running optimization for {}".format(dataset))
multilayer_network.basic_stats()  # check core imports
triplet_set = list(set(multilayer_network.get_decomposition_cycles()))
print("\n".join(triplet_set))
for decomposition in multilayer_network.get_decomposition(
        heuristic=["idf", "tf", "chi", "ig", "gr", "delta", "rf", "okapi"],
        cycle=triplet_set):
    print(decomposition)
