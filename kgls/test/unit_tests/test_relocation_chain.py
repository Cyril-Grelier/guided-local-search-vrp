
from kgls.local_search.operator_relocation_chain import search_relocation_chains
from kgls.datastructure import Node, Route, VRPProblem, CostEvaluator


def test_search_relocation_chains():

    def build_problem() -> tuple[VRPProblem, CostEvaluator]:
        depot1 = Node(0, 0, 0, 0, True)
        depot2 = Node(7, 100, 0, 0, True)
        customers = [
            Node(1, 0, 10, 1),
            Node(2, 0, 20, 1),
            Node(3, 0, 30, 1),
            Node(4, 100, 10, 1),
            Node(5, 100, 20, 1),
            Node(6, 100, 20, 1),
        ]
        vrp_problem = VRPProblem([depot1] + customers + [depot2], 3)
        vrp_evaluator = CostEvaluator([depot1] + customers + [depot2], 3)

        return vrp_problem, vrp_evaluator

    problem, evaluator = build_problem()
    # optimal routes are D1-1-2-3-D1 and D2-4-5-D2

    # CASE 1: move node4 before node5 and node 3 before node 2
    route1 = Route([
        problem.nodes[0],
        problem.nodes[1],
        problem.nodes[2],
        problem.nodes[4],
        problem.nodes[0]
    ])
    route2 = Route([
        problem.nodes[7],
        problem.nodes[5],
        problem.nodes[3],
        problem.nodes[6],
        problem.nodes[7]
    ])

    relocation_chains: list = search_relocation_chains(
        evaluator,
        [problem.nodes[4]],
        2
    )

    # Assertions
    # Check if valid moves were generated
    assert relocation_chains
    relocations = relocation_chains[0].relocations
    assert relocations[0].node_to_move == problem.nodes[4]
    assert relocations[0].move_after == problem.nodes[7]
    assert relocations[1].node_to_move == problem.nodes[3]
    assert relocations[1].move_after == problem.nodes[1]
    assert relocations[0].improvement == relocations[1].improvement == 180
