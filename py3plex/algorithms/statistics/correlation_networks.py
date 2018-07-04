## implement scale free network estimation
## do this according to the paper WCGA

import numpy as np
from collections import Counter
from scipy import stats

def pick_threshold(matrix):
    current_r_opt = 0
    rho, pval = stats.spearmanr(matrix)
    for j in np.linspace(0,1,50):
        tmp_array = rho.copy()
        tmp_array[tmp_array > j] = 1
        tmp_array[tmp_array < j] = 0
        np.fill_diagonal(tmp_array, 0) ## self loops
        rw_sum = np.sum(tmp_array,axis=0)
        counts = Counter(rw_sum)
        key_counts = np.log(list(counts.keys()))
        counts = np.log(list(counts.values()))
        slope, intercept, r_value, p_value, std_err = stats.linregress(key_counts,counts)
        if r_value > current_r_opt:
            print("Updating R^2: {}".format(r_value))
            current_r_opt = r_value
        if r_value > 0.80:
            return j        
    return current_r_opt

def default_correlation_to_network(matrix,input_type="matrix",preprocess="standard"):
    if preprocess == "standard":
        matrix = (matrix - np.mean(matrix, axis=0)) / np.std(matrix, axis=0)
    
    optimal_threshold = pick_threshold(matrix)
    print("Rsq threshold {}".format(optimal_threshold))
    matrix[matrix > optimal_threshold] = 1
    matrix[matrix < optimal_threshold] = 0
    return matrix

if __name__ == "__main__":
    from numpy import genfromtxt
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename",default="/home/skblaz/Downloads/expression.tsv")
    args = parser.parse_args()
    datta = args.filename
    a = genfromtxt(datta, delimiter='\t',skip_header=4)
    a = np.nan_to_num(a)
    print("Read the data..")
#    idx = np.random.randint(1000,size=5000)
#    a = a[:,idx]
    print(default_correlation_to_network(a).shape)
