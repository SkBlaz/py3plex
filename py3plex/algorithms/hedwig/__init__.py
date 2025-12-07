import json
import logging
import multiprocessing as mp
import os
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from tqdm import tqdm

from .core import ExperimentKB, Rule
from .core.load import load_graph
from .core.settings import DESCRIPTION, VERSION, logger
from .core.converters import convert_mapping_to_rdf, obo2n3
from .learners import HeuristicLearner, OptimalLearner
from .stats import Validate, adjustment, scorefunctions, significance

# Global variables for multiprocessing (set by run_learner)
arguments: Dict[str, Any] = {}
knowledgebase: Any = None
validator_object: Any = None


def _parameters_report(args: Dict[str, Any], start: str, time_taken: float) -> str:
    sep = "-" * 40 + "\n"
    rep = (
        DESCRIPTION
        + "\n"
        + f"Version: {VERSION}"
        + "\n"
        + f"Start: {start}"
        + "\n"
        + f"Time taken: {time_taken:.2f} seconds"
        + "\n"
        + "Parameters:"
        + "\n"
    )

    for arg, val in args.items():
        rep += f"\t{arg}={str(val)}\n"
    rep = sep + rep + sep

    return rep


def generate_rules_report(
    kwargs: Dict[str, Any],
    rules_per_target: List[Tuple[Any, List[Any]]],
    human: Callable[[Any, Any], Any] = lambda label, rule: label,
) -> str:
    rules_report = ""
    for _, rules in rules_per_target:

        if rules:
            rules_report += Rule.ruleset_report(
                rules,
                show_uris=kwargs["uris"],
                human=human,
                latex=kwargs["latex_report"],
            )
            rules_report += "\n"
    if not rules_report:
        rules_report = "No significant rules found"

    return rules_report


def run(
    kwargs: Dict[str, Any],
    cli: bool = True,
    generator_tag: bool = False,
    num_threads: Union[str, int] = "all",
) -> List[Tuple[Any, List[Any]]]:

    # change non-default settings. This is useful for func calls

    if cli:
        logger.setLevel(logging.DEBUG if kwargs["verbose"] else logging.INFO)
    else:
        logger.setLevel(logging.NOTSET)

    logger.info("Starting Hedwig3")
    start = time.time()
    start_date = datetime.now().isoformat()

    # here comest the network reduction part.
    graph = build_graph(kwargs)

    logger.info("Building the knowledge base")
    score_func = getattr(scorefunctions, kwargs["score"])
    kb = ExperimentKB(graph, score_func, instances_as_leaves=kwargs["leaves"])
    validator = Validate(
        kb,
        significance_test=significance.apply_fisher,
        adjustment=getattr(adjustment, kwargs["adjust"]),
    )

    rules_per_target = run_learner(kwargs, kb, validator, num_threads=num_threads)
    rules_report = generate_rules_report(kwargs, rules_per_target)
    end = time.time()
    time_taken = end - start
    logger.info("Finished in %d seconds" % time_taken)

    logger.info("Outputing results")

    if kwargs["covered"]:
        with open(kwargs["covered"], "w") as f:
            examples = Rule.ruleset_examples_json(rules_per_target)
            f.write(json.dumps(examples, indent=2))

    parameters_report = _parameters_report(kwargs, start_date, time_taken)
    rules_out_file = kwargs["output"]
    if rules_out_file:
        with open(rules_out_file, "w") as f:
            if rules_out_file.endswith("json"):
                f.write(Rule.to_json(rules_per_target, show_uris=kwargs["uris"]))
            else:
                f.write(parameters_report)
                f.write(rules_report)
    else:
        logger.info(parameters_report)
        logger.info(rules_report)

    return rules_per_target


