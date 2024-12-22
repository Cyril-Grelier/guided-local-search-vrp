import logging
from collections import defaultdict, deque

from kgls.datastructure import Node, Route, VRPSolution, CostEvaluator
from .local_search_move import LocalSearchMove

logger = logging.getLogger(__name__)


class LKEdge:
    node1: Node
    node2: Node

    def __init__(self, node1: Node, node2: Node):
        self.node1 = node1
        self.node2 = node2

    def __hash__(self):
        if self.node1 > self.node2:
            return hash((self.node1, self.node2))
        else:
            return hash((self.node2, self.node1))

    def __eq__(self, other):
        if other.node1 == self.node1 and other.node2 == self.node2:
            return True
        if other.node1 == self.node2 and other.node2 == self.node1:
            return True
        return False


class NOptMove(LocalSearchMove):

    def __init__(
            self,
            removed_edges: set,
            new_edges: set,
            improvement: float,
            end_with_node: Node,
            route: Route
    ):
        self.new_edges: set[LKEdge] = new_edges
        self.removed_edges: set[LKEdge] = removed_edges
        self.improvement: float = improvement
        self.end_with_node: Node = end_with_node
        self.route: Route = route

    def get_routes(self):
        return [self.route]

    def is_disjunct(self, other):
        pass

    def execute(self, solution: VRPSolution):
        logger.debug(
            f'Executing {len(self.removed_edges)}-opt move '
            f'with improvement {int(self.improvement)}')

        graph = defaultdict(list)
        for node in self.route.nodes:
            if node.is_depot:
                new_neighbors = [self.route.customers[-1], self.route.customers[0]]
            else:
                new_neighbors = [solution.prev(node), solution.next(node)]

            for _r in self.removed_edges:
                if _r.node1 == node:
                    new_neighbors.remove(_r.node2)
                elif _r.node2 == node:
                    new_neighbors.remove(_r.node1)
            for _a in self.new_edges:
                if _a.node1 == node:
                    new_neighbors.append(_a.node2)
                elif _a.node2 == node:
                    new_neighbors.append(_a.node1)
            graph[node] = new_neighbors

        cur_node = self.route.depot
        new_route = [cur_node]

        while len(new_route) < self.route.size + 1:
            new_neighbours = graph[cur_node]
            assert len(new_neighbours) == 2

            if new_neighbours[1] not in new_route:
                cur_node = new_neighbours[1]
            else:
                cur_node = new_neighbours[0]

            assert cur_node not in new_route
            new_route.append(cur_node)

        new_route.append(self.route.depot)

        solution.rearrage_route(self.route, new_route)


class LKMoveSearcher:
    def __init__(
            self,
            route: Route,
            end_node: Node,
            max_depth: int,
            possible_new_neighbours: dict[Node, list[tuple[Node, int]]],
            current_neighbors: dict[Node, list[tuple[Node, int]]],
            completion_costs_dict: dict[Node, int],
    ):
        self.valid_moves = []
        self.end_node = end_node
        self.route = route
        self.max_depth = max_depth
        self.current_neighbors = current_neighbors
        self.possible_new_neighbours = possible_new_neighbours
        self.completion_costs_dict = completion_costs_dict
        self.min_completion_costs = min(_c for _c in self.completion_costs_dict.values())

    def search(
            self,
            start_node: Node,
            added_edges: set[LKEdge],
            removed_edges: set[LKEdge],
            cum_improvement: int,
            changes_made: int = 1
    ):
        if changes_made > 1:
            # try to complete
            completion_costs = self.completion_costs_dict.get(start_node, float('inf'))
            if cum_improvement - completion_costs > 0:

                if LKEdge(self.end_node, start_node) not in added_edges:
                    extended_move = added_edges.copy()
                    extended_move.add(LKEdge(self.end_node, start_node))

                    if not self.has_sub_routes(extended_move, removed_edges):
                        self.valid_moves.append(
                            NOptMove(
                                removed_edges=removed_edges.copy(),
                                new_edges=extended_move,
                                improvement=cum_improvement - completion_costs,
                                end_with_node=self.end_node,
                                route=self.route,
                            )
                        )

        if changes_made >= self.max_depth:
            # Stopping condition: Maximum depth reached
            return None

        # try to connect 'start_node' to any of the nearest non-connected nodes in the route
        for candidate_neighbour, cost_added in self.possible_new_neighbours[start_node]:
            if cum_improvement > cost_added:
                if LKEdge(start_node, candidate_neighbour) not in added_edges:
                    # try to break an edge adjacent to 'candidate_neighbour'
                    for neighbour_neighbour, cost_removed in self.current_neighbors[candidate_neighbour]:
                        if cum_improvement - cost_added + cost_removed > self.min_completion_costs:
                            if LKEdge(candidate_neighbour, neighbour_neighbour) not in removed_edges:
                                extended_move = added_edges.copy()
                                extended_move.add(LKEdge(start_node, candidate_neighbour))
                                extended_move_remove = removed_edges.copy()
                                extended_move_remove.add(LKEdge(candidate_neighbour, neighbour_neighbour))

                                self.search(
                                    start_node=neighbour_neighbour,
                                    added_edges=extended_move,
                                    removed_edges=extended_move_remove,
                                    cum_improvement=cum_improvement - cost_added + cost_removed,
                                    changes_made=changes_made+1
                                )

    def has_sub_routes(
            self,
            added_edges: set[LKEdge],
            removed_edges: set[LKEdge]
    ) -> bool:
        # check whether one node is connected to all other nodes in the route
        graph = defaultdict(list)
        for node in self.current_neighbors.keys():
            new_neighbors = [self.current_neighbors[node][0][0], self.current_neighbors[node][1][0]]

            # remove neighbours from removed edges
            for _r in removed_edges:
                if _r.node1 == node:
                    new_neighbors.remove(_r.node2)
                elif _r.node2 == node:
                    new_neighbors.remove(_r.node1)

            # add neighbours from new edges
            for _a in added_edges:
                if _a.node1 == node:
                    new_neighbors.append(_a.node2)
                elif _a.node2 == node:
                    new_neighbors.append(_a.node1)

            graph[node] = new_neighbors

        # Check connectivity with Breadth First Search (BFS)
        visited = set()
        queue = deque([self.end_node])  # Start BFS from arbitrary node

        while queue:
            node = queue.popleft()
            if node not in visited:
                visited.add(node)
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        queue.append(neighbor)

        # If all nodes are visited, the graph is connected
        return len(visited) != len(self.current_neighbors)


