## visualize benchmarks

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
sns.set_style("whitegrid")

palette="Set3"
cnames = ["percent_train","micro_F","macro_F","setting","dataset","time"]


def plot_core_macro(fname):

    """
    A very simple visualization of the results..
    """
    p1 = sns.pointplot('percent_train','macro_F',hue='setting', data=fname,markers=["p"]*10,ci="sd",linestyles=['-', '--', '-.', ':']*5)
    plt.show()
    
    return 1

def plot_core_micro(fname):

    """
    A very simple visualization of the results..
    """
    p1 = sns.lineplot('percent_train','micro_F',hue='setting', data=fname)
    plt.show()
    
    return 1
