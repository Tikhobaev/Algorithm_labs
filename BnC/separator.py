import numpy as np
from numpy import argsort


def _sort_desc_by_weight(graph, weights):
    return list(argsort(weights)[::-1])


def _sort_by_weight_div_degrees(graph, weights):
    new_weights = np.array(weights) / np.array([graph.degree(i) + 1 for i in range(1, len(weights) + 1)])
    return list(argsort(new_weights)[::-1])


def _find_maximal_weighted_set(graph, weights, sort_func=_sort_by_weight_div_degrees):
    result = []
    deleted = [False] * len(weights)
    sorted_vertices: list = sort_func(graph, weights)

    for v in sorted_vertices:
        if deleted[v]:
            continue
        result.append(v + 1)
        for neighbour in graph.neighbors(v + 1):
            deleted[neighbour - 1] = True

    return result, sum([weights[v - 1] for v in result])


def find_maximal_weighted_set(graph, weights):
    set_first, weight_first = _find_maximal_weighted_set(graph, weights, _sort_desc_by_weight)
    set_second, weight_second = _find_maximal_weighted_set(graph, weights, _sort_by_weight_div_degrees)

    if weight_first > weight_second:
        return set_first, weight_first
    return set_second, weight_second
