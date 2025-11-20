# visualize benchmarks

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ..logging_config import get_logger

logger = get_logger(__name__)

sns.set_style("whitegrid")

palette = "Set3"


def plot_core_macro(fname: pd.DataFrame) -> int:
    """
    A very simple visualization of the results..
    """
    sns.pointplot(
        "percent_train",
        "macro_F",
        hue="setting",
        data=fname,
        markers=["p"] * 10,
        ci="sd",
        linestyles=["-", "--", "-.", ":"] * 5,
    )
    plt.show()

    return 1


def plot_core_micro(fname: pd.DataFrame) -> int:
    """
    A very simple visualization of the results..
    """
    sns.lineplot("percent_train", "micro_F", hue="setting", data=fname)
    plt.show()

    return 1


palette = "Set3"
cnames = ["percent_train", "micro_F", "macro_F", "setting", "dataset", "time"]


def plot_core_macro_box(fname: str) -> int:

    fnamex = pd.read_csv(fname, sep=" ")
    logger.debug("DataFrame loaded:\n%s", fnamex)
    fnamex.columns = cnames
    logger.debug("DataFrame head:\n%s", fnamex.head())

    sns.boxplot("percent_train", "macro_F", hue="setting", data=fnamex)
    plt.show()
    return 1


def plot_core_micro_grid(fname: str) -> None:

    fnamex = pd.read_csv(fname, sep=" ")
    fnamex.columns = cnames
    grid = sns.FacetGrid(fnamex, col="dataset", hue="setting", col_wrap=2)
    grid.map(plt.plot, "percent_train", "micro_F", marker="o").add_legend()
    plt.show()


def plot_core_macro_gg(fnamex: pd.DataFrame) -> None:
    logger.debug("DataFrame columns: %s", fnamex.columns)
    fx = fnamex.groupby(["setting"])["macro_F"].mean().sort_values().index.values
    g = sns.FacetGrid(fnamex, col="dataset", hue="setting", col_wrap=3)
    g = g.map(
        plt.plot, "percent_train", "macro_F", marker="o", linewidth=1
    ).add_legend()
    g.set_xlabels("Train percentage (%)")
    g.set_ylabels("Average Macro F1")
    plt.show()

    sns.boxplot(x="setting", y="macro_F", data=fnamex, color="white", order=fx)
    plt.xticks(rotation=45)
    plt.xlabel("Algorithm")
    plt.ylabel("Average Macro F1")
    plt.show()


def plot_core_micro_gg(fnamex: pd.DataFrame) -> None:

    fx = fnamex.groupby(["setting"])["micro_F"].mean().sort_values().index.values
    logger.debug("DataFrame columns: %s", fnamex.columns)
    g = sns.FacetGrid(fnamex, col="dataset", hue="setting", col_wrap=3)
    g = g.map(
        plt.plot, "percent_train", "micro_F", marker="o", linewidth=1
    ).add_legend()
    g.set_xlabels("Train percentage (%)")
    g.set_ylabels("Average Micro F1")
    plt.show()

    sns.boxplot(x="setting", y="micro_F", data=fnamex, color="white", order=fx)
    plt.xticks(rotation=45)
    plt.xlabel("Algorithm")
    plt.ylabel("Average Micro F1")
    plt.show()


def plot_core_time_gg(fname: str) -> None:

    fnamex = pd.read_csv(fname, sep=" ")
    fnamex.columns = cnames

    #       + geom_boxplot()
    #       + theme(axis_text_x=element_text(rotation=90, hjust=1))
    #       + theme_bw()
    #       + facet_wrap('~dataset')
    #       )
    # gx.draw()
    # plt.show()


def plot_core_variability(fname: str) -> None:

    fname = pd.read_csv(fname, separator=" ")
    # for each dataset, take all variability and get it to a box plot


def plot_core_time(fnamex: pd.DataFrame) -> int:

    fnamex.columns = cnames
    logger.debug("DataFrame head:\n%s", fnamex.head())
    sns.boxplot("setting", "time", data=fnamex)
    plt.show()
    return 1


