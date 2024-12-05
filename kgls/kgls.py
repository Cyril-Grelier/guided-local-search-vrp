import logging
import math
import time

from datastructure import CostEvaluator, VRPProblem, VRPSolution
from interfaces.problem_reader import read_vrp_instance
from local_search import improve_solution, perturbate_solution
from solution_construction import clark_wright_route_reduction
from abortion_condition import BaseAbortionCondition, MaxRuntimeCondition, MaxIterationsCondition, RuntimeWithoutImprovementCondition, IterationsWithoutImprovementCondition

logger = logging.getLogger(__name__)


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

    def __init__(self, path_to_instance_file: str):
        self._vrp_instance = read_vrp_instance(path_to_instance_file)
        self._cost_evaluator = CostEvaluator(self._vrp_instance.nodes, self._vrp_instance.capacity)
        self._best_solution_costs = math.inf
        self._abortion_condition = IterationsWithoutImprovementCondition(100)

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

        self._run_stats.append({
            "time": time.time(),
            "iteration": self._iteration,
            "costs": current_costs,
            "best_costs": self._best_solution_costs,
        })

    def run(self, visualize_progress: bool = False):
        logger.info(f'Running KGLS. {self._abortion_condition.msg}')

        start_time = time.time()
        self._run_stats = []
        self._iteration = 0

        # construct initial solution
        self._cur_solution = clark_wright_route_reduction(
            vrp_instance=self._vrp_instance,
            cost_evaluator=self._cost_evaluator
        )

        if visualize_progress:
            self._cur_solution.start_plotting()

        # TODO solution.copy()
        # TODO class run_stats
        improve_solution(
            solution=self._cur_solution,
            cost_evaluator=self._cost_evaluator,
            start_search_from_routes=self._cur_solution.routes
        )
        self._update_run_stats(start_time)

        while not self._abortion_condition.should_abort(
                iteration=self._iteration,
                best_iteration=self._best_iteration,
                start_time=start_time,
                best_sol_time=self._best_solution_time
        ):
            self._iteration += 1
            logger.info(iter)

            changed_routes = perturbate_solution(
                solution=self._cur_solution,
                cost_evaluator=self._cost_evaluator
            )
            improve_solution(
                solution=self._cur_solution,
                cost_evaluator=self._cost_evaluator,
                start_search_from_routes=changed_routes
            )

            self._update_run_stats(start_time)


    def continue_from_solution(self, path_to_instance_file: str, path_to_solution: str):
        pass
