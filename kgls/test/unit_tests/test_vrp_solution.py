from datastructure import Node, VRPProblem, Route, VRPSolution


def test_insert_nodes_after():
    depot = Node(0, 0, 0, 0, True)
    customers = [
        Node(1, 0, 0, 1),
        Node(2, 0, 0, 1),
        Node(3, 0, 0, 1),
        Node(4, 0, 0, 1),
    ]
    nodes = [depot] + customers
    problem = VRPProblem(nodes, 5)
    route = Route([depot] + customers[:2] + [depot])

    solution = VRPSolution(problem, [route])
    solution.insert_nodes_after(customers[2:], customers[0])

    solution.routes[0].validate()
    assert solution.routes[0].print() == "0-1-3-4-2-0"


def test_remove_nodes():
    depot = Node(0, 0, 0, 0, True)
    customers = [
        Node(1, 0, 0, 1),
        Node(2, 0, 0, 1),
        Node(3, 0, 0, 1),
        Node(4, 0, 0, 1),
    ]
    nodes = [depot] + customers
    problem = VRPProblem(nodes, 5)
    route = Route([depot] + customers + [depot])

    solution = VRPSolution(problem, [route])
    solution.remove_nodes(customers[1:3][::-1])

    solution.routes[0].validate()
    assert solution.routes[0].print() == "0-1-4-0"

    solution.remove_nodes([customers[0]])

    solution.routes[0].validate()
    assert solution.routes[0].print() == "0-4-0"
