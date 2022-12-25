import re
from time import time
import networkx as nx
from pandas import DataFrame
from problem import ProblemHandler
from heuristic import MaxCliqueProblem
from branch_and_cut import BranchAndCut, BnCTimeoutException


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


if __name__ == '__main__':
    filenames = [
        # Easy graphs
        "johnson16-2-4.clq", "johnson8-2-4.clq", "johnson8-4-4.clq",
        "MANN_a9.clq",
        "keller4.clq",
        "c-fat200-1.clq", "c-fat200-2.clq", "c-fat200-5.clq", "c-fat500-1.clq", "c-fat500-10.clq", "c-fat500-2.clq", "c-fat500-5.clq",
        "hamming6-2.clq", "hamming6-4.clq", "hamming8-2.clq", "hamming8-4.clq",
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
    heuristic_times, bnc_times, clique_sizes, cliques = [], [], [], []
    time_limit = 7000
    abs_tol = 1e-4
    with open("report.txt", "w") as report_file:
        for filename in filenames:
            filename = "../clique_graphs/" + filename
            print(f'{filename} started...')
            graph = read_graph_file(filename)
            problem_handler = ProblemHandler(graph=graph)
            problem_handler.design_problem()

            # Heuristic from lab 2 is used
            mcp = MaxCliqueProblem()
            mcp.read_graph_from_file(filename)
            start_time = time()
            mcp.find_clique()
            total_time = round(time() - start_time, 3)
            heuristic_times.append(total_time)
            if not mcp.check():
                error = "Error: incorrect clique!!!"
                print(error)
                report_file.write(error)
            heuristic_clique = mcp.get_best_clique()
            heuristic_clique_size = mcp.get_clique_size()
            log_info = f"Heuristic clique size - {heuristic_clique_size}, time - {total_time} "
            print(log_info)

            # Branch and cut
            bnc_algorithm = BranchAndCut(
                problem=problem_handler,
                initial_solution=heuristic_clique,
                graph=graph,
                time_limit=time_limit,
                initial_obj_value=heuristic_clique_size,
                abs_tol=abs_tol
            )
            start_time = time()
            try:
                bnc_algorithm.run()
            except BnCTimeoutException:
                pass
            total_time = round(time() - start_time, 3)
            bnc_times.append(total_time)
            # Check on clique correctness is performed in BnB when best clique is found
            clique_nodes = bnc_algorithm.get_best_clique()
            bnc_clique_size = bnc_algorithm.best_obj_value
            clique_sizes.append(bnc_clique_size)
            cliques.append(clique_nodes)
            print(f"BnC clique size = {bnc_clique_size} in {round(total_time, 3)}s.\n")

    df = DataFrame({
        'Instance': filenames,
        'Time heuristic, sec': heuristic_times,
        'Time BnC, sec': bnc_times,
        'Clique size': clique_sizes,
        'Clique vertices': cliques
    })
    df.to_excel('report.xlsx', sheet_name='BnC', index=False)
