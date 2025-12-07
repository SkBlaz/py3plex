# embedding
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.manifold import TSNE


def visualize_embedding(multinet, labels=None, verbose=True):
    embedding = multinet.embedding
    X = embedding[0]
    indices = embedding[1]
    
    # Convert np.matrix to np.array for compatibility with sklearn
    if isinstance(X, np.matrix):
        X = np.asarray(X)

    if verbose:
        print("------ Starting embedding visualization -------")

    if labels:
        # optionally match indices to labels and add a column
        label_vector = [labels[x] for x in indices]
        X_embedded = TSNE(n_components=2).fit_transform(X)
        dfr = pd.DataFrame(X_embedded, columns=["dim1", "dim2"])
        dfr["labels"] = label_vector
        print(dfr.head())

        # Create scatter plot with matplotlib
        plt.figure(figsize=(8, 6))
        for label in dfr["labels"].unique():
            mask = dfr["labels"] == label
            plt.scatter(
                dfr.loc[mask, "dim1"],
                dfr.loc[mask, "dim2"],
                label=label,
                s=20,
                alpha=0.7,
            )
        plt.xlabel("dim1")
        plt.ylabel("dim2")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    else:
        X_embedded = TSNE(n_components=2).fit_transform(X)
        dfr = pd.DataFrame(X_embedded, columns=["dim1", "dim2"])
        print(dfr.head())

        # Create scatter plot with matplotlib
        plt.figure(figsize=(8, 6))
        plt.scatter(dfr["dim1"], dfr["dim2"], s=20, alpha=0.7)
        plt.xlabel("dim1")
        plt.ylabel("dim2")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
