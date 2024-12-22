
import logging
import math
import time

from .operator_relocation_chain import search_relocation_chains
from .operator_linkernighan import search_lk_moves
from .operator_3_opt import search_3_opt_moves
from .operator_cross_exchange import search_cross_exchanges
from kgls.datastructure import Node, Route, VRPSolution, CostEvaluator


logger = logging.getLogger(__name__)

# TODO best or first improving move
# TODO execute operator until no better solution found?


def improve_route(
        route: Route,
        solution: VRPSolution,
        cost_evaluator: CostEvaluator
) -> None:
    start = time.time()

    if route.size > 2:
        found_move = True
        while found_move:
            found_move = False
            valid_moves = search_lk_moves(
                solution=solution,
                cost_evaluator=cost_evaluator,
                route=route,
                max_depth=4
            )

            if valid_moves:
                old_costs = cost_evaluator.get_solution_costs(solution)
                best_move = valid_moves[0]
                best_move.execute(solution)

                # validate changes in solution
                new_costs = cost_evaluator.get_solution_costs(solution)
                improvement = old_costs - new_costs
                assert math.isclose(improvement, best_move.improvement), \
                    f'Improvement of LK was {improvement} ' \
                    f'but expected was {best_move.improvement}'
                solution.validate()

                solution.solution_stats['moves_lk'] += 1
                solution.plot(cost_evaluator.get_solution_costs(solution, True))

                found_move = True

    end = time.time()
    solution.solution_stats['route_improvement_time'] += end - start


def get_disjunct_moves(moves: list) -> list:
    disjunct_moves = []
    for move in moves:
        is_disjunct = True
        for disjunct_move in disjunct_moves:
            if not move.is_disjunct(disjunct_move):
                is_disjunct = False
                break

        if is_disjunct:
            disjunct_moves.append(move)

    return disjunct_moves


def find_best_improving_moves(
        solution: VRPSolution,
        cost_evaluator: CostEvaluator,
        start_nodes: list[Node],
        intra_route_opt: bool,
        operator_name: str,
        **kwargs
) -> tuple[int, set[Route]]:

    operators = {
        "relocation_chain": search_relocation_chains,
        "segment_move": search_3_opt_moves,
        "cross_exchange": search_cross_exchanges,
    }

    if operator_name not in operators:
        raise ValueError(f"Operator '{operator_name}' is not defined")

    start = time.time()

    candidate_moves = operators[operator_name](
        solution=solution,
        cost_evaluator=cost_evaluator,
        start_nodes=start_nodes,
        **kwargs)

    end = time.time()
    solution.solution_stats[f'move_time_{operator_name}'] += end - start

    if candidate_moves:
        # find all disjunct moves, sorted by steepest descent
        logger.debug(
            f'Found {len(candidate_moves)} improving moves, '
            f'current solution value: {cost_evaluator.get_solution_costs(solution)}'
        )
        # candidate_moves = sorted(candidate_moves)
        changed_routes = set()
        disjunct_moves = get_disjunct_moves(candidate_moves)

        # execute the moves
        for move in disjunct_moves:
            changed_routes = changed_routes | move.get_routes()
            old_costs = cost_evaluator.get_solution_costs(solution)

            move.execute(solution)
            solution.solution_stats[f'move_count_{operator_name}'] += 1
            solution.plot(cost_evaluator.get_solution_costs(solution, True))

            # validate changes in solution
            new_costs = cost_evaluator.get_solution_costs(solution)
            improvement = old_costs - new_costs
            assert math.isclose(improvement, move.improvement), \
                f'Improvement of move {operator_name} was {improvement} ' \
                f'but expected was {move.improvement}'
            solution.validate()

        # optimize all changed routes
        if intra_route_opt:
            for route in changed_routes:
                improve_route(route, solution, cost_evaluator)

        return len(disjunct_moves), changed_routes

    else:
        return 0, set()


def local_search(
        solution: VRPSolution,
        cost_evaluator: CostEvaluator,
        start_from_nodes: set[Node],
        intra_route_opt: bool
) -> tuple[int, set[Route]]:
    found_moves_segment, changed_routes_segment = find_best_improving_moves(
        solution=solution,
        cost_evaluator=cost_evaluator,
        start_nodes=start_from_nodes,
        intra_route_opt=intra_route_opt,
        operator_name="segment_move",
    )

    found_moves_cross, changed_routes_cross = find_best_improving_moves(
        solution=solution,
        cost_evaluator=cost_evaluator,
        start_nodes=start_from_nodes,
        intra_route_opt=intra_route_opt,
        operator_name="cross_exchange",
    )

    found_moves_rc, changed_routes_rc = find_best_improving_moves(
        solution=solution,
        cost_evaluator=cost_evaluator,
        start_nodes=start_from_nodes,
        intra_route_opt=intra_route_opt,
        operator_name="relocation_chain",
        max_depth=3
    )
    found_moves = found_moves_segment + found_moves_cross + found_moves_rc
    changed_routes = changed_routes_segment | changed_routes_cross | changed_routes_rc

    return found_moves, changed_routes


def improve_solution(
        solution: VRPSolution,
        cost_evaluator: CostEvaluator,
        start_search_from_routes: set[Route]
):
    # intra-route optimization of routes
    for route in start_search_from_routes:
        improve_route(route, solution, cost_evaluator)

    # inter-route optimization, starting from all routes in 'start_search_from_routes'
    start_from_nodes = set()
    for route in start_search_from_routes:
        start_from_nodes.update(route.customers)
    changes_found = True

    while changes_found:
        executed_moves, _ = local_search(solution, cost_evaluator, start_from_nodes, True)
        changes_found = executed_moves > 0


def perturbate_solution(solution: VRPSolution, cost_evaluator: CostEvaluator) -> set[Route]:
    start = time.time()
    logger.debug('Starting perturbation of solution')

    # add previous penalties to costs of edges and compute the badness of the edges of the current solution
    cost_evaluator.enable_penalization()
    cost_evaluator.determine_edge_badness(solution.routes)

    applied_changes: int = 0
    changed_routes_perturbation = set()

    while applied_changes < 3:
        worst_edge = cost_evaluator.get_and_penalize_worst_edge()
        logger.debug(f'Penalizing edge({worst_edge.get_first_node()} - {worst_edge.get_second_node()})')
        start_from_nodes = [node for node in worst_edge.nodes if not node.is_depot]

        executed_moves, changed_routes = local_search(solution, cost_evaluator, start_from_nodes, False)

        applied_changes += executed_moves
        changed_routes_perturbation.update(changed_routes)

    cost_evaluator.disable_penalization()

    end = time.time()
    solution.solution_stats['perturbation_time'] += end - start

    return changed_routes_perturbation
