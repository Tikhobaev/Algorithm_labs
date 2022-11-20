import cplex
import networkx as nx


class ProblemHandler:
    STRATEGIES = [
        nx.coloring.strategy_largest_first,
        nx.coloring.strategy_random_sequential,
        nx.coloring.strategy_independent_set,
        nx.coloring.strategy_connected_sequential_bfs,
        nx.coloring.strategy_saturation_largest_first,
    ]

    def __init__(self, graph: nx.Graph, is_integer: bool = False):
        self.model: cplex.Cplex = None
        self.graph: nx.Graph = graph
        self.is_integer = is_integer
        return

    def design_problem(self):
        self.model = cplex.Cplex()
        self.model.set_log_stream(None)
        self.model.set_results_stream(None)
        self.model.set_warning_stream(None)
        self.model.set_error_stream(None)
        self.model.objective.set_sense(self.model.objective.sense.maximize)

        nodes = sorted(self.graph.nodes())
        n_vars = self.graph.number_of_nodes()
        constraints = self._create_constraints()
        n_constraints = len(constraints)

        obj = [1.0] * n_vars
        upper_bounds = [1.0] * n_vars
        lower_bounds = [0.0] * n_vars
        var_names = [f'x{i}' for i in nodes]
        constraint_names = [f'c{i + 1}' for i in range(n_constraints)]
        constraint_senses = ['L'] * n_constraints
        right_hand_side = [1.0] * n_constraints

        self.model.variables.add(obj=obj, names=var_names, ub=upper_bounds, lb=lower_bounds)
        self.model.linear_constraints.add(lin_expr=constraints, senses=constraint_senses,
                                          rhs=right_hand_side, names=constraint_names)

    def _create_constraints(self):
        non_edges = list(nx.non_edges(self.graph))
        independent_sets = self._get_independent_sets(self.graph)

        # Remove not connected edges which are included in ind set to avoid redundant constraints
        not_connected = []
        for pair in non_edges:
            already_included = False
            for ind_set in independent_sets:
                if pair[0] in ind_set and pair[1] in ind_set:
                    already_included = True
                    break
            if not already_included:
                not_connected.append(pair)

        constraints = []
        for ind_set in independent_sets:
            constraints.append([[f'x{i}' for i in ind_set], [1.0] * len(ind_set)])
        for node_i, node_j in not_connected:
            constraints.append([[f'x{node_i}', f'x{node_j}'], [1.0, 1.0]])
        return constraints

    def _get_independent_sets(self, graph: nx.Graph) -> list:
        strategies = [
            nx.coloring.strategy_largest_first,
            nx.coloring.strategy_random_sequential,
            nx.coloring.strategy_independent_set,
            nx.coloring.strategy_connected_sequential_bfs,
            nx.coloring.strategy_saturation_largest_first,
        ]
        independent_sets = set()
        for strategy in strategies:
            if strategy == nx.coloring.strategy_random_sequential:
                self._color_n_times(independent_sets, graph, strategy)
            else:
                coloring_dct = nx.coloring.greedy_color(graph, strategy)
                color2nodes = dict()
                for node, color in coloring_dct.items():
                    if color not in color2nodes:
                        color2nodes[color] = []
                    color2nodes[color].append(node)
                for color, colored_nodes in color2nodes.items():
                    if len(colored_nodes) >= 3:
                        # Will not add ind sets that are just 2 not connected vertices
                        colored_nodes = tuple(sorted(colored_nodes))
                        independent_sets.add(colored_nodes)
        independent_sets = [set(ind_set) for ind_set in independent_sets]
        return independent_sets

    @staticmethod
    def _color_n_times(independent_sets, graph, strategy):
        for _ in range(40):
            coloring_dct = nx.coloring.greedy_color(graph, strategy)
            color2nodes = dict()
            for node, color in coloring_dct.items():
                if color not in color2nodes:
                    color2nodes[color] = []
                color2nodes[color].append(node)
            for color, colored_nodes in color2nodes.items():
                if len(colored_nodes) >= 3:
                    # Will not add ind sets that are just 2 not connected vertices
                    colored_nodes = tuple(sorted(colored_nodes))
                    independent_sets.add(colored_nodes)
