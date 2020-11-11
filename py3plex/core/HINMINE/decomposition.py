# this is the code for the network decomposition

from math import log
import numpy as np
from collections import defaultdict


def aggregate_sum(input_thing, classes, universal_set):
    if type(input_thing) == list:
        return sum(input_thing)
    elif type(input_thing) == dict:
        output = {}
        for key in input_thing:
            output[key] = sum(input_thing[key])
        return output
    else:
        raise AttributeError('Expected dictionary or list as first argument')


def aggregate_weighted_sum(input_thing, classes, universal_set):
    n = len(universal_set)
    weights = [(len(cl.train_members) + len(cl.validate_members)) * 1.0 / n
               for cl in classes]
    n_classes = len(classes)
    if type(input_thing) == list:
        running_sum = 0
        for i in range(n_classes):
            running_sum += weights[i] * input_thing[i]
        return running_sum
    elif type(input_thing) == dict:
        return_dict = {}
        for key in input_thing:
            running_sum = 0
            for i in range(n_classes):
                running_sum += weights[i] * input_thing[key][i]
            return_dict[key] = running_sum
        return return_dict
    else:
        raise AttributeError('Expected dictionary or list as first argument')


def get_calculation_method(method_name):
    if method_name == 'tf':
        return calculate_importance_tf
    elif method_name == 'chi':
        return calculate_importance_chi
    elif method_name == 'ig':
        return calculate_importance_ig
    elif method_name == 'gr':
        return calculate_importance_gr
    elif method_name == 'idf':
        return calculate_importance_idf
    elif method_name == 'delta':
        return calculate_importance_delta
    elif method_name == 'rf':
        return calculate_importance_rf
    elif method_name == 'okapi':
        return calculate_importance_okapi
    elif method_name == "w2w":  # TBA
        return calculate_importance_w2w
    else:
        raise Exception('Unknown weighing method')


def get_aggregation_method(method_name):
    if method_name == 'sum':
        return aggregate_sum
    elif method_name == 'weighted_sum':
        return aggregate_weighted_sum
    else:
        raise Exception('Unknown aggregation method')


def calculate_importances(midpoints,
                          classes,
                          universal_set,
                          method,
                          degrees=None,
                          avgdegree=None):
    n = len(universal_set)
    importance_calculator = get_calculation_method(method)
    return_dict = {}
    for midpoint in midpoints:
        if degrees is None:
            return_dict[midpoint] = importance_calculator(
                classes, universal_set, midpoints[midpoint], n)
        else:
            return_dict[midpoint] = importance_calculator(classes,
                                                          universal_set,
                                                          midpoints[midpoint],
                                                          n,
                                                          degrees=degrees,
                                                          avgdegree=avgdegree)
    return return_dict


def calculate_importance_tf(classes, universal_set, linked_nodes, n, **kwargs):
    """
    Calculates importance of a single midpoint using term frequency weighing.
    :param classes: List of all classes
    :param universal_set: Set of all indices to consider
    :param linked_nodes: Set of all nodes linked by the midpoint
    :param n: Number of elements of universal set
    :return: List of weights of the midpoint for each label in class
    """
    return [1.0 / len(classes) for _ in classes]


def np_calculate_importance_tf(predicted, label_matrix):
    return (1.0 / label_matrix.shape[1]) * np.ones(label_matrix.shape[1])


def calculate_importance_chi(classes, universal_set, linked_nodes, n,
                             **kwargs):
    """
    Calculates importance of a single midpoint using chi-squared weighing.
    :param classes: List of all classes
    :param universal_set: Set of all indices to consider
    :param linked_nodes: Set of all nodes linked by the midpoint
    :param n: Number of elements of universal set
    :return: List of weights of the midpoint for each label in class
    """
    predicted_pos = universal_set.intersection(linked_nodes)
    predicted_pos_num = len(predicted_pos)
    return_list = []
    for label in classes:
        if label is None:
            continue
        actual_pos = label.not_test_members
        actual_pos_num = label.not_test_members_num
        tp = len(predicted_pos.intersection(actual_pos))
        return_list.append(chi_value(actual_pos_num, predicted_pos_num, tp, n))
    return return_list


