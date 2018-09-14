## set of routines for validation of the PPR-based classification

from ..node_ranking import *
from ..general.benchmark_classification import *
import pandas as pd
import time
import numpy as np
import multiprocessing as mp
from sklearn.model_selection import ShuffleSplit

def construct_PPR_matrix(graph_matrix,parallel=False):

    """
    PPR matrix is the matrix of features used for classification --- this is the spatially intense version of the classifier
    """
    
    ## initialize the vectors
    n = graph_matrix.shape[1]
    vectors = np.zeros((n, n))
        
    results = run_PPR(graph_matrix,parallel=parallel)
    
    ## get the results in batches
    for result in results:
        if result != None:
            ## individual batches
            for ppr in result:
                vectors[ppr[0],:] = ppr[1]            
    return vectors

def construct_PPR_matrix_targets(graph_matrix,targets,parallel=False):

    n = graph_matrix.shape[1]
    vectors = np.empty((len(targets), n))
    tar_map = dict(zip(targets,range(len(targets))))
    results = run_PPR(graph_matrix,targets=targets,parallel=parallel)
    for result in results:
        vectors[tar_map[result[0]],:] = vectors[1]
            
    return vectors
    ## deal with that now..

def validate_ppr(core_network,labels,dataset_name="test",repetitions=5,random_seed=123,multiclass_classifier=None,target_nodes=None,parallel=False):
    """
    The main validation class --- use this to obtain CV results!
    """
    df = pd.DataFrame()
    for k in range(repetitions):

        ## this is relevant for supra-adjacency-based tasks..
        if target_nodes is not None:
            print("Subnetwork ranking in progress..")
            vectors = construct_PPR_matrix_targets(core_network,target_nodes,parallel=parallel)
            labels = labels[target_nodes]
            
        else:            
            vectors = construct_PPR_matrix(core_network,parallel=parallel)            
        
        for j in np.arange(0.1,1,0.1):

            ## run the training..
            print("Train size:{}, method {}".format(j,"PPR"))
            print(vectors.shape,labels.shape)
            rs = ShuffleSplit(n_splits=10, test_size=j, random_state=random_seed)
            micros = []
            macros = []
            times = []
            for X_train, X_test in rs.split(labels):
                start = time.time()
                train_x = vectors[X_train]
                test_x = vectors[X_test]
                train_labels = labels[X_train]
                test_labels = labels[X_test]
                
                clf = multiclass_classifier
                clf.fit(train_x, train_labels)
                mi,ma = evaluate_oracle_F1(clf,test_x,test_labels,input_proba=False)

                ## train the model
                end = time.time()
                elapsed = end - start
                micros.append(mi)
                macros.append(ma)
                times.append(elapsed)
            outarray = {"percent_train": np.round(1-j,1), "micro_F":np.mean(micros),"macro_F":np.mean(macros) ,"setting": "PPR" ,"dataset": dataset_name,"time":np.mean(times)}
            df = df.append(outarray,ignore_index=True)
            
    df = df.reset_index()
    return df
        
