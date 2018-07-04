
## embedding
from sklearn.manifold import TSNE
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def visualize_embedding (multinet,labels=None):
    from plotnine import *
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

def get_2d_coordinates_tsne(multinet,output_format="json",verbose=True):

    embedding = multinet.embedding
    X = embedding[0]
    indices = embedding[1]
    if verbose:
        multinet.monitor("Doing the TSNE reduction to 2 dimensions!")
    X_embedded = TSNE(n_components=2).fit_transform(X)
    dfr = pd.DataFrame(X_embedded,columns=['dim1','dim2'])
    dfr['node_names'] = [n for n in multinet.get_nodes()]
    dfr['node_codes'] = indices
    if output_format == "json":        
        ## export this as json
        return dfr.to_json(orient='records')
    
    elif output_format == "dataframe":
        ## pure pandas dataframe
        return dfr
    
    else:
        return None
