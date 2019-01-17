## tutorial

import argparse
import bayesiantests as bt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from collections import defaultdict

def generate_bayesian_diagram(result_matrices,algo_names = ["algo1","algo2"],score_of_interest="micro_F",rope=0.01,rho=1/5):

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
