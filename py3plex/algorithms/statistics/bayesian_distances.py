# tutorial

from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

from .bayesiantests import hierarchical, hierarchical_MC, plot_posterior


def generate_bayesian_diagram(
    result_matrices: np.ndarray,
    algo_names: Optional[List[str]] = None,
    rope: float = 0.01,
    rho: float = 1 / 5,
    show_diagram: bool = True,
    save_diagram: Optional[str] = None,
) -> Tuple[float, float, float]:
    """
    Generate Bayesian comparison diagram for algorithm results.

    Args:
        result_matrices: Results matrices from cross-validation
        algo_names: Names of algorithms being compared
        rope: Region of practical equivalence (default: 0.01)
        rho: Correlation parameter (default: 1/5)
        show_diagram: Whether to display the diagram (default: True)
        save_diagram: Path to save diagram (optional)

    Returns:
        Tuple of (left probability, equivalence probability, right probability)
    """

    # rope=0.01 #we consider two classifers equivalent when the difference of accuracy is less that 1%
    if algo_names is None:
        algo_names = ["algo1", "algo2"]
    print(rope, rho)
    # rho=1/5 #we are performing 10 folds, 10 runs cross-validation
    pl, pe, pr = hierarchical(
        result_matrices, rope, rho, verbose=True, names=algo_names
    )
    samples = hierarchical_MC(result_matrices, rope, rho, names=algo_names)

    # plt.rcParams['figure.facecolor'] = 'black'
    plot_posterior(
        samples, algo_names, proba_triplet=[np.round(pl, 2), pe, np.round(pr, 2)]
    )

    if show_diagram:
        plt.show()

    if save_diagram is not None:
        plt.savefig(save_diagram)
    return (pl, pe, pr)
