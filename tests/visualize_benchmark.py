

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

sns.set_style("white")
palette="Set3"
def load_results(df):

    loaded = pd.read_csv(df)
    return loaded

def node_dependent_performance(df):

    df2 = df[["N","Py3plex","Pymnet","p"]]
    df2 = pd.melt(df2, id_vars=['N','p'], value_vars=['Pymnet','Py3plex'])
    print(df2.head())
    df2 = df2.groupby(['p','N','variable']).mean().reset_index()
    print(df2.head())
    df2.columns = ["p","|N|","Library","time"]
    print(df2)
    
    # grid = sns.FacetGrid(df2, col="N", hue="variable", col_wrap=2)
    # grid.map(sns.swarmplot, "E", "value",marker="o").add_legend()


    sns.boxplot(x="|N|", y="time", data=df2,hue="Library",
                whis="range", palette="vlag")
 
    plt.show()
    
    pass

if __name__ == "__main__":

    df = load_results("example_benchmark.csv")
    node_dependent_performance(df)
    
    
    pass
