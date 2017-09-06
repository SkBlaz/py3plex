## this algorithm decomposes time-series into residuals, upon which anomalies are detected!


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from PyAstronomy import pyasl
#from statsmodels.tsa.seasonal import seasonal_decompose

sns.set_style("white")
pdfrm = pd.read_csv("anomaly_dataset.csv")

plt.figure(1)
count = 0

otls = {}

otls_vals = []

for name, df in pdfrm.groupby('layer'):

    ts = pd.Series(df['count'])
    r = pyasl.generalizedESD(ts, 10, 0.05, fullOutput=True)

    ## remember outliers
    print("Outliers",r[0],name)
    otls[name]= r[1]

    if name != "RE":
        otls_vals.append(set(r[1]))

real_outlier = set.intersection(*otls_vals)
print("real_outlier:",real_outlier)

plt.figure(1)
count = 0
ccols = ["red","green","blue","red"]
for name,datax in pdfrm.groupby('layer'):

    outliers = otls[name]
    outdf = datax.iloc[outliers]    
    count +=1
    plt.subplot("31"+str(count))
    if count == 2:
        plt.ylabel("Number of triangles",labelpad=20)
    plt.plot(datax["time"],datax["count"],label=name,color="black")
    plt.plot(outdf['time'],outdf['count'],'ro',color="red",label="outliers")
    
    plt.legend()
    
plt.xlabel("Time")
plt.show()
