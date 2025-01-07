import logging
import math
import time
from typing import Any

from .datastructure import CostEvaluator, VRPProblem, VRPSolution
from .read_write.problem_reader import read_vrp_instance
from .read_write.solution_reader import read_vrp_solution
from .local_search import improve_solution, perturbate_solution
from .solution_construction import clark_wright_route_reduction
from .abortion_condition import BaseAbortionCondition, MaxRuntimeCondition, MaxIterationsCondition, \
    RuntimeWithoutImprovementCondition, IterationsWithoutImprovementCondition

logger = logging.getLogger(__name__)

DEFAULT_PARAMETERS = {
    'depth_lin_kernighan': 4,
    'depth_relocation_chain': 3,
    'num_perturbations': 3,
    'neighborhood_size': 20,
    'moves': ['segment_move', 'cross_exchange', 'relocation_chain']
}


class KGLS():
    _abortion_condition: BaseAbortionCondition
    _vrp_instance: VRPProblem
    _cost_evaluator: CostEvaluator
    _best_solution: VRPSolution
    _cur_solution: VRPSolution
    _iteration: int
    _best_solution_costs: int
    _best_iteration: int
    _best_solution_time: int
    _run_stats: list[dict[str, any]]

    def __init__(self, path_to_instance_file: str, **kwargs):
        self.run_parameters = self._get_run_parameters(**kwargs)
        self._vrp_instance = read_vrp_instance(path_to_instance_file)
        self._cost_evaluator = CostEvaluator(self._vrp_instance.nodes, self._vrp_instance.capacity, self.run_parameters)
        self._best_solution_costs = math.inf
        self._cur_solution = None
        self._best_solution = None
        self._abortion_condition = IterationsWithoutImprovementCondition(100)

    def _get_run_parameters(self, **kwargs) -> dict[str, Any]:
        # Check user-provided parameters
        for key, value in kwargs.items():
            if key not in DEFAULT_PARAMETERS:
                raise ValueError(f"Invalid parameter: {key}")

            if key != 'moves' and not isinstance(value, int):
                actual_type = type(value).__name__
                raise TypeError(f"Parameter '{key}' must be of type int, got {actual_type}")

            elif key == 'moves':
                if not isinstance(value, list):
                    actual_type = type(value).__name__
                    raise TypeError(f"Parameter '{key}' must be of type list, got {actual_type}")
                if any(move not in DEFAULT_PARAMETERS["moves"] for move in value):
                    raise ValueError(f'Moves must be in {", ".join(DEFAULT_PARAMETERS["moves"])}')

        # update default parameters
        params = {**DEFAULT_PARAMETERS, **kwargs}
        return params

    @property
    def best_solution(self):
        return self._best_solution

    def best_solution_to_file(self, path_to_file: str):
        self._best_solution.to_file(path_to_file)

    def set_abortion_condition(self, condition_name: str, param: int):
        """
        Set the abortion condition for KGLS.
        :param condition_name: Name of the condition ('iterations_with_improvement', 'max_iterations', 'max_runtime').
        :param params: Parameter for the condition.
        """
        condition_classes = {
            "max_iterations": MaxIterationsCondition,
            "max_runtime": MaxRuntimeCondition,
            "iterations_without_improvement": IterationsWithoutImprovementCondition,
            "runtime_without_improvement": RuntimeWithoutImprovementCondition,
        }
        if condition_name not in condition_classes:
            raise ValueError(
                f"Unknown abortion condition: {condition_name}. "
                f"Choose one of {' ,'.join(condition_classes.keys())}.")
        self._abortion_condition = condition_classes[condition_name](param)

    def _update_run_stats(self, start_time):
        current_costs = self._cost_evaluator.get_solution_costs(self._cur_solution)

        if current_costs < self._best_solution_costs:
            logger.info(
                f'{(time.time() - start_time): 1f} ' \
                f'{100 * (current_costs - self._vrp_instance.bks) / self._vrp_instance.bks: .2f}'
            )
            self._best_iteration = self._iteration
            self._best_solution_time = time.time()
            self._best_solution_costs = current_costs
            self._best_solution = self._cur_solution.copy()

        self._run_stats.append({
            "time": time.time(),
            "iteration": self._iteration,
            "costs": current_costs,
            "best_costs": self._best_solution_costs,
        })

    def run(self, visualize_progress: bool = False, start_solution: VRPSolution = None):
        logger.info(f'Running KGLS. {self._abortion_condition.msg}')

        start_time = time.time()
        self._run_stats = []
        self._iteration = 0

        # construct initial solution
        if start_solution is None:
            self._cur_solution = clark_wright_route_reduction(
                vrp_instance=self._vrp_instance,
                cost_evaluator=self._cost_evaluator
            )
        else:
            self._cur_solution = start_solution

        if visualize_progress:
            self._cur_solution.start_plotting()

        self._update_run_stats(start_time)

        improve_solution(
            solution=self._cur_solution,
            cost_evaluator=self._cost_evaluator,
            start_search_from_routes=self._cur_solution.routes,
            run_parameters=self.run_parameters,
        )
        self._update_run_stats(start_time)

        while not self._abortion_condition.should_abort(
                iteration=self._iteration,
                best_iteration=self._best_iteration,
                start_time=start_time,
                best_sol_time=self._best_solution_time
        ):
            self._iteration += 1

            changed_routes = perturbate_solution(
                solution=self._cur_solution,
                cost_evaluator=self._cost_evaluator,
                run_parameters=self.run_parameters,
            )
            improve_solution(
                solution=self._cur_solution,
                cost_evaluator=self._cost_evaluator,
                start_search_from_routes=changed_routes,
                run_parameters=self.run_parameters,
            )

            self._update_run_stats(start_time)

        logger.info(f'KLGS finished after {(time.time() - start_time): 1f} seconds and '
                    f'{self._iteration} iterations.')

    def print_stats(self):
        for key in sorted(self._cur_solution.solution_stats.keys()):
            print(f"{key}:\t{int(self._cur_solution.solution_stats[key])}")

    def _load_solution(self, path_to_file: str) -> VRPSolution:
        if not self._cur_solution is None:
            raise ValueError(
                'Cannot overwrite current solution with a new one. '
                'Please create a new KGLS instance to start from a solution.'
            )

        solution = read_vrp_solution(path_to_file, self._vrp_instance)
        return solution

    def start_from_solution(self, path_to_file: str, visualize_progress: bool = False):
        logger.info(f'Loading starting solution')
        starting_solution = self._load_solution(path_to_file)

        logger.info(f'Continuing KGLS from specified solution')
        self.run(visualize_progress, starting_solution)
