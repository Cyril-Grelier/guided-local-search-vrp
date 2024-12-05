
from kgls.local_search.operator_linkernighan import search_lk_moves
from kgls.datastructure import Node, Route, VRPProblem, CostEvaluator


def build_problem() -> tuple[VRPProblem, CostEvaluator]:
    depot = Node(0, 0, 0, 0, True)
    customers = [
        Node(1, 10, 0, 1),
        Node(2, 20, 0, 1),
        Node(3, 30, 0, 1),
        Node(4, 40, 0, 1),
    ]
    vrp_problem = VRPProblem([depot] + customers, 5)
    vrp_evaluator = CostEvaluator([depot] + customers, 5)

    return vrp_problem, vrp_evaluator


def test_search_n_opt_moves():

    problem, evaluator = build_problem()
    # optimal route is 0-1-2-3-4-0 with route costs of 80

    # CASE 1: 2-opt
    # 0-2-1-3-4-0 with route costs 100
    # remove (0-2), (1-3) and add (0-1), (2-3)
    route = Route([
        problem.depot,
        problem.nodes[2],
        problem.nodes[1],
        problem.nodes[3],
        problem.nodes[4],
        problem.depot
    ])
    found_moves: list = search_lk_moves(evaluator, route, 2)

    assert found_moves
    best_move = found_moves[0]
    assert best_move.improvement == 20
    assert (problem.nodes[2], problem.depot) in best_move.removed_edges
    assert (problem.nodes[3], problem.nodes[1]) in best_move.removed_edges
    assert (problem.nodes[1], problem.depot) in best_move.new_edges
    assert (problem.nodes[3], problem.nodes[2]) in best_move.new_edges

    # CASE 2: 3-opt
    # 0-3-1-2-4-0 with route costs of 120
    # remove (0-3), (2-4), (3-1) and add (3-2), (4-3), (1-0)
    route = Route([
        problem.depot,
        problem.nodes[3],
        problem.nodes[1],
        problem.nodes[2],
        problem.nodes[4],
        problem.depot
    ])
    found_moves: list = search_lk_moves(evaluator, route, 3)

    assert found_moves
    found_moves = sorted(found_moves)
    best_move = found_moves[0]
    assert best_move.improvement == 40
    assert (problem.nodes[3], problem.nodes[0]) in best_move.removed_edges
    assert (problem.nodes[4], problem.nodes[2]) in best_move.removed_edges
    assert (problem.nodes[3], problem.nodes[1]) in best_move.removed_edges
    assert (problem.nodes[3], problem.nodes[2]) in best_move.new_edges
    assert (problem.nodes[4], problem.nodes[3]) in best_move.new_edges
    assert (problem.nodes[1], problem.nodes[0]) in best_move.new_edges
