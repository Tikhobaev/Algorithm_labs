from time import time
from pandas import DataFrame


class ColoringProblem:
    def __init__(self):
        self.neighbour_sets = []
        self.colors = []
        self.maxColor = 0

    def read_graph_from_file(self, filename):
        with open("../graphs/" + filename, "r") as file:
            for line in file:
                line = line.rstrip()
                if line[0] == "e":
                    start, finish = [int(number) for number in line[2:].split(" ")]
                    self.neighbour_sets[start - 1].add(finish -1)
                    self.neighbour_sets[finish - 1].add(start -1)
                elif line[0] == "p":
                    vertices, edges = [int(number) for number in line[7:].split(" ")]
                    self.neighbour_sets = [set() for _ in range(vertices)]
                    self.colors = [0] * vertices

    def greedy_graph_coloring(self, uncolored_vertices=None):
        """ Solves graph coloring problem using greedy heuristic Smallest degree last with remove """
        if uncolored_vertices is None:
            uncolored_vertices = [(i, len(self.neighbour_sets[i])) for i in range(len(self.neighbour_sets))]
            uncolored_vertices.sort(key=lambda tup: tup[1], reverse=True)

        # calculate new degrees
        remaining_vertex_numbers = {vertex: True for vertex, degree in uncolored_vertices}
        for i, (vertex, degree) in enumerate(uncolored_vertices):
            degree = 0
            for neighbour in self.neighbour_sets[vertex]:
                if neighbour in remaining_vertex_numbers:
                    degree += 1
            uncolored_vertices[i] = (vertex, degree)
        uncolored_vertices.sort(key=lambda tup: tup[1], reverse=True)

        # remove mins
        min_degree = uncolored_vertices[-1][1]
        index = 0
        for i, (vertex, degree) in enumerate(uncolored_vertices[::-1]):
            if degree == min_degree:
                index = i
            else:
                break

        removed = uncolored_vertices[-1 - index::]
        remaining = uncolored_vertices[:len(uncolored_vertices) - index - 1]

        # call recursive
        if len(remaining):
            self.greedy_graph_coloring(remaining)

        # color removed vertices
        for i in range(len(removed)):
            vertex = removed[i][0]
            available_colors = {i: True for i in range(1, self.maxColor + 1)}
            min_color = self.maxColor + 1
            for neighbour in self.neighbour_sets[vertex]:
                available_colors[self.colors[neighbour]] = False

            for color, value in available_colors.items():
                if value and color != 0:
                    min_color = color
                    break
            if min_color == self.maxColor + 1:
                self.maxColor += 1
            self.colors[vertex] = min_color

    def check(self):
        for i, neighbours in enumerate(self.neighbour_sets):
            if self.colors[i] == 0:
                print(f"Vertex {i + 1} is not colored")
                return False
            for neighbour in neighbours:
                if self.colors[neighbour] == self.colors[i]:
                    print(f"Neighbour vertices {i + 1}, {neighbour + 1} have the same color")
                    return False
        return True

    def number_of_colors(self):
        return self.maxColor

    def get_colors(self):
        return self.colors


def run():
    filenames = ["myciel3.col", "myciel7.col", "latin_square_10.col", "school1.col", "school1_nsh.col",
                 "mulsol.i.1.col", "inithx.i.1.col", "anna.col", "huck.col", "jean.col", "miles1000.col",
                 "miles1500.col", "fpsol2.i.1.col", "le450_5a.col", "le450_15b.col", "le450_25a.col",
                 "games120.col", "queen11_11.col", "queen5_5.col"]
    times, color_nums, color_groups = [], [], []
    with open("report.txt", "w") as report_file:
        for filename in filenames:
            gp = ColoringProblem()
            gp.read_graph_from_file(filename)
            start = time()
            gp.greedy_graph_coloring()
            end = time()
            if not gp.check():
                error = "Error: incorrect coloring!!!"
                print(error)
                report_file.write(error)
            time_sec = round(end - start, 3)
            log_info = f"{filename}: num colors - {gp.number_of_colors()}, time - {time_sec} "
            print(log_info)
            report_file.write(log_info)
            color_classes = {color: [] for color in range(1, gp.number_of_colors() + 1)}
            colors = gp.get_colors()
            for i, color in enumerate(colors, start=1):
                color_classes[color].append(i)
            report_file.write(str(list(color_classes.values())))
            report_file.write("\n")

            times.append(time_sec)
            color_nums.append(gp.number_of_colors())
            color_groups.append(list(color_classes.values()))

    df = DataFrame({'Instance': filenames, 'Time, sec': times, "Colors": color_nums, "Color classes": color_groups})
    df.to_excel('report.xlsx', sheet_name='Coloring', index=False)


if __name__ == "__main__":
    run()
