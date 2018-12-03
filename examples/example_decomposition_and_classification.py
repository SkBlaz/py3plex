## first decompose, then classify!



from py3plex.core import multinet

## a simple decomposition example. Note that target nodes need to have "labels" property, to which labels are assigned in class1---class2---...and so on...

dataset = "../datasets/imdb.gpickle"

multilayer_network = multinet.multi_layer_network().load_network(input_file=dataset,directed=True,input_type=dataset.split(".")[-1])

print ("Running optimization for {}".format(dataset))
multilayer_network.basic_stats() ## check core imports        
triplet_set = list(set(multilayer_network.get_decomposition_cycles()))
print(triplet_set)
for decomposition in multilayer_network.get_decomposition(heuristic=["idf","rf"], cycle=triplet_set, parallel=True):
    print(decomposition[0])



validation_results = validate_ppr(multilayer_network.core_network,multilayer_network.labels,multiclass_classifier=model,repetitions=2)

## plot the results
plot_core_macro(validation_results)
