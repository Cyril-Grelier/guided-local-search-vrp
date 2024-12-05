import logging
from itertools import combinations
import math
from typing import List

from datastructure.cost_evaluator import CostEvaluator
from kgls.datastructure.node import Node
from kgls.datastructure.vrp_problem import VRPProblem
from kgls.datastructure.vrp_solution import VRPSolution

logger = logging.getLogger(__name__)


class Saving:
    def __init__(self, from_node, to_node, saving):
        self.from_node = from_node
        self.to_node = to_node
        self.saving = saving

    def __lt__(self, other):
        return self.saving > other.saving


def compute_savings(
        customers: List[Node],
        depot: Node,
        cost_evaluator: CostEvaluator
) -> list[Saving]:
    savings_list = []

    for node_1, node_2 in combinations(customers, 2):
        saving = (
            cost_evaluator.get_distance(node_1, depot)
            + cost_evaluator.get_distance(node_2, depot)
            - cost_evaluator.get_distance(node_1, node_2)
        )

        savings_list.append(
            Saving(node_1, node_2, saving)
        )

    return sorted(savings_list)


def compute_weighted_savings(
        customers: List[Node],
        depot: Node,
        cost_evaluator: CostEvaluator
) -> list[Saving]:

    savings_list = compute_savings(customers, depot, cost_evaluator)

    max_saving = sorted([_s.saving for _s in savings_list])[-1]
    max_demand = sorted([_n.demand for _n in customers])[-1] + sorted([_n.demand for _n in customers])[-2]

    weighted_savings_list = []
    for node_1, node_2 in combinations(customers, 2):
        saving = (
                cost_evaluator.get_distance(node_1, depot)
                + cost_evaluator.get_distance(node_2, depot)
                - cost_evaluator.get_distance(node_1, node_2)
        )
        saving = saving / max_saving + (node_1.demand + node_2.demand) / max_demand

        weighted_savings_list.append(
            Saving(node_1, node_2, saving)
        )

    return sorted(weighted_savings_list)


def clark_wright_parallel(
        vrp_instance: VRPProblem,
        cost_evaluator: CostEvaluator,
        demand_weighted: bool = False,
        visualize_progess: bool = False
) -> VRPSolution:

    if demand_weighted:
        savings_list = compute_weighted_savings(vrp_instance.customers, vrp_instance.depot, cost_evaluator)
    else:
        savings_list = compute_savings(vrp_instance.customers, vrp_instance.depot, cost_evaluator)

    not_planned = vrp_instance.customers.copy()  # Nodes not yet planned
    can_be_extended: list[Node] = []  # Nodes planned at the start or end of a route
    cannot_be_extended: list[Node] = []  # Nodes planned not at the start or end or a route

    # start with empty solution
    solution = VRPSolution(vrp_instance, [])

    for saving in savings_list:
        node1, node2 = saving.from_node, saving.to_node

        # check whether any of the two nodes cannot be extended
        if node1 in cannot_be_extended or node2 in cannot_be_extended:
            continue

        elif node1 in not_planned and node2 in not_planned:
            if node1.demand + node2.demand <= vrp_instance.capacity:
                # create a new route with node1 and node2
                depot_of_route = vrp_instance.depot.copy()
                solution.add_route(
                    [depot_of_route, node1, node2, depot_of_route]
                )

                not_planned.remove(node1)
                not_planned.remove(node2)
                can_be_extended.append(node1)
                can_be_extended.append(node2)

        elif node1 in can_be_extended and node2 in not_planned:
            if node1.route.volume + node2.demand <= vrp_instance.capacity:
                # add node2 before or after node1
                if node1.prev.is_depot:
                    solution.insert_nodes_after([node2], node1.prev)
                else:
                    solution.insert_nodes_after([node2], node1)

                can_be_extended.remove(node1)
                not_planned.remove(node2)
                cannot_be_extended.append(node1)
                can_be_extended.append(node2)

        elif node2 in can_be_extended and node1 in not_planned:
            if node2.route.volume + node1.demand <= vrp_instance.capacity:
                # add node1 before or after node2
                if node2.prev.is_depot:
                    solution.insert_nodes_after([node1], node2.prev)
                else:
                    solution.insert_nodes_after([node1], node2)

                can_be_extended.remove(node2)
                not_planned.remove(node1)
                cannot_be_extended.append(node2)
                can_be_extended.append(node1)

        elif node1 in can_be_extended and node2 in can_be_extended:
            # if both nodes are in different routes, merge the two routes
            # by moving all customers from route2 into route 1
            if (node1.route != node2.route) and \
                    (node1.route.volume + node2.route.volume <= vrp_instance.capacity):
                route2 = node2.route
                route2_customers = route2.get_customers()

                if node1.next.is_depot:
                    # insert customers from route2 at the end, node2 has to be the first node
                    if node2.next.is_depot:
                        route2_customers = route2_customers[::-1]

                    solution.insert_nodes_after(route2_customers, node1)

                if node1.prev.is_depot:
                    # insert at the front, node2 has to be the last node
                    if node2.prev.is_depot:
                        route2_customers = route2_customers[::-1]

                    solution.insert_nodes_after(route2_customers, node1.prev)

                solution.routes.remove(route2)

                can_be_extended.remove(node2)
                can_be_extended.remove(node1)
                cannot_be_extended.append(node2)
                cannot_be_extended.append(node1)

    # All nodes which were not inserted into a route (e.g., because of high capacity)
    # get their 'own' route
    for node in not_planned:
        depot_of_route = vrp_instance.depot.copy()
        solution.add_route(
            [depot_of_route, node, depot_of_route]
        )

    solution.validate()

    return solution


def clark_wright_route_reduction(
        vrp_instance: VRPProblem,
        cost_evaluator: CostEvaluator,
        visualize_progess: bool = False
) -> VRPSolution:
    logger.info('Constructing VRP solution with Clarke-Wright heuristic')
    solution = clark_wright_parallel(vrp_instance, cost_evaluator)

    minimal_num_routes = math.ceil(
        sum(_cust.demand for _cust in vrp_instance.customers) / vrp_instance.capacity
    )

    if len(solution.routes) > minimal_num_routes + 1:
        logger.info(
            f'Solution had {len(solution.routes)} routes, compared to {minimal_num_routes} minimal routes. '
            f'Trying to reduce the number of routes by considering capacity in the savings.')
        solution = clark_wright_parallel(vrp_instance, cost_evaluator, True)

    return solution
