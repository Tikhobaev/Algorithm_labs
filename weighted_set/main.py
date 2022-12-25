import re
import networkx as nx
import numpy as np
from time import time
from pandas import DataFrame
from heuristic import find_maximal_weighted_set


def read_graph_file(file_path: str):
    result_graph = None
    with open(file_path, "r") as file:
        edges = []
        num_edges = 0
        for line in file:
            line = line.rstrip()
            if line[0] == "e":
                start, finish = [int(number) for number in line[2:].split(" ")]
                edges.append((start, finish))
            elif line[0] == "p":
                _, __, num_vertices, num_edges = re.split(r"\s+", line)
                _, num_edges = int(num_vertices), int(num_edges)
            else:
                pass
        if len(edges) != num_edges:
            raise
        result_graph = nx.Graph(edges)
    return result_graph


def run():
    filenames = [
        # Easy graphs
        "johnson16-2-4.clq", "johnson8-2-4.clq", "johnson8-4-4.clq",
        "MANN_a9.clq", "keller4.clq",
        "c-fat200-1.clq", "c-fat200-2.clq", "c-fat200-5.clq", "c-fat500-1.clq", "c-fat500-10.clq", "c-fat500-2.clq",
        "c-fat500-5.clq",
        "hamming6-2.clq", "hamming6-4.clq", "hamming8-2.clq", "hamming8-4.clq",
        "MANN_a9.clq",
        "gen200_p0.9_55.clq",
        "san200_0.7_1.clq", "san200_0.9_1.clq", "san200_0.9_2.clq",

        # Hard graphs
        "C125.9.clq", "gen200_p0.9_44.clq", "keller4.clq",
        "MANN_a27.clq", "MANN_a45.clq",
        "p_hat300-1.clq", "p_hat300-2.clq", "p_hat300-3.clq",
        "san200_0.7_2.clq", "san200_0.9_3.clq",
        "brock200_2.clq", "brock200_3.clq", "brock200_4.clq", "brock200_1.clq",
        "sanr200_0.7.clq"

    ]
    times, set_weights, sets = [], [], []
    with open("report.txt", "w") as report_file:
        for filename in filenames:
            graph = read_graph_file("../clique_graphs/" + filename)
            num_nodes = graph.number_of_nodes()
            weights = [np.ceil(10 * i / num_nodes) * 0.1 for i in range(1, num_nodes + 1)]
            start = time()
            res, weight = find_maximal_weighted_set(graph, weights)
            end = time()
            time_sec = round(end - start, 3)
            log_info = f"{filename}: weight - {weight}, time - {time_sec} "
            print(log_info)
            report_file.write(log_info)
            times.append(time_sec)
            set_weights.append(weight)
            sets.append(res)

    df = DataFrame({'Instance': filenames, 'Time, sec': times, "Weights": set_weights, "Set": sets})
    df.to_excel('report.xlsx', sheet_name='Weighted sets', index=False)


if __name__ == "__main__":
    run()
