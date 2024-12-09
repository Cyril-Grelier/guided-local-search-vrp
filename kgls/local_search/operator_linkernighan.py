import logging

from kgls.datastructure.edge import Edge, get_sorted_tuple
from kgls.datastructure import Node, Route, VRPSolution, CostEvaluator
from .local_search_move import LocalSearchMove

logger = logging.getLogger(__name__)


class NOptMove(LocalSearchMove):

    def __init__(self, removed_edge: Edge, improvement: float, end_with_node: Node, route: Route, new_edges=set()):
        self.new_edges: set[Edge] = new_edges
        self.removed_edges: set[Edge] = removed_edge
        self.improvement: float = improvement
        self.end_with_node: Node = end_with_node
        self.route: Route = route

    def extend(
            self,
            new_edge: Edge = None,
            removed_edge: Edge = None,
            improvement_change: float = 0
    ):
        # copy existing move
        extended_move = NOptMove(self.removed_edges.copy(), self.improvement, self.end_with_node, self.route,
                                 self.new_edges.copy())
        # extended_move.new_edges =
        # extended_move.removed_edges =

        # extend
        extended_move.improvement += improvement_change
        if new_edge:
            extended_move.new_edges.add(new_edge)
        if removed_edge:
            extended_move.removed_edges.add(removed_edge)

        return extended_move

    def get_routes(self):
        return [self.route]

    def is_disjunct(self):
        pass

    def complete_move(self, start_node: Node):
        if start_node not in [self.end_with_node] + self.end_with_node.get_neighbours():
            completion_costs = start_node.get_distance(self.end_with_node)
            if self.improvement - completion_costs > 0:
                new_edge: Edge = get_sorted_tuple(start_node, self.end_with_node)

                if new_edge not in self.new_edges:
                    return self.extend(
                        new_edge=new_edge,
                        improvement_change=-completion_costs
                    )

        return None

    # TODO costEvaluator is only for debug reasons
    def execute(self, solution: VRPSolution):
        logger.debug(
            f'Executing {len(self.removed_edges)}-opt move '
            f'with improvement {int(self.improvement)}')

        # start from depot
        # TODO should not contain subroutes
        cur_node = self.route.depot
        num_nodes = 0

        while cur_node != self.route.depot or num_nodes < self.route.size:

            if get_sorted_tuple(cur_node, cur_node.next) not in self.removed_edges:
                # might need to rotate
                if cur_node.next.prev != cur_node:
                    cur_node.next.next = cur_node.next.prev
                    cur_node.next.prev = cur_node

                # edge remains, nothing needs to be done
                cur_node = cur_node.next
            else:
                #  there must be a new edge with 'cur_node'
                new_neighbour: Node = None
                for edge in self.new_edges:
                    if Edge(*edge).contains(cur_node):
                        new_neighbour = Edge(*edge).other_node(cur_node)
                        break

                assert new_neighbour is not None, 'no new edge with node found'

                # new_neighbour becomes new successor of cur_node.
                # If it has a predecessor which is not removed, move it as successor
                if get_sorted_tuple(new_neighbour, new_neighbour.prev) not in self.removed_edges:
                    new_neighbour.next = new_neighbour.prev

                cur_node.next = new_neighbour
                new_neighbour.prev = cur_node
                self.new_edges.remove(edge)

                cur_node = new_neighbour

            num_nodes += 1


def has_sub_routes(start_node: Node, added_edges, removed_edges) -> bool:
    # check whether one node is connected to all other nodes in the route
    nodes_to_check: set[Node] = {start_node}
    connected_nodes: set[Node] = set()

    while len(nodes_to_check) > 0:
        node: Node = nodes_to_check.pop()
        connected_nodes.add(node)

        found_neighbours = 0
        if get_sorted_tuple(node, node.prev) not in removed_edges and node.prev not in connected_nodes:
            nodes_to_check.add(node.prev)
            found_neighbours += 1
        if get_sorted_tuple(node, node.next) not in removed_edges and node.next not in connected_nodes:
            nodes_to_check.add(node.next)
            found_neighbours += 1

        if found_neighbours < 2:
            for edge_n1, edge_n2 in added_edges:
                if edge_n1 == node and edge_n2 not in connected_nodes:
                    nodes_to_check.add(edge_n2)
                elif edge_n2 == node and edge_n1 not in connected_nodes:
                    nodes_to_check.add(edge_n1)

    route = start_node.route
    if not route:
        route = start_node.next.route
    if len(connected_nodes) == route.size + 1:
        return False
    return True


