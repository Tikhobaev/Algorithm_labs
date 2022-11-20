import cplex
import time
from math import isclose
from problem import ProblemHandler


class BnBTimeoutException(Exception):
    pass


class BranchAndBound:

    def __init__(self, problem: ProblemHandler, initial_obj_value: float, initial_solution: list,
                 abs_tol: float = 1e-4, time_limit: int = None):
        self.call_counter = 0
        self.problem = problem
        self.best_obj_value = initial_obj_value
        self.best_solution = initial_solution
        self.abs_tol = abs_tol
        self.start_time = None
        self.time_limit = time_limit

    def run(self):
        self.call_counter += 1
        if self.call_counter == 1:
            self.start_time = time.time()
        try:
            self.problem.model.solve()
        except cplex.exceptions.CplexSolverError as error:
            print(error)
            return
        current_obj_value = self.problem.model.solution.get_objective_value()

        if int(current_obj_value + self.abs_tol) <= self.best_obj_value:
            return
        current_solution = self.problem.model.solution.get_values()

        # If all variables are integer (= current_obj_value also integer)
        # -> not branching anymore, this is the best solution in nearest area
        if self.is_all_integer(current_solution, abs_tol=self.abs_tol):
            clique_nodes = self._get_clique(current_solution)
            # This check is redundant, but just not to ruin hours of calculations...
            is_clique = self.is_clique(self.problem.graph, clique_nodes)
            if not is_clique:
                print("Error: found solution is not a clique")
                return
            print(f'Found better clique: {round(current_obj_value)}')
            self.best_solution = current_solution
            self.best_obj_value = round(current_obj_value)
            return

        if time.time() - self.start_time > self.time_limit:
            print(f"Stopped by timeout {self.time_limit}s")
            raise BnBTimeoutException

        branching_var_index = self.choose_branch(current_solution)
        if branching_var_index is None:
            return
        branching_var_name = f'x{branching_var_index + 1}'
        rounded_value = round(current_solution[branching_var_index])
        for branch_value in [rounded_value, 1 - round(rounded_value)]:
            constraint = [[branching_var_name], [1.0]]
            index = self.problem.model.linear_constraints.add(lin_expr=[constraint], senses=['E'], rhs=[branch_value])
            self.run()
            self.problem.model.linear_constraints.delete(index)
        return

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
            if not (isclose(value, 0) or isclose(value, 1)):
                diff_to_int = abs(1 - value)
                if diff_to_int <= min_diff_to_int:
                    min_diff_to_int = diff_to_int
                    selected_var_index = _index
        return selected_var_index

    @staticmethod
    def is_all_integer(variables: list, abs_tol: float = 1e-4) -> bool:
        for var in variables:
            if not (isclose(var, 0, abs_tol=abs_tol) or isclose(var, 1, abs_tol=abs_tol)):
                return False
        return True
