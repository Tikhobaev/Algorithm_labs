import copy
import re
import random
from time import time
from pandas import DataFrame


class MaxCliqueProblem:
    def __init__(self):
        self.neighbour_sets = []
        self.maxColor = 0
        self.colors = []
        self.best_clique = []

    def read_graph_from_file(self, filename):
        with open("../clique_graphs/" + filename, "r") as file:
            for line in file:
                line = line.rstrip()
                if line[0] == "e":
                    start, finish = [int(number) for number in line[2:].split(" ")]
                    self.neighbour_sets[start - 1].add(finish - 1)
                    self.neighbour_sets[finish - 1].add(start - 1)
                elif line[0] == "p":
                    _, __, vertices, edges = re.split(r"\s+", line)
                    vertices, edges = int(vertices), int(edges)
                    # vertices, edges = [int(number) for number in line.split(" ")[2:]]
                    self.neighbour_sets = [set() for _ in range(vertices)]
                    self.colors = [0] * vertices

    def find_clique(self, first_iter=True, candidates=None, clique=None):
        clique = []
        max_iter = 10
        randomization = 4
        for i in range(randomization):
            for _ in range(max_iter):
                self._find_clique(i)
                if len(self.get_clique()) > len(clique):
                    clique = copy.deepcopy(self.get_clique())
        self.best_clique = clique

    def _find_clique(self, randomization=None, first_iter=True, candidates=None, clique=None):
        if not first_iter and len(candidates) == 1:
            clique.append(candidates[0][0])
            return

        # calculate new degrees
        if first_iter:
            candidates = [(i, len(self.neighbour_sets[i])) for i in range(len(self.neighbour_sets))]
            candidates.sort(key=lambda tup: tup[1], reverse=True)
            clique = []
        else:
            remaining_vertex_numbers = {vertex: True for vertex, degree in candidates}
            for i, (vertex, degree) in enumerate(candidates):
                degree = 0
                for neighbour in self.neighbour_sets[vertex]:
                    if neighbour in remaining_vertex_numbers:
                        degree += 1
                candidates[i] = (vertex, degree)
            candidates.sort(key=lambda tup: tup[1], reverse=True)

        # remove mins
        min_degree = candidates[-1][1]
        index = 0
        for i, (vertex, degree) in enumerate(candidates[::-1]):
            if degree == min_degree:
                index = i
            else:
                break
        removed = candidates[-1 - index::]
        remaining = candidates[:len(candidates) - index - 1]

        # call recursive
        if len(remaining):
            self._find_clique(randomization, False, remaining, clique)

        # add vertexes to clique
        current = removed[random.randint(0, randomization) % len(removed)][0]
        all_connected = True
        for vertex in clique:
            if current not in self.neighbour_sets[vertex]:
                all_connected = False
        if all_connected:
            clique.append(current)

        for i in range(len(removed)):
            current = removed[i][0]
            all_connected = True
            for vertex in clique:
                if current != vertex and current not in self.neighbour_sets[vertex]:
                    all_connected = False
            if all_connected and current not in clique:
                clique.append(current)

        if first_iter:
            self.best_clique = clique

    def check(self):
        if len(set(self.best_clique)) != len(self.best_clique):
            print("Duplicated vertices in the clique")
            return False
        for vertex_i in self.best_clique:
            for vertex_j in self.best_clique:
                if vertex_i != vertex_j and vertex_j not in self.neighbour_sets[vertex_i]:
                    print("Returned subgraph is not a clique")
                    return False
        return True

    def get_clique(self):
        return self.best_clique


def run():
    filenames = ["brock200_1.clq", "brock200_2.clq", "brock200_3.clq", "brock200_4.clq",
                 "brock400_1.clq", "brock400_2.clq", "brock400_3.clq", "brock400_4.clq",
                 "C125.9.clq", "gen200_p0.9_44.clq", "gen200_p0.9_55.clq", "hamming8-4.clq", "johnson16-2-4.clq", "johnson8-2-4.clq",
                 "keller4.clq", "MANN_a27.clq", "MANN_a9.clq", "p_hat1000-1.clq", "p_hat1000-2.clq", "p_hat1500-1.clq",
                 "p_hat300-3.clq", "p_hat500-3.clq", "san1000.clq", "sanr200_0.9.clq", "sanr400_0.7.clq"
                 ]
    times, clique_sizes, cliques = [], [], []
    with open("report.txt", "w") as report_file:
        for filename in filenames:
            mcp = MaxCliqueProblem()
            mcp.read_graph_from_file(filename)
            start = time()
            mcp.find_clique()
            end = time()
            if not mcp.check():
                error = "Error: incorrect coloring!!!"
                print(error)
                report_file.write(error)
            time_sec = round(end - start, 3)
            log_info = f"{filename}: clique size - {len(mcp.get_clique())}, time - {time_sec} "
            print(log_info)
            report_file.write(log_info)
            report_file.write(str(mcp.get_clique()))
            report_file.write("\n")

            times.append(time_sec)
            clique_sizes.append(len(mcp.get_clique()))
            cliques.append(mcp.get_clique())

    df = DataFrame({'Instance': filenames, 'Time, sec': times, "Clique size": clique_sizes, "Clique vertices": cliques})
    df.to_excel('report.xlsx', sheet_name='Clique', index=False)


if __name__ == "__main__":
    run()
