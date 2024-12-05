
from kgls.local_search.operator_3_opt import search_3_opt_moves_from
from kgls.datastructure import Node, Route, VRPProblem, CostEvaluator


def build_problem() -> tuple[VRPProblem, CostEvaluator]:
    depot1 = Node(0, 0, 0, 0, True)
    depot2 = Node(6, 100, 0, 0, True)
    customers = [
        Node(1, 0, 10, 1),
        Node(2, 0, 20, 1),
        Node(3, 0, 30, 1),
        Node(4, 100, 10, 1),
        Node(5, 100, 20, 1),
    ]
    vrp_problem = VRPProblem([depot1] + customers + [depot2], 3)
    vrp_evaluator = CostEvaluator([depot1] + customers + [depot2], 3)

    return vrp_problem, vrp_evaluator


def test_search_3_opt_moves_from():

    problem, evaluator = build_problem()
    # optimal routes are D1-1-2-3-D1 and D2-4-5-D2

    # CASE 1: move node 4 into
    route1 = Route([
        problem.nodes[0],
        problem.nodes[1],
        problem.nodes[2],
        problem.nodes[3],
        problem.nodes[4],
        problem.nodes[0]
    ])
    route2 = Route([
        problem.nodes[6],
        problem.nodes[5],
        problem.nodes[6]
    ])

    found_moves: list = search_3_opt_moves_from(evaluator, problem.nodes[4])

    assert found_moves
    best_move = sorted(found_moves)[0]
    assert best_move.improvement == 172
    assert best_move.segment == [problem.nodes[4]]

    # CASE 2: exchange [2,3] and [4]
    route1 = Route([
        problem.nodes[0],
        problem.nodes[1],
        problem.nodes[0]
    ])
    route2 = Route([
        problem.nodes[6],
        problem.nodes[2],
        problem.nodes[3],
        problem.nodes[4],
        problem.nodes[5],
        problem.nodes[6]
    ])

    found_moves: list = search_3_opt_moves_from(evaluator, problem.nodes[2])

    assert found_moves
    best_move = sorted(found_moves)[0]
    assert best_move.segment == [problem.nodes[3], problem.nodes[2]]