def search_lk_moves(
        solution: VRPSolution,
        cost_evaluator: CostEvaluator,
        route: Route,
        max_depth: int
) -> list[NOptMove]:
    # initialize the data structures
    depot_node = route.depot
    customers = route.customers

    # compute which neighbor to connect to
    possible_new_neighbors: dict[Node, list[tuple[Node, int]]] = {}

    # For the depot node: it can connect to any customer in the route except current neighbors
    possible_new_neighbors[depot_node] = [
        (customer, cost_evaluator.get_distance(depot_node, customer))
        for customer in customers[1:-1]
    ]
    # For customers, any of the 6 nearest nodes in the route (which are not currently a neighbour)
    # are candidate neighbors
    for customer in customers:
        nearest_nodes_in_route = [
            (node, cost_evaluator.get_distance(customer, node))
            for node in route.nodes
            if node != customer and node != solution.prev(customer) and node != solution.next(customer)
        ]
        nearest_nodes_in_route = sorted(nearest_nodes_in_route, key=lambda x: x[1])
        possible_new_neighbors[customer] = nearest_nodes_in_route[:6]
        # TODO this needs to be sorted before filtering for 6!
        # TODO also the depot is never included here!

    neighbors: dict[Node, list[tuple[Node, int]]] = dict()
    for node in customers:
        neighbors[node] = [
            (solution.prev(node), cost_evaluator.get_distance(node, solution.prev(node))),
            (solution.next(node), cost_evaluator.get_distance(node, solution.next(node)))
        ]
    neighbors[depot_node] = [
        (customers[-1], cost_evaluator.get_distance(depot_node, customers[-1])),
        (customers[0], cost_evaluator.get_distance(depot_node, customers[0]))
    ]

    valid_moves: list[NOptMove] = []

    for start_node in route.nodes:
        end_node = neighbors[start_node][0][0]

        completion_costs = {
            node: cost_evaluator.get_distance(end_node, node)
            for node in route.nodes
            if node != end_node and node != neighbors[end_node][0][0] and node != neighbors[end_node][1][0]
        }

        searcher = LKMoveSearcher(
            route=route,
            end_node=end_node,
            max_depth=max_depth,
            possible_new_neighbours=possible_new_neighbors,
            current_neighbors=neighbors,
            completion_costs_dict=completion_costs,
        )
        searcher.search(
            start_node=start_node,
            removed_edges={LKEdge(end_node, start_node)},
            added_edges=set(),
            cum_improvement=cost_evaluator.get_distance(start_node, end_node),
        )
        valid_moves.extend(searcher.valid_moves)

    return sorted(valid_moves)