def build_graph(kwargs: Dict[str, Any]) -> Any:
    data = kwargs["data"]
    data.split(".")[0]

    # Walk the dir to find BK files
    ontology_list: List[str] = []
    for root, _sub_folders, files in os.walk(kwargs["bk_dir"]):
        ontology_list.extend(os.path.join(root, f) for f in files)

    try:
        graph = load_graph(
            ontology_list,
            data,
            def_format=kwargs["format"],
            cache=not kwargs["nocache"],
        )
    except Exception as e:
        logger.error("Could not load the graph: %s", e)
        exit(1)
    return graph


def rule_kernel(target: Any) -> Tuple[Any, List[Any]]:

    # find exact rule map
    # if target:
    #     logger.info('Starting '+arguments['learner']+' learner for target \'%s\'' % target)
    # else:
    #     logger.info('Ranks detected - starting learner.')

    learner_cls = {"heuristic": HeuristicLearner, "optimal": OptimalLearner}[
        arguments["learner"]
    ]
    learner = learner_cls(
        knowledgebase,
        n=arguments["beam"],
        min_sup=int(arguments["support"] * knowledgebase.n_examples()),
        target=target,
        depth=arguments["depth"],
        sim=0.9,
        use_negations=arguments["negations"],
        optimal_subclass=arguments["optimalsubclass"],
    )

    rules = learner.induce()

    if knowledgebase.is_discrete_target():
        # if arguments['adjust'] == 'fdr':
        #     logger.info('Validating rules, FDR = %.3f' % arguments['FDR'])
        # elif arguments['adjust'] == 'fwer':
        #     logger.info('Validating rules, alpha = %.3f' % arguments['alpha'])
        rules = validator_object.test(
            rules, alpha=arguments["alpha"], q=arguments["FDR"]
        )

    return (target, rules)


def run_learner(
    kwargs: Dict[str, Any],
    kb: ExperimentKB,
    validator: Validate,
    generator: bool = False,
    num_threads: Union[str, int] = "all",
) -> List[Tuple[Any, List[Any]]]:

    if kb.is_discrete_target():
        targets = list(kb.class_values if not kwargs["target"] else [kwargs["target"]])
    else:
        targets = [None]

    rules_per_target: List[Tuple[Any, List[Any]]] = []

    if num_threads != 0:
        global knowledgebase
        global arguments
        global validator_object
        validator_object = validator
        arguments = kwargs
        knowledgebase = kb
        n = len(targets)
        if num_threads == "all":
            step = mp.cpu_count()  # number of parallel processes
        else:
            step = int(num_threads)
        jobs = [range(n)[i : i + step] for i in range(0, n, step)]  # generate jobs

        rules_per_target = []
        pbar = tqdm(total=len(targets))
        for batch in jobs:
            with mp.Pool(processes=step) as p:
                batch_list = [targets[x] for x in batch]
                results = p.map(rule_kernel, batch_list)
                pbar.update(step)
                for rule in results:
                    rules_per_target.append(rule)
        pbar.close()
    else:
        for target in targets:
            if target:
                logger.info(
                    "Starting " + kwargs["learner"] + f" learner for target '{target}'"
                )
            else:
                logger.info("Ranks detected - starting learner.")

            learner_cls = {"heuristic": HeuristicLearner, "optimal": OptimalLearner}[
                kwargs["learner"]
            ]
            learner = learner_cls(
                kb,
                n=kwargs["beam"],
                min_sup=int(kwargs["support"] * kb.n_examples()),
                target=target,
                depth=kwargs["depth"],
                sim=0.9,
                use_negations=kwargs["negations"],
                optimal_subclass=kwargs["optimalsubclass"],
            )

            rules = learner.induce()

            if kb.is_discrete_target():
                if kwargs["adjust"] == "fdr":
                    logger.info("Validating rules, FDR = {:.3f}".format(kwargs["FDR"]))
                elif kwargs["adjust"] == "fwer":
                    logger.info(
                        "Validating rules, alpha = {:.3f}".format(kwargs["alpha"])
                    )
                rules = validator.test(rules, alpha=kwargs["alpha"], q=kwargs["FDR"])

            rules_per_target.append((target, rules))

    return rules_per_target
