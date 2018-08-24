import os
import time
from datetime import datetime
import logging
import json

from .core import ExperimentKB, Rule
from .learners import HeuristicLearner, OptimalLearner
from .stats import scorefunctions, adjustment, significance, Validate
from .core.load import load_graph
from .core.settings import VERSION, DESCRIPTION, logger
from .core.converters import *

def _parameters_report(args, start, time_taken):
    sep = '-'*40 + '\n'
    rep = DESCRIPTION + '\n' +\
        'Version: %s' % VERSION + '\n' +\
        'Start: %s' % start + '\n' +\
        'Time taken: %.2f seconds' % time_taken + '\n' +\
        'Parameters:' + '\n'

    for arg, val in args.items():
        rep += '\t%s=%s\n' % (arg, str(val))
    rep = sep + rep + sep

    return rep

def generate_rules_report(kwargs, rules_per_target, human=lambda label, rule: label):
    rules_report = ''
    for _, rules in rules_per_target:
        
        if rules:
            rules_report += Rule.ruleset_report(rules, show_uris=kwargs['uris'],
                                                human=human,latex=kwargs['latex_report'])
            rules_report += '\n'
    if not rules_report:
        rules_report = 'No significant rules found'
        
    return rules_report

def run(kwargs, cli=True):

    
    ## change non-default settings. This is useful for func calls
        
    if cli:
        logger.setLevel(logging.DEBUG if kwargs['verbose'] else logging.INFO)
    else:
        logger.setLevel(logging.NOTSET)

    logger.info('Starting Hedwig3')
    start = time.time()
    start_date = datetime.now().isoformat()
    
    ## here comest the network reduction part.
    graph = build_graph(kwargs)
        
    logger.info('Building the knowledge base')
    score_func = getattr(scorefunctions, kwargs['score'])
    kb = ExperimentKB(graph, score_func, instances_as_leaves=kwargs['leaves'])
    validator = Validate(kb, significance_test=significance.apply_fisher,
                         adjustment=getattr(adjustment, kwargs['adjust']))

    rules_per_target = run_learner(kwargs, kb, validator)
    rules_report = generate_rules_report(kwargs, rules_per_target)

    end = time.time()
    time_taken = end-start
    logger.info('Finished in %d seconds' % time_taken)

    logger.info('Outputing results')

    if kwargs['covered']:
        with open(kwargs['covered'], 'w') as f:
            examples = Rule.ruleset_examples_json(rules_per_target)
            f.write(json.dumps(examples, indent=2))

    parameters_report = _parameters_report(kwargs, start_date, time_taken)
    rules_out_file = kwargs['output']
    if rules_out_file:
        with open(rules_out_file, 'w') as f:
            if rules_out_file.endswith('json'):
                f.write(Rule.to_json(rules_per_target, show_uris=kwargs['uris']))
            else:
                f.write(parameters_report)
                f.write(rules_report)
    else:
        print (parameters_report)
        print (rules_report)

    return rules_per_target


def build_graph(kwargs):
    data = kwargs['data']
    base_name = data.split('.')[0]

    # Walk the dir to find BK files
    ontology_list = []
    for root, sub_folders, files in os.walk(kwargs['bk_dir']):
        ontology_list.extend(map(lambda f: os.path.join(root, f), files))

    try:
        graph = load_graph(
            ontology_list,
            data,
            def_format=kwargs['format'],
            cache=not kwargs['nocache']
        )
    except Exception as e:
        print (e,"Could not load the graph..")
        exit(1)
    return graph


def run_learner(kwargs, kb, validator):

    if kb.is_discrete_target():
        targets = kb.class_values if not kwargs['target'] else [kwargs['target']]
    else:
        targets = [None]

    rules_report = ''
    rules_per_target = []

    for target in targets:
        if target:
            logger.info('Starting '+kwargs['learner']+' learner for target \'%s\'' % target)
        else:
            logger.info('Ranks detected - starting learner.')

        learner_cls = {
            'heuristic': HeuristicLearner,
            'optimal': OptimalLearner
        } [kwargs['learner']]
        learner = learner_cls(kb,
                          n=kwargs['beam'],
                          min_sup=int(kwargs['support']*kb.n_examples()),
                          target=target,
                          depth=kwargs['depth'],
                          sim=0.9,
                          use_negations=kwargs['negations'],
                          optimal_subclass=kwargs['optimalsubclass'])

        rules = learner.induce()

        if kb.is_discrete_target():
            if kwargs['adjust'] == 'fdr':
                logger.info('Validating rules, FDR = %.3f' % kwargs['FDR'])
            elif kwargs['adjust'] == 'fwer':
                logger.info('Validating rules, alpha = %.3f' % kwargs['alpha'])
            rules = validator.test(rules, alpha=kwargs['alpha'], q=kwargs['FDR'])

        rules_per_target.append((target, rules))

    return rules_per_target
