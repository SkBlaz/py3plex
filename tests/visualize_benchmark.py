

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

sns.set_style('whitegrid')
def load_results(df):

    loaded = pd.read_csv(df)
    return loaded

def node_dependent_performance(df):

    print(df["E"])
    df2 = pd.melt(df, id_vars=['N','p','E'], value_vars=['Pymnet','Py3plex'])
    #df2 = df2.groupby(['E','variable','N']).mean().reset_index()
    
    print(df2)
    # grid = sns.FacetGrid(df2, col="N", hue="variable", col_wrap=2)
    # grid.map(sns.swarmplot, "E", "value",marker="o").add_legend()


    sns.boxplot(x="E", y="value", data=df2,hue="variable",
                whis="range", palette="vlag")
 
    plt.show()
    
    pass

if __name__ == "__main__":

    df = load_results("example_benchmark.csv")
    node_dependent_performance(df)
    
    
    pass
