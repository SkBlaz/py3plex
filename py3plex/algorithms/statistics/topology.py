# test scale-freenes of a network

from typing import Any, List, Tuple

import matplotlib.pyplot as plt
import networkx as nx

from ...logging_config import get_logger
from .powerlaw import Fit

logger = get_logger(__name__)


def basic_pl_stats(degree_sequence: List[int]) -> Tuple[float, float]:
    """
    Calculate basic power law statistics for a degree sequence.

    Args:
        degree_sequence: Degree sequence of individual nodes

    Returns:
        Tuple of (alpha, sigma) values
    """

    results = Fit(degree_sequence, discrete=True)
    return (results.alpha, results.sigma)


def plot_power_law(
    degree_sequence: List[int],
    title: str,
    xlabel: str,
    plabel: str,
    ylabel: str = "Number of nodes",
    formula_x: int = 70,
    formula_y: float = 0.05,
    show: bool = True,
    use_normalization: bool = False,
) -> Any:

    plt.figure(2)
    ax1 = plt.subplot(211)
    results = Fit(degree_sequence, discrete=True)

    a = results.power_law.pdf(degree_sequence)
    fig1 = results.plot_pdf(
        linewidth=1,
        color="black",
        label="Raw data",
        linear_bins=True,
        linestyle="",
        marker="o",
        markersize=1,
    )
    results.power_law.plot_pdf(
        linewidth=1.5, ax=fig1, color="green", linestyle="--", label="Power law"
    )
    results.lognormal.plot_pdf(
        linewidth=0.5, ax=fig1, color="blue", linestyle="-", label="Log-normal"
    )
    results.truncated_power_law.plot_pdf(
        linewidth=0.5,
        ax=fig1,
        color="orange",
        linestyle="-",
        label="Truncated power law",
    )
    results.exponential.plot_pdf(
        linewidth=0.5, ax=fig1, color="red", linestyle="-", label="Exponential"
    )

    logger.info("ALPHA: %s", results.alpha)
    logger.info("SIGMA: %s", results.sigma)
    logger.info("xmin: %s", results.xmin)

    logger.info(
        "percent of non PL coverage: %s",
        len([x for x in degree_sequence if x < results.xmin])
        * 100
        / len(degree_sequence),
    )
    logger.info(
        "Percentage of PL coverage: %s",
        len([x for x in degree_sequence if x > results.xmin])
        * 100
        / len(degree_sequence),
    )

    try:
        start = a[int(results.xmin)]
        k = results.xmin
        norm: Any = int(
            round(start * len(degree_sequence) * 100 / pow(k, -results.alpha), 0)
        )
    except (IndexError, KeyError, ValueError, ZeroDivisionError):
        norm = "C"

    # print ("Xm: ",results.fitting_cdf)
    # print ("n: ",results.n)

    logger.info("Fixed xmax: %s", results.fixed_xmax)
    logger.info(
        "Distribution compare (truncated_power_law vs lognormal): %s",
        results.distribution_compare("truncated_power_law", "lognormal"),
    )
    logger.info(
        "Distribution compare (lognormal vs power_law): %s",
        results.distribution_compare("lognormal", "power_law"),
    )
    logger.info(
        "Distribution compare (truncated_power_law vs power_law): %s",
        results.distribution_compare("truncated_power_law", "power_law"),
    )

    logger.info("............")

    logger.info(
        "Distribution compare (exponential vs lognormal): %s",
        results.distribution_compare("exponential", "lognormal"),
    )
    logger.info(
        "Distribution compare (exponential vs truncated_power_law): %s",
        results.distribution_compare("exponential", "truncated_power_law"),
    )
    logger.info(
        "Distribution compare (exponential vs power_law): %s",
        results.distribution_compare("exponential", "power_law"),
    )
    plt.legend(numpoints=1, loc="lower left", bbox_to_anchor=(0.05, 0))
    yticks = ax1.get_yticks()
    vals: List[float] = [float(round(x * len(degree_sequence), 1)) for x in yticks]
    ax1.set_yticklabels([str(v) for v in vals[0:6]])
    plt.ylabel(ylabel)
    plt.axvline(x=results.xmin, color="black", linestyle="--")
    plt.ylim(0, 0.1)

    if not use_normalization:
        norm = "C"

    ax1.text(
        formula_x,
        formula_y,
        r"$f(k) = " + norm + r" \cdot k^{-" + str(round(results.alpha, 3)) + "}$",
        fontsize=13,
    )

    #    plt.xlabel(xlabel)
    #    plt.figure(3)

    ax1 = plt.subplot(212)
    plt.axvline(x=results.xmin, color="black", linestyle="--")
    plt.xlabel(xlabel)
    ax1.text(results.xmin + 0.5, 0.001, r"$X_{min}$", fontsize=13)
    fig1 = results.plot_ccdf(
        linewidth=2,
        color="black",
        label="Raw data",
        linestyle="",
        marker="o",
        markersize=1,
    )
    results.power_law.plot_ccdf(
        ax=fig1, color="green", linestyle="--", label="Power law", linewidth=1.5
    )
    results.lognormal.plot_ccdf(
        ax=fig1, color="blue", linestyle="-", label="Log-normal"
    )
    results.truncated_power_law.plot_ccdf(
        ax=fig1, color="orange", linestyle="-", label="Truncated power law"
    )
    results.exponential.plot_ccdf(
        ax=fig1, color="red", linestyle="-", label="Exponential", linewidth=0.5
    )

    #    ax1.set_xscale('log')
    #    ax1.set_xticks([20,30,40,65])
    #    plt.xticks(x, [1,10,100,1000], rotation='vertical')

    plt.ylabel(r"$P(k) = Pr(K \geq k)$")
    #    plt.xlim(5,120)

    if show:
        plt.show()


if __name__ == "__main__":

    G = nx.powerlaw_cluster_graph(1000, 3, 0.5, 1573)
    val_vect = sorted(dict(nx.degree(G)).values(), reverse=True)
    plot_power_law(val_vect, "", "Node degree", "individual node")