def search_lk_moves_from(
        valid_moves,
        start_node: Node,
        end_node: Node,
        max_depth: int,
        possible_new_neighbours: dict[Node, list[tuple[Node, int]]],
        current_neighbors: dict[Node, list[tuple[Node, int]]],
        completion_costs_dict=dict[Node, int],
        added_edges: set = set(),
        removed_edges: set = set(),
        cum_improvement: float = 0
):
    if len(removed_edges) > 1:
        # try to complete
        completion_costs = completion_costs_dict.get(start_node, float('inf'))
        if cum_improvement - completion_costs > 0:
            added_edge = get_sorted_tuple(start_node, end_node)

            if added_edge not in added_edges:
                extended_move = added_edges.copy()
                extended_move.add(added_edge)

                if not has_sub_routes(start_node, extended_move, removed_edges):
                    route = start_node.route
                    valid_moves.append(
                        NOptMove(
                            removed_edge=removed_edges.copy(),
                            improvement=cum_improvement - completion_costs,
                            end_with_node=end_node,
                            route=route,
                            new_edges=extended_move
                        )
                    )

    if len(removed_edges) >= max_depth:
        # Stopping condition: Maximum depth reached
        return None

    for candidate_neighbour, candidate_distance in possible_new_neighbours[start_node]:
        # is there another candidate node in the route which is a potential neighbour?
        if cum_improvement > candidate_distance:
            added_edge: tuple = get_sorted_tuple(start_node, candidate_neighbour)

            if added_edge not in added_edges:
                # try to break a neighboring edge
                for neighbour_neighbour, neighbour_neighbour_distance in current_neighbors[candidate_neighbour]:
                    remove_edge = get_sorted_tuple(candidate_neighbour, neighbour_neighbour)
                    if remove_edge not in removed_edges:
                        extended_move = added_edges.copy()
                        extended_move.add(added_edge)
                        extended_move_remove = removed_edges.copy()
                        extended_move_remove.add(remove_edge)

                        search_lk_moves_from(
                            valid_moves=valid_moves,
                            start_node=neighbour_neighbour,
                            end_node=end_node,
                            max_depth=max_depth,
                            possible_new_neighbours=possible_new_neighbours,
                            current_neighbors=current_neighbors,
                            completion_costs_dict=completion_costs_dict,
                            added_edges=extended_move,
                            removed_edges=extended_move_remove,
                            cum_improvement=cum_improvement - candidate_distance + neighbour_neighbour_distance
                        )


def search_lk_moves(
        cost_evaluator: CostEvaluator,
        route: Route,
        max_depth: int
) -> list[NOptMove]:
    # initialize the data structures and first edge removal
    depot_node = route.depot
    customers = route.get_customers()

    # compute which neighbor to connect to
    possible_new_neighbors: dict[Node, list[Node]] = {}

    # For the depot node: it can connect to any customer in the route except current neighbors
    possible_new_neighbors[depot_node] = [
        (customer, cost_evaluator.get_distance(depot_node, customer)) for customer in customers
        if customer not in depot_node.get_neighbours()
    ]
    # For each customer: they can connect to the depot and up to 6 nearest nodes in their neighborhood
    for customer in customers:
        possible_new_neighbors[customer] = [
                                               (node, cost_evaluator.get_distance(customer, node)) for node in
                                               [depot_node] + customers
                                               if node in cost_evaluator.get_neighborhood(
                customer) and node not in customer.get_neighbours()
                                           ][:6]  # Limit to 6 nearest neighbors

    neighbors = {
        node: [
            (neighbor, cost_evaluator.get_distance(node, neighbor))
            for neighbor in node.get_neighbours()
        ]
        for node in route.get_nodes()
    }

    valid_moves: list[NOptMove] = []

    for start_node in route.get_nodes():
        # for end_node in start_node.get_neighbours():
        end_node = start_node.prev

        completion_costs = {
            node: cost_evaluator.get_distance(end_node, node)
            for node in route.get_nodes()
            if node != end_node and node not in end_node.get_neighbours()
        }

        search_lk_moves_from(
            valid_moves=valid_moves,
            start_node=start_node,
            end_node=end_node,
            max_depth=max_depth,
            possible_new_neighbours=possible_new_neighbors,
            current_neighbors=neighbors,
            completion_costs_dict=completion_costs,
            cum_improvement=cost_evaluator.get_distance(start_node, end_node),
            removed_edges={get_sorted_tuple(start_node, end_node)},
        )

    return sorted(valid_moves)
