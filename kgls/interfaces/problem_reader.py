import os

from kgls.datastructure import Node, VRPProblem


def read_vrp_instance(file_path: str) -> VRPProblem:
    nodes = dict()
    capacity = 0

    with open(file_path, 'r') as file:
        section = None
        for line in file:
            line = line.strip()

            if line == '':
                continue

            if line.startswith("CAPACITY"):
                capacity = int(line.split(':')[1].strip())

            elif not line[0].isdigit():
                section = line
                continue

            elif section == "NODE_COORD_SECTION":
                parts = line.split()
                node_id = int(parts[0]) - 1
                x = float(parts[1])
                y = float(parts[2])
                nodes[node_id] = Node(node_id, x, y)

            elif section == "DEMAND_SECTION":
                parts = line.split()
                node_id = int(parts[0].strip()) - 1
                demand = int(parts[1].strip())
                nodes[node_id].set_demand(demand)
                if demand == 0:
                    nodes[node_id].set_depot()

            elif line == "EOF":
                break

        # also try read the best known solution
        sol_file_path = file_path.replace('.vrp', '.sol')
        if os.path.exists(sol_file_path):
            best_solution = read_best_known_solution(sol_file_path)
        else:
            best_solution = float('inf')

    return VRPProblem(
        nodes=list(nodes.values()),
        capacity=capacity,
        bks=best_solution
    )


def read_best_known_solution(file_path: str) -> float:
    cost = float('inf')
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()

            if line.startswith('Cost'):
                parts = line.split()
                cost = int(parts[1].strip())

    return cost
