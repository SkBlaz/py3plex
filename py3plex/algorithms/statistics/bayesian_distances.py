## tutorial

import argparse
import bayesiantests as bt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from collections import defaultdict

def generate_bayesian_diagram(result_matrices,algo_names = ["algo1","algo2"],rope=0.01,rho=1/5,show_diagram=True,save_diagram=None):

    #rope=0.01 #we consider two classifers equivalent when the difference of accuracy is less that 1%
    print(rope,rho)
    #rho=1/5 #we are performing 10 folds, 10 runs cross-validation
    pl, pe, pr=bt.hierarchical(result_matrices,rope,rho, verbose=True, names=algo_names)
    samples=bt.hierarchical_MC(result_matrices,rope,rho, names=algo_names)

    #plt.rcParams['figure.facecolor'] = 'black'
    fig = bt.plot_posterior(samples,algo_names)
    
    if show_diagram:
        plt.show()
        
    if save_diagram is not None:
        plt.savefig(save_diagram)
    return (pl,pe,pr)

