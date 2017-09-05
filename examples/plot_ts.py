## this example plots anomaly_dataset.csv

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_style("white")
pdfrm = pd.read_csv("anomaly_dataset.csv")

plt.figure(1)
count = 0
ccols = ["red","green","blue","red"]
for name,datax in pdfrm.groupby('layer'):
    count +=1
    plt.subplot("31"+str(count))
    if count == 2:
        plt.ylabel("Number of triangles",labelpad=20)
    plt.plot(datax["time"],datax["count"],label=name,color="black")
    plt.legend()
plt.xlabel("Time")
plt.show()

#fig, (ax1, ax2) = plt.subplots(nrows = 2, ncols = 1)
