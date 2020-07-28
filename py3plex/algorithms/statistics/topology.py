## test scale-freenes of a network

import networkx as nx
import numpy as np
import random
import argparse
from itertools import groupby, chain
from collections import defaultdict
import pandas as pd
from .powerlaw import *
import matplotlib.pyplot as plt


def basic_pl_stats(degree_sequence):
    """
    :param degree sequence of individual nodes
    """

    results = Fit(degree_sequence, discrete=True)
    return (results.alpha, results.sigma)


def plot_power_law(degree_sequence,
                   title,
                   xlabel,
                   plabel,
                   ylabel="Number of nodes",
                   formula_x=70,
                   formula_y=0.05,
                   show=True,
                   use_normalization=False):

    plt.figure(2)
    ax1 = plt.subplot(211)
    results = Fit(degree_sequence, discrete=True)

    a = results.power_law.pdf(degree_sequence)
    fig1 = results.plot_pdf(linewidth=1,
                            color="black",
                            label="Raw data",
                            linear_bins=True,
                            linestyle="",
                            marker="o",
                            markersize=1)
    results.power_law.plot_pdf(linewidth=1.5,
                               ax=fig1,
                               color="green",
                               linestyle="--",
                               label="Power law")
    results.lognormal.plot_pdf(linewidth=0.5,
                               ax=fig1,
                               color="blue",
                               linestyle="-",
                               label="Log-normal")
    results.truncated_power_law.plot_pdf(linewidth=0.5,
                                         ax=fig1,
                                         color="orange",
                                         linestyle="-",
                                         label="Truncated power law")
    results.exponential.plot_pdf(linewidth=0.5,
                                 ax=fig1,
                                 color="red",
                                 linestyle="-",
                                 label="Exponential")

    print("ALPHA: ", results.alpha)
    print("SIGMA: ", results.sigma)
    print("xmin: ", results.xmin)

    print("percent of non PL coverage: {}".format(
        len([x for x in degree_sequence if x < results.xmin]) * 100 /
        len(degree_sequence)))
    print("Percentage of PL coverage: {}".format(
        len([x for x in degree_sequence if x > results.xmin]) * 100 /
        len(degree_sequence)))

    try:
        start = a[int(results.xmin)]
        k = results.xmin
        norm = int(
            round(start * len(degree_sequence) * 100 / pow(k, -results.alpha),
                  0))
    except:
        norm = "C"

    # print ("Xm: ",results.fitting_cdf)
    # print ("n: ",results.n)

    print("Fixed xmax: ", results.fixed_xmax)
    print(results.distribution_compare('truncated_power_law', 'lognormal'))
    print(results.distribution_compare('lognormal', 'power_law'))
    print(results.distribution_compare('truncated_power_law', 'power_law'))

    print("............")

    print(results.distribution_compare('exponential', 'lognormal'))
    print(results.distribution_compare('exponential', 'truncated_power_law'))
    print(results.distribution_compare('exponential', 'power_law'))
    import matplotlib.ticker as mtick
    from matplotlib.ticker import ScalarFormatter, FormatStrFormatter
    plt.legend(numpoints=1, loc="lower left", bbox_to_anchor=(0.05, 0))
    vals = ax1.get_yticks()
    vals = [float(round(x * len(degree_sequence), 1)) for x in vals]
    ax1.set_yticklabels(vals[0:6])
    plt.ylabel(ylabel)
    plt.axvline(x=results.xmin, color="black", linestyle="--")
    plt.ylim(0, 0.1)

    if not use_normalization:
        norm = "C"

    ax1.text(formula_x,
             formula_y,
             r"$f(k) = " + norm + " \cdot k^{-" +
             str(round(results.alpha, 3)) + "}$",
             fontsize=13)

    #    plt.xlabel(xlabel)
    #    plt.figure(3)

    ax1 = plt.subplot(212)
    plt.axvline(x=results.xmin, color="black", linestyle="--")
    plt.xlabel(xlabel)
    ax1.text(results.xmin + 0.5, 0.001, r"$X_{min}$", fontsize=13)
    fig1 = results.plot_ccdf(linewidth=2,
                             color="black",
                             label="Raw data",
                             linestyle="",
                             marker="o",
                             markersize=1)
    results.power_law.plot_ccdf(ax=fig1,
                                color="green",
                                linestyle="--",
                                label="Power law",
                                linewidth=1.5)
    results.lognormal.plot_ccdf(ax=fig1,
                                color="blue",
                                linestyle="-",
                                label="Log-normal")
    results.truncated_power_law.plot_ccdf(ax=fig1,
                                          color="orange",
                                          linestyle="-",
                                          label="Truncated power law")
    results.exponential.plot_ccdf(ax=fig1,
                                  color="red",
                                  linestyle="-",
                                  label="Exponential",
                                  linewidth=0.5)

    #    ax1.set_xscale('log')
    #    ax1.set_xticks([20,30,40,65])
    #    plt.xticks(x, [1,10,100,1000], rotation='vertical')

    import matplotlib.ticker as mtick
    plt.ylabel(r"$P(k) = Pr(K \geq k)$")
    #    plt.xlim(5,120)

    if show:
        plt.show()


if __name__ == "__main__":

    G = nx.powerlaw_cluster_graph(1000, 3, 0.5, 1573)
    val_vect = sorted(dict(nx.degree(G)).values(), reverse=True)
    plot_power_law(val_vect, "", "Node degree", "individual node")
