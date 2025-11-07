from .learner import Learner as HeuristicLearner
from .optimal import OptimalLearner

# here add random rules, as well as bottom-up search

__all__ = ["HeuristicLearner", "OptimalLearner"]
