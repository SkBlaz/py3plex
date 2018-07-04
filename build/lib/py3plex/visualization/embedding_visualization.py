
## embedding
from sklearn.manifold import TSNE
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from plotnine import *

def visualize_embedding (multinet,labels=None):
    embedding = multinet.embedding
    X = embedding[0]
    indices = embedding[1]

    if labels:    
        ## optionally match indices to labels and add a column
        pass
    else:
        X_embedded = TSNE(n_components=2).fit_transform(X)
        dfr = pd.DataFrame(X_embedded,columns=['dim1','dim2'])
        print(dfr.head())
        gx = (ggplot(dfr, aes('dim1', 'dim2'))
              + geom_point(size=0.5)+ theme_bw()
        )
        gx.draw()
        plt.show()
