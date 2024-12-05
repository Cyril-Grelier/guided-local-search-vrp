
from datastructure import Node, VRPProblem, CostEvaluator
from solution_construction.savings_algorithm import compute_savings, compute_weighted_savings, clark_wright_parallel


def test_compute_savings():
    depot = Node(0, 0, 0, 0, True)
    customers = [
        Node(1, 0, 10, 1),
        Node(2, 0, 20, 1)
    ]
    nodes = [depot] + customers

    evaluator = CostEvaluator(nodes, 3)

    savings = compute_savings(customers, depot, evaluator)

    assert len(savings) == 1, 'Symmetric savings can be ommited'
    assert savings[0].saving == 20


def test_clark_wright_parallel():
    depot = Node(0, 0, 0, 0, True)
    customers = [
        Node(1, 0, 10, 1),
        Node(2, 0, 10, 1),
        Node(3, 10, 0, 1),
        Node(4, 10, 0, 1),
    ]
    nodes = [depot] + customers
    problem = VRPProblem(nodes, 5)
    evaluator = CostEvaluator(nodes, 5)

    solution = clark_wright_parallel(problem, evaluator)

    # Node1 and Node2 are on the same location and are connected first.
    # Then Node3 and Node 4 for the same reason. Finally, Node1 is merged with Node3.
    # Since Node1 is the first node in the route, Node3 is inserted before it
    # resulting in the route 0-4-3-1-2-0
    assert len(solution.routes) == 1
    assert solution.routes[0].print() == "0-4-3-1-2-0"


def test_compute_weighted_savings():
    depot = Node(0, 0, 0, 0, True)
    customers = [
        Node(1, 0, 10, 1),
        Node(2, 0, 10, 2),
        Node(3, 0, 10, 3)
    ]
    nodes = [depot] + customers
    evaluator = CostEvaluator(nodes, 5)

    savings = compute_weighted_savings(customers, depot, evaluator)

    assert len(savings) == 3, 'Symmetric savings can be ommited'
    # nodes with higher demands have higher savings
    assert savings[0].saving == 2.0  # Node2 to Node3
    assert savings[1].saving == 1.8  # Node1 to Node3
    assert savings[2].saving == 1.6  # Node1 to Node3
