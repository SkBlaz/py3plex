## core IO operations

from .dataStructures import HeterogeneousInformationNetwork
import numpy as np


def load_hinmine_object(infile,
                        label_delimiter="---",
                        weight_tag=False,
                        targets=True):

    ## load the network to the HINMINE framework (Kralj et al. 2018)
    net = infile
    hin = HeterogeneousInformationNetwork(net,
                                          label_delimiter,
                                          weight_tag,
                                          target_tag=targets)
    train_indices = []
    test_indices = []
    for index, node in enumerate(hin.node_list):
        if len(hin.graph.node[node]['labels']) > 0:
            train_indices.append(index)
        else:
            test_indices.append(index)
    hin.split_to_indices(train_indices=train_indices,
                         test_indices=test_indices)
    if targets:
        hin.create_label_matrix()
    return hin
