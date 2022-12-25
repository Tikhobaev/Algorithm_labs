import cplex
import time
from math import isclose
import numpy as np
import networkx as nx

from problem import ProblemHandler
from separator import find_maximal_weighted_set


class BnCTimeoutException(Exception):
    pass


class BranchAndCut:
    def __init__(self, problem: ProblemHandler, initial_obj_value: float, initial_solution: list, graph: nx.Graph,
                 abs_tol: float = 1e-4, time_limit: int = None):
        self.call_counter = 0
        self.problem = problem
        self.best_obj_value = initial_obj_value
        self.best_solution = initial_solution
        self.abs_tol = abs_tol
        self.start_time = None
        self.time_limit = time_limit
        self.sep_iter = 0
        self.max_sep_iter = 1000
        self.sep_tol = 0.15
        self.max_stagnation_count = 10
        self.graph = graph
        self.max_recursion_depth = 100
        self.constrained_vars = np.zeros(self.graph.number_of_nodes(), dtype=np.bool)

    def run(self, recursion_depth=0):
        self.call_counter += 1
        if self.call_counter == 1:
            self.start_time = time.time()
        if time.time() - self.start_time > self.time_limit:
            print(f"Stopped by timeout {self.time_limit}s")
            raise BnCTimeoutException
        if recursion_depth > self.max_recursion_depth:
            return

        try:
            self.problem.model.solve()
        except cplex.exceptions.CplexSolverError as error:
            print(error)
            return
        current_obj_value = self.problem.model.solution.get_objective_value()

        if int(current_obj_value + self.abs_tol) <= self.best_obj_value:
            return
        current_solution = self.problem.model.solution.get_values()

        if self.is_all_integer(current_solution, abs_tol=self.abs_tol):
            clique_nodes = self._get_clique(current_solution)
            # This check is redundant, but just not to ruin hours of calculations...
            is_clique = self.is_clique(self.problem.graph, clique_nodes)
            if not is_clique:
                return
            print(f'Found better clique: {round(current_obj_value)}')
            self.best_solution = current_solution
            self.best_obj_value = round(current_obj_value)
            return

        if self.call_counter % 100 == 0:
            slacks = self.problem.model.solution.get_linear_slacks()
            constraint_names = self.problem.model.linear_constraints.get_names()
            for i, slack in enumerate(slacks):
                if slack > 1e-3:
                    name = constraint_names[i]
                    if 'Branch' not in name:
                        self.problem.model.linear_constraints.delete(name)

        # SEPARATION
        stagnation_count = 0
        obj_value_history = list()
        for sep_iter in range(self.max_sep_iter):
            # Constraint
            ind_set, weight_total = find_maximal_weighted_set(self.graph, current_solution)

            if weight_total <= 1.0 + self.abs_tol:
                break
            self.problem.model.linear_constraints.add(
                lin_expr=[[[f'x{v}' for v in ind_set], [1.0] * len(ind_set)]],
                senses=['L'],
                rhs=[1.0],
                names=[f'Strong_{self.sep_iter}']
            )
            self.sep_iter += 1

            # Solve
            try:
                self.problem.model.solve()
            except cplex.exceptions.CplexSolverError as error:
                print(error)
                return
            current_obj_value = self.problem.model.solution.get_objective_value()
            if int(current_obj_value + self.abs_tol) <= self.best_obj_value:
                return

            if current_obj_value is None:
                return
            if int(current_obj_value + self.abs_tol) <= self.best_obj_value:
                return

            # Check how many stagnating iterations
            if len(obj_value_history) > 0:
                if isclose(obj_value_history[-1], current_obj_value, abs_tol=1e-2):
                    break
                if (obj_value_history[-1] - current_obj_value) < self.sep_tol:
                    stagnation_count += 1
                else:
                    stagnation_count = 0
                if stagnation_count > self.max_stagnation_count:
                    break
            obj_value_history.append(current_obj_value)
            current_solution = self.problem.model.solution.get_values()

        # BRANCHING
        branching_var_index = self.choose_branch(current_solution)
        if branching_var_index is None:
            weak_constraints = self.check_solution(current_solution)
            if weak_constraints is not None:
                for itr, pair in enumerate(weak_constraints):
                    var_names = [f'x{i}' for i in pair]
                    constraint = [var_names, [1.0] * len(var_names)]
                    self.problem.model.linear_constraints.add(
                        lin_expr=[constraint],
                        senses=['L'],
                        rhs=[1.0],
                        names=[f'Weak{self.call_counter}_{itr}']
                    )
                # print("Weak branching")
                self.run(recursion_depth + 1)
            else:
                print(f'\t\t\tFound new best: {current_obj_value}')
                self.best_solution = current_solution
                self.best_obj_value = round(current_obj_value)
                return
        else:
            branching_var_name = f'x{branching_var_index + 1}'
            rounded_value = round(current_solution[branching_var_index])
            for branch_value in [rounded_value, 1 - round(rounded_value)]:
                constraint_name = f'Branch{self.call_counter}_{branch_value}_{branching_var_name}'
                constraint = [[branching_var_name], [1.0]]
                index = self.problem.model.linear_constraints.add(
                    lin_expr=[constraint], senses=['E'], rhs=[branch_value], names=[constraint_name]
                )
                self.constrained_vars[branching_var_index] = True
                self.run(recursion_depth + 1)
                self.constrained_vars[branching_var_index] = False
                self.problem.model.linear_constraints.delete(constraint_name)

    def is_clique(self, graph, nodes):
        subgraph = graph.subgraph(nodes)
        num_of_nodes = subgraph.number_of_nodes()
        num_of_edges = subgraph.number_of_edges()
        num_of_edges_complete = int(num_of_nodes * (num_of_nodes - 1) / 2)
        if num_of_edges == num_of_edges_complete:
            return True
        return False

    def _get_clique(self, solution: list) -> list:
        return [var_index + 1 for var_index, var in enumerate(solution) if isclose(var, 1, abs_tol=self.abs_tol)]

    def get_best_clique(self) -> list:
        return self._get_clique(self.best_solution)

    def choose_branch(self, solution: list) -> int:
        selected_var_index = None
        min_diff_to_int = 2
        for _index, value in enumerate(solution):
            if not self.constrained_vars[_index]:
                if not (isclose(value, 0) or isclose(value, 1)):
                    diff_to_int = abs(1 - value)
                    if diff_to_int <= min_diff_to_int:
                        min_diff_to_int = diff_to_int
                        selected_var_index = _index
        return selected_var_index

    def check_solution(self, solution: list) -> list:
        clique_nodes = self._get_clique(solution)
        is_clique = self.is_clique(self.problem.graph, clique_nodes)
        if is_clique:
            return None
        else:
            complement_g = nx.complement(self.problem.graph.subgraph(clique_nodes))
            return list(filter(lambda pair: pair[0] != pair[1], complement_g.edges()))

    @staticmethod
    def is_all_integer(variables: list, abs_tol: float = 1e-4) -> bool:
        for var in variables:
            if not (isclose(var, 0, abs_tol=abs_tol) or isclose(var, 1, abs_tol=abs_tol)):
                return False
        return True
