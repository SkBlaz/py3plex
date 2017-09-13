## this algorithm decomposes time-series into residuals, upon which anomalies are detected!


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import itertools
from PyAstronomy import pyasl

sns.set_style("white")
pdfrm = pd.read_csv("anomaly_dataset.csv")
pdfrm_copy = pdfrm
plt.figure(1)


otls = {}
otls_vals = []

## to zavij v funkcijo, ki iterira do max stevila outlierjev.

threshold = 5
it = 2

while True:
    for name, df in pdfrm.groupby('layer'):
        ts = pd.Series(df['count'])
        r = pyasl.generalizedESD(ts, it, 0.05, fullOutput=True)

        ## remember outliers
        otls[name]= r[1]
        otls_times = df.iloc[r[1]]['time']
        otls_vals.append(set(otls_times))

    real_outlier = []        
    for j in range(2,len(otls_vals)+1):
        ilist = list(itertools.combinations(otls_vals,j))
        for ex in ilist:
            intersection = set.intersection(*ex)
            if len(intersection) != 0:
                real_outlier.append(intersection)

    if len(real_outlier) > threshold:        
        break
    it+=1


count = 0
for name,datax in pdfrm_copy.groupby('layer'):

    time_outliers = []
    for j in real_outlier:
        for x in j:
            time_outliers.append(x)
            
#    outliers = otls[name]
    outdf = datax[datax['time'].isin(time_outliers)]
#    outdf = datax.iloc[outliers]
    count +=1
    plt.subplot("31"+str(count))
    if count == 2:
        plt.ylabel("Number of triangles",labelpad=20)
    plt.plot(datax["time"],datax["count"],label=name,color="black")
    plt.plot(outdf['time'],outdf['count'],'ro',color="red",label="outliers")
    
    plt.legend()
    
plt.xlabel("Time")
plt.show()