def plot_critical_distance(fname: str, num_algo: int = 14) -> None:

    import operator
    from collections import defaultdict

    import matplotlib.pyplot as plt
    import Orange

    #    print(fname.head())

    names = fname.setting.unique()
    rkx = fname.groupby(["dataset", "setting"])["macro_F"].mean()
    ranks = defaultdict(list)
    clf_ranks = defaultdict(list)
    for df, clf in rkx.index:
        ranks[df].append((clf, rkx[(df, clf)]))

    for _k, v in ranks.items():
        a = dict(v)
        sorted_d = sorted(a.items(), key=operator.itemgetter(1))
        for en, j in enumerate(sorted_d):
            logger.debug("Rank %d: %s", en, j[0])
            clf_ranks[j[0]].append(len(sorted_d) - en)

    logger.info("Classifier ranks: %s", clf_ranks)
    clf_score = {k: np.mean(v) for k, v in clf_ranks.items()}
    names = list(clf_score.keys())
    avranks = list(clf_score.values())
    cd = Orange.evaluation.compute_CD(avranks, num_algo, alpha="0.05")
    Orange.evaluation.graph_ranks(
        avranks, names, cd=cd, width=6, textspace=1.5, reverse=True
    )
    plt.show()

    rkx = fname.groupby(["dataset", "setting"])["micro_F"].mean()
    ranks = defaultdict(list)
    clf_ranks = defaultdict(list)
    for df, clf in rkx.index:
        ranks[df].append((clf, rkx[(df, clf)]))

    for _k, v in ranks.items():
        a = dict(v)
        sorted_d = sorted(a.items(), key=operator.itemgetter(1))
        for en, j in enumerate(sorted_d):
            logger.debug("Rank %d: %s", en, j[0])
            clf_ranks[j[0]].append(len(sorted_d) - en)

    logger.info("Classifier ranks: %s", clf_ranks)
    clf_score = {k: np.mean(v) for k, v in clf_ranks.items()}
    names = list(clf_score.keys())
    avranks = list(clf_score.values())
    cd = Orange.evaluation.compute_CD(avranks, num_algo, alpha="0.05")
    Orange.evaluation.graph_ranks(
        avranks, names, cd=cd, width=6, textspace=1.5, reverse=True
    )
    plt.show()

    fname["time"] = 1 / fname["time"]
    rkx = fname.groupby(["dataset", "setting"])["time"].mean()
    ranks = defaultdict(list)
    clf_ranks = defaultdict(list)
    for df, clf in rkx.index:
        ranks[df].append((clf, rkx[(df, clf)]))

    for _k, v in ranks.items():
        a = dict(v)
        sorted_d = sorted(a.items(), key=operator.itemgetter(1))
        for en, j in enumerate(sorted_d):
            logger.debug("Rank %d: %s", en, j[0])
            clf_ranks[j[0]].append(len(sorted_d) - en)

    logger.info("Classifier ranks: %s", clf_ranks)
    clf_score = {k: np.mean(v) for k, v in clf_ranks.items()}
    names = list(clf_score.keys())
    avranks = list(clf_score.values())
    cd = Orange.evaluation.compute_CD(avranks, 54, alpha="0.05")
    Orange.evaluation.graph_ranks(
        avranks, names, cd=cd, width=6, textspace=1.5, reverse=True
    )
    plt.show()


def plot_mean_times(fn: pd.DataFrame) -> None:

    # for each dataset, plot times.
    fx = fn.groupby(["setting"])["time"].mean().sort_values().index.values
    rkx = fn.groupby(["dataset", "setting"])["time"].mean()
    rkx.reset_index()

    ax = sns.boxplot(x="setting", y="time", data=fn, color="white", order=fx)
    plt.xticks(rotation=45)
    ax.set_xlabel("Algorithm", fontsize=20)
    ax.set_ylabel("Average execution time (s)", fontsize=20)
    ax.set_yscale("log")
    ax.tick_params(labelsize=15)
    plt.show()


def plot_robustness(infile: pd.DataFrame) -> None:

    logger.debug("Input DataFrame head:\n%s", infile.head())
    #    infile['percent_train'] = pd.to_numeric(infile['percent_train'])
    infile = infile[infile["percent_train"] < 0.6]
    p1 = sns.boxplot("percent_train", "macro_F", data=infile)
    p1.set_xlabel("Train percent", fontsize=20)
    p1.set_ylabel("Macro F score", fontsize=20)
    plt.show()

    p1 = sns.boxplot("percent_train", "micro_F", data=infile)
    p1.set_xlabel("Train percent", fontsize=20)
    p1.set_ylabel("Micro F score", fontsize=20)
    plt.show()

    #       + geom_density_2d(aes(color='percent_train'))
    #       +xlab("Macro F score")
    #       +ylab("Micro F score")
    #       + theme(axis_text=element_text(size=15))
    #       + theme(axis_title=element_text(size=15))
    #       + theme_bw()
    # )
    # gx.draw()
    # plt.show()


def generic_grouping(
    fname: pd.DataFrame,
    score_name: str,
    threshold: float = 1.0,
    percentages: bool = True,
) -> pd.DataFrame:
    fname = fname[fname["percent_train"] < threshold]
    sub1 = fname[["percent_train", score_name, "setting", "dataset"]]
    if percentages:
        sub1["dataset"] = sub1["dataset"] + "_" + sub1["percent_train"].astype(str)
    grouped = sub1.groupby(["dataset", "setting"]).agg(["mean", "std"])
    grouped.score_name = np.round(grouped[score_name], 3)
    stdacc = np.round(grouped[score_name, "std"], 2)
    meanacc = np.round(grouped[score_name, "mean"], 2)
    acc_agg = meanacc.map(str) + " (" + stdacc.map(str) + ")"

    grouped = (
        grouped.drop([("percent_train", "mean")], axis=1)
        .drop([("percent_train", "std")], axis=1)
        .drop([(score_name, "std")], axis=1)
    )
    grouped[(score_name, "mean")] = acc_agg
    grouped = grouped.reset_index()
    grouped.columns = ["dataset", "setting", "score"]

    if percentages:
        df0 = grouped.pivot(index="dataset", columns="setting", values="score")
    else:
        df0 = grouped.pivot(index="dataset", columns="setting", values="score").T
    return df0


def table_to_latex(fname, outfolder="../final_results/tables/", threshold=1):

    df0 = generic_grouping(fname, "micro_F", threshold)
    df0.to_latex(outfolder + "micro_F.tex", index=True)

    df1 = generic_grouping(fname, "macro_F", threshold)
    df1.to_latex(outfolder + "macro_F.tex", index=True)

    df2 = generic_grouping(fname, "time", threshold)
    df2.to_latex(outfolder + "time.tex", index=True)
