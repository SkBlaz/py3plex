## tutorial

import argparse
import bayesiantests as bt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from collections import defaultdict

cnames = ["percent_train","micro_F","macro_F","setting","dataset","time"]

## this loads a single results file with respect to certain algorithm
# def read_results_file(filename,algorithm_of_interest="node2vec"):
#     fnamex = pd.read_csv(filename,sep=" ")
#     fnamex.columns = cnames
#     fnamex['dataset'] = fnamex['dataset'].replace({'../matrix_data/multi_class/Blogspot.mat': 'Blogspot',
#                                                    '../matrix_data/multi_class/Bitcoin.mat': 'Bitcoin',
#                                                    '../matrix_data/multi_class/Bitcoin_alpha.mat': 'Bitcoin Alpha',
#                                                    '../matrix_data/multi_class/Homo_sapiens.mat': 'Homo Sapiens PPI',
#                                                    '../matrix_data/multi_class/POS.mat': 'Wiki',
#                                                    '../matrix_data/multi_class/ions.mat': 'Ions',
#                                                    '../matrix_data/multi_class/cora.mat': 'Cora',
#                                                    '../matrix_data/multi_class/citeseer.mat': 'CiteSeer'})
    
#     fnamex.setting = fnamex.setting.replace({"default0" : "DNR (1)",
#                                              "no_deep_no_community" : "PPR",
#                                              "default1" :"DNR (2)",
#                                              "default2" :"DNR (3)",
#                                              "DNR_e2e0PR" : "DNR-e2e (1)",
#                                              "DNR_e2e1PR" : "DNR-e2e (2)",
#                                              "DNR_e2e2PR" : "DNR-e2e (3)",
#                                              "DNR_e2e0LAPLACIAN" : "L-DNR-e2e (1)",
#                                              "DNR_e2e1LAPLACIAN" : "L-DNR-e2e (2)",
#                                              "DNR_e2e2LAPLACIAN" : "L-DNR-e2e (3)",
#                                              "N2V" : "Node2vec",
#                                              "RAW2" : "HINMINE",
#                                              "PCA2" : "HINMINE-PCA",
#                                              "LP_basic" : "LP"})

#     fnamex = fnamex[fnamex['setting'] == algorithm_of_interest]

#     return fnamex


## load all files

def generate_bayesian_diagram(result_matrices,algo_names = ["Node2vec","DNR-e2e (1)"],score_of_interest="micro_F",rope=0.01,rho=1/5):

    algo_data = {}
    
    ## input folders
    algo_names = algo_names
    df_extracted = []
    score_of_interest = score_of_interest
    unique_datasets = set()

    #rope=0.01 #we consider two classifers equivalent when the difference of accuracy is less that 1%
    #rho=1/5 #we are performing 10 folds, 10 runs cross-validation
    pl, pe, pr=bt.hierarchical(result_matrices,rope,rho, verbose=True, names=algo_names)
    samples=bt.hierarchical_MC(result_matrices,rope,rho, names=algo_names)

    #plt.rcParams['figure.facecolor'] = 'black'
    fig = bt.plot_posterior(samples,algo_names)

    return (pl,pe,pr)
#    plt.savefig('triangle_hierarchical.png',facecolor="black")
#    plt.show()