def np_calculate_importance_chi(predicted, label_matrix, actual_pos_nums):
    tp = predicted * label_matrix
    predicted_pos_num = np.count_nonzero(predicted)  # TODO: speed this up!
    tp_nums = np.ones((1, label_matrix.shape[0])).dot(tp)
    fp_nums = predicted_pos_num - tp_nums
    fn_nums = actual_pos_nums - tp_nums
    tn_nums = label_matrix.shape[0] - tp_nums - fp_nums - fn_nums
    tmp = tp_nums * tn_nums - fp_nums * fn_nums
    # TODO: alternative: tp_nums = count something greater than 0.
    top = tmp * tmp
    bot = predicted_pos_num * (fn_nums +
                               tn_nums) * actual_pos_nums * (tn_nums + fp_nums)
    # bot_zeros = np.where(bot == 0)[0]
    # bot[bot_zeros] = 1
    # if not np.all(top[bot_zeros] == 0):
    #     raise Exception('Error in chi implementation')
    bot[bot == 0] = 1
    res = top / bot
    return res


def calculate_importance_w2w(classes, universal_set, linked_nodes, n,
                             **kwargs):
    pass


def calculate_importance_ig(classes, universal_set, linked_nodes, n, **kwargs):
    """
    Calculates importance of a single midpoint using IG (information gain) weighing
    :param classes: List of all classes
    :param universal_set: Set of all indices to consider
    :param linked_nodes: Set of all nodes linked by the midpoint
    :param n: Number of elements of universal set
    :return: List of weights of the midpoint for each label in class
    """
    predicted_pos = universal_set.intersection(linked_nodes)
    predicted_pos_num = len(predicted_pos)
    return_list = []
    for label in classes:
        if label is None:
            continue
        actual_pos = label.not_test_members
        actual_pos_num = label.not_test_members_num
        tp = len(predicted_pos.intersection(actual_pos))
        return_list.append(ig_value(actual_pos_num, predicted_pos_num, tp, n))
    return return_list


def calculate_importance_gr(classes, universal_set, linked_nodes, n, **kwargs):
    """
    Calculates importance of a single midpoint using the GR (gain ratio)
    :param classes: List of all classes
    :param universal_set: Set of all indices to consider
    :param linked_nodes: Set of all nodes linked by the midpoint
    :param n: Number of elements of universal set
    :return: List of weights of the midpoint for each label in class
    """
    predicted_pos = universal_set.intersection(linked_nodes)
    predicted_pos_num = len(predicted_pos)
    return_list = []
    for label in classes:
        if label is None:
            continue
        actual_pos = label.not_test_members
        actual_pos_num = label.not_test_members_num
        tp = len(predicted_pos.intersection(actual_pos))
        return_list.append(gr_value(actual_pos_num, predicted_pos_num, tp, n))
    return return_list


def calculate_importance_okapi(classes,
                               universal_set,
                               linked_nodes,
                               n,
                               degrees=None,
                               avgdegree=None):
    k1 = 1.5
    b = 0.75
    predicted_pos = universal_set.intersection(linked_nodes)  #
    predicted_pos_num = len(predicted_pos)
    log((n - predicted_pos_num + 0.5) / (predicted_pos_num + 0.5))
    return_vec = np.zeros((len(linked_nodes), 1))
    for i, linked_node in enumerate(linked_nodes):
        return_vec[i] = (k1 +
                         1) / (1 + k1 *
                               (1 - b + b * degrees[linked_node] / avgdegree))
    return [return_vec for _ in classes]


def calculate_importance_idf(classes, universal_set, linked_nodes, n,
                             **kwargs):
    """
    Calculates importance of a single midpoint using idf weighing
    :param classes: List of all classes
    :param universal_set: Set of all indices to consider
    :param linked_nodes: Set of all nodes linked by the midpoint
    :param n: Number of elements of universal set
    :return: List of weights of the midpoint for each label in class
    """
    predicted_pos = universal_set.intersection(linked_nodes)
    predicted_pos_num = len(predicted_pos)
    idf = log(n * 1.0 / (1 + predicted_pos_num))
    return_list = [idf for _ in classes]
    return return_list


def calculate_importance_delta(classes, universal_set, linked_nodes, n,
                               **kwargs):
    """
    Calculates importance of a single midpoint using delta-idf weighing
    :param classes: List of all classes
    :param universal_set: Set of all indices to consider
    :param linked_nodes: Set of all nodes linked by the midpoint
    :param n: Number of elements of universal set
    :return: List of weights of the midpoint for each label in class
    """
    predicted_pos = universal_set.intersection(linked_nodes)
    predicted_pos_num = len(predicted_pos)
    predicted_neg_num = n - predicted_pos_num
    return_list = []
    for label in classes:
        if label is None:
            continue
        actual_pos_num = label.not_test_members_num
        actual_neg_num = n - actual_pos_num
        diff = actual_pos_num * 1.0 / (predicted_pos_num +
                                       1) - actual_neg_num * 1.0 / (
                                           predicted_neg_num + 1)
        return_list.append(abs(diff))
    return return_list


def calculate_importance_rf(classes, universal_set, linked_nodes, n, **kwargs):
    """
    Calculates importance of a single midpoint using rf weighing
    :param classes: List of all classes
    :param universal_set: Set of all indices to consider
    :param linked_nodes: Set of all nodes linked by the midpoint
    :param n: Number of elements of universal set
    :return: List of weights of the midpoint for each label in class
    """
    predicted_pos = universal_set.intersection(linked_nodes)
    predicted_pos_num = len(predicted_pos)
    return_list = []
    for label in classes:
        if label is None:
            continue
        actual_pos = label.not_test_members
        tp = len(predicted_pos.intersection(actual_pos))
        return_list.append(rf_value(predicted_pos_num, tp))
    return return_list


def rf_value(predicted_pos_num, tp):
    fp = predicted_pos_num - tp
    return log(2 + tp * 1.0 / max(1, fp), 2)


def ig_value(actual_pos_num, predicted_pos_num, tp, n):
    fp = predicted_pos_num - tp
    fn = actual_pos_num - tp
    tn = n - tp - fp - fn
    tpp = tp * 1.0 / n
    tnp = tn * 1.0 / n
    fpp = fp * 1.0 / n
    fnp = fn * 1.0 / n
    r = 0
    if tp > 0:
        r += tpp * log(tp * n * 1.0 / (actual_pos_num * predicted_pos_num), 2)
    if fn > 0:
        r += fnp * log(
            fn * n * 1.0 / (actual_pos_num * (n - predicted_pos_num)), 2)
    if fp > 0:
        r += fpp * log(
            fp * n * 1.0 / ((n - actual_pos_num) * predicted_pos_num), 2)
    if tn > 0:
        r += tnp * log(
            tn * n * 1.0 / ((n - actual_pos_num) * (n - predicted_pos_num)), 2)
    assert r >= 0
    return r


def gr_value(actual_pos_num, predicted_pos_num, tp, n):
    pp = actual_pos_num * 1.0 / n
    if pp == 1 or pp == 0:
        return 0
    return ig_value(actual_pos_num, predicted_pos_num, tp,
                    n) / (-pp * log(pp, 2) - (1 - pp) * log((1 - pp), 2))


def chi_value(actual_pos_num, predicted_pos_num, tp, n):
    fp = predicted_pos_num - tp
    fn = actual_pos_num - tp
    tn = n - tp - fp - fn
    tmp = tp * tn - fp * fn
    top = tmp * tmp
    bot = predicted_pos_num * (fn + tn) * actual_pos_num * (tn + fp)
    if bot > 0:
        return top * 1.0 / bot
    elif bot == 0:
        return 0
    else:
        raise Exception("Error in chi implementation.")


def hinmine_get_cycles(network, cycle=None):
    if cycle is None:
        candidates = network.calculate_decomposition_candidates()
        cycle = []
        for x in candidates:
            edges = x['edge_list']
            node = x['node_list']
            spr = "_____"
            try:
                if node[0] == node[2]:
                    cycle.append(node[0] + spr + edges[0] + spr + node[1] +
                                 spr + edges[1] + spr + node[2])
            except:
                pass

    return cycle


def hinmine_decompose(network, heuristic, cycle=None, parallel=False):
    if cycle is None:
        candidates = network.calculate_decomposition_candidates()
        cycle = []
        for x in candidates:
            edges = x['edge_list']
            node = x['node_list']
            spr = "_____"
            try:
                cycle.append(node[0] + spr + edges[0] + spr + node[1] + spr +
                             edges[1] + spr + node[2])
            except:
                pass

        print(
            'No decomposition cycle provided. Candidate cycles thus used are: %s'
            % cycle)


#       cycle = cycle[0:2]
    try:
        cycles = cycle
    except KeyError:
        raise Exception('No decomposition cycle selected')
    hin = network

    if parallel:
        import multiprocessing as mp
        p = mp.Pool(processes=mp.cpu_count())
    else:
        p = None

    for cycle in cycles:
        cycle = cycle.split('_____')
        node_sequence = []
        edge_sequence = []
        for i in range(len(cycle)):
            if i % 2 == 0:
                node_sequence.append(cycle[i])
            else:
                edge_sequence.append(cycle[i])
        degrees = defaultdict(int)
        for item in hin.midpoint_generator(node_sequence, edge_sequence):
            for node in item:
                degrees[node] += 1

        hin.decompose_from_iterator('decomposition',
                                    heuristic,
                                    None,
                                    hin.midpoint_generator(
                                        node_sequence, edge_sequence),
                                    degrees=degrees,
                                    parallel=parallel,
                                    pool=p)

    return hin
