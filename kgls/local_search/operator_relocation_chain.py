from collections import defaultdict
import logging

from kgls.datastructure import Node, Route, VRPSolution, CostEvaluator
from .local_search_move import LocalSearchMove

# TODO continue valid chains to find even better improvements
from kgls.local_search.operator_linkernighan import Edge

logger = logging.getLogger(__name__)


class Relocation:

    def __init__(self, node_to_move: Node, move_to_route: Route, move_after: Node, move_before: Node,
                 improvement: float):
        self.node_to_move = node_to_move
        self.move_to_route = move_to_route
        self.move_after = move_after
        self.move_before = move_before
        self.improvement = improvement
        self.forbidden_nodes = {
            node_to_move,
            node_to_move.prev,
            node_to_move.next,
            move_after,
            move_before
        }

    def __lt__(self, other):
        return self.improvement > other.improvement


class RelocationChain(LocalSearchMove):

    def __init__(self):
        self.relocations: list[Relocation] = []
        self.forbidden_nodes: set[Node] = set()
        # TODO better solution for below two things?
        # TODO tuple instead of edge?
        self.forbidden_insertion: set[Edge] = set()
        self.relocated_nodes: set[Node] = set()
        self.improvement: float = 0
        self.demand_changes: defaultdict[Route, int] = defaultdict(int)

    def get_routes(self) -> set[Route]:
        involved_routes = set()
        for relocation in self.relocations:
            involved_routes.add(relocation.move_to_route)
            involved_routes.add(relocation.node_to_move.route)
        return involved_routes

    def _add_relocation(self, relocation: Relocation):
        self.relocations.append(relocation)

        self.forbidden_nodes = self.forbidden_nodes | relocation.forbidden_nodes
        self.forbidden_insertion.add(Edge(relocation.move_after, relocation.move_before))
        # TODO not allowed to place after or before the relocated node in the old route
        self.forbidden_insertion.add(Edge(relocation.node_to_move.prev, relocation.node_to_move))
        self.forbidden_insertion.add(Edge(relocation.node_to_move, relocation.node_to_move.next))

        self.demand_changes[relocation.node_to_move.route] -= relocation.node_to_move.demand
        self.demand_changes[relocation.move_to_route] += relocation.node_to_move.demand

        self.relocated_nodes.add(relocation.node_to_move)
        self.improvement += relocation.improvement

    def can_insert_between(self, node1: Node, node2: Node):
        return (
                Edge(node1, node2) not in self.forbidden_insertion and
                node1 not in self.relocated_nodes and
                node2 not in self.relocated_nodes
        )

    def is_disjunct(self, other):
        for route in self.get_routes():
            if route in other.get_routes():
                return False
        return True

    def extend(self, relocation: Relocation):
        extended_chain = RelocationChain()
        extended_chain.relocations = self.relocations.copy()
        extended_chain.relocated_nodes = self.relocated_nodes.copy()
        extended_chain.forbidden_nodes = self.forbidden_nodes.copy()
        extended_chain.forbidden_insertion = self.forbidden_insertion.copy()
        extended_chain.improvement = self.improvement
        extended_chain.demand_changes = self.demand_changes.copy()

        extended_chain._add_relocation(relocation)

        return extended_chain

    def execute(self, solution: VRPSolution):
        logging.debug(
            f'Executing relocation with {len(self.relocations)} relocations '
            f'and improvement of {int(self.improvement)}')

        # TODO operator relocate in solution
        for relocation in self.relocations:
            old_route = relocation.node_to_move.route

            # link edges in legacy route
            relocation.node_to_move.prev.next = relocation.node_to_move.next
            relocation.node_to_move.next.prev = relocation.node_to_move.prev

            # new start node?
            if relocation.node_to_move.prev.is_depot:
                # TODO remove route if required
                old_route.start_node = relocation.node_to_move.next

            # link edges in destination route
            relocation.move_after.next = relocation.node_to_move
            relocation.node_to_move.prev = relocation.move_after

            relocation.move_before.prev = relocation.node_to_move
            relocation.node_to_move.next = relocation.move_before

            if relocation.move_after.is_depot:
                relocation.move_to_route.start_node = relocation.node_to_move

            old_route.size -= 1
            old_route.volume -= relocation.node_to_move.demand
            relocation.move_to_route.size += 1
            relocation.move_to_route.volume += relocation.node_to_move.demand

            relocation.node_to_move.route = relocation.move_to_route


def insert_node(
        node_to_move: Node,
        removal_gain: float,
        insert_next_to: Node,
        cur_chain: RelocationChain,
        cost_evaluator: CostEvaluator,
):
    # TODO check insertion before and after
    #insertion_cost = cost_evaluator.insertion_costs[node_to_move, insert_next_to]
    #insert_after = cost_evaluator.insertion_after[node_to_move, insert_next_to]
    insertion_cost_before = (
            cost_evaluator.get_distance(node_to_move, insert_next_to.prev)
            + cost_evaluator.get_distance(node_to_move, insert_next_to)
            - cost_evaluator.get_distance(insert_next_to.prev, insert_next_to)
    )
    insertion_cost_after = (
            cost_evaluator.get_distance(node_to_move, insert_next_to.next)
            + cost_evaluator.get_distance(node_to_move, insert_next_to)
            - cost_evaluator.get_distance(insert_next_to.next, insert_next_to)
    )
    if insertion_cost_before <= insertion_cost_after:
        insertion_cost = insertion_cost_before
        insert_after = insert_next_to.prev
    else:
        insertion_cost = insertion_cost_after
        insert_after = insert_next_to

    cost_change = removal_gain - insertion_cost

    if cur_chain.improvement + cost_change > 0:
        if cur_chain.can_insert_between(insert_after, insert_after.next):
            route = insert_next_to.route

            return Relocation(node_to_move, route, insert_after, insert_after.next, cost_change)

    return None

def search_relocation_chains_from(
        valid_relocations_chain: list,
        cost_evaluator: CostEvaluator,
        node_to_move: Node,
        max_depth: int,
        current_depth: int = 0,
        cur_chain: RelocationChain = None
):
    if current_depth >= max_depth:
        # Stopping condition: Maximum depth reached
        return None

    # initialize the first chain
    if cur_chain is None:
        cur_chain = RelocationChain()

    original_prev = node_to_move.prev
    original_next = node_to_move.next

    # Step 1: Calculate the cost change from removing the node
    #removal_improvement = cost_evaluator.ejection_costs[node_to_move]
    removal_improvement = (
            cost_evaluator.get_distance(node_to_move, original_prev)
            + cost_evaluator.get_distance(node_to_move, original_next)
            - cost_evaluator.get_distance(original_prev, original_next)
    )

    # Step 2: For each candidate neighbour of 'node_to_move',
    # check whether a relocation next to it would improve the solution
    candidate_insertions = defaultdict(list)
    for neighbour in cost_evaluator.get_neighborhood(node_to_move):
        if neighbour.route != node_to_move.route and neighbour not in cur_chain.relocated_nodes:
            insertion = insert_node(
                node_to_move,
                removal_improvement,
                neighbour,
                cur_chain,
                cost_evaluator
            )
            if insertion:
                candidate_insertions[neighbour.route].append(
                    insertion
                )

    # TODO this can also be pre-processed
    for destination_route, insertions in candidate_insertions.items():
        best_insertion = sorted(insertions)[0]
        extended_chain = cur_chain.extend(best_insertion)

        # Check feasibility of the target route after insertion
        new_route_volume = destination_route.volume + extended_chain.demand_changes[destination_route]
        if cost_evaluator.is_feasible(new_route_volume):
            valid_relocations_chain.append(
                extended_chain
            )
        else:
            if len(extended_chain.relocations) < max_depth:
                # try to restore feasibility by a follow-up relocation
                # this can be achieved by ejecting a node in the destination route
                for candidate_node in destination_route.get_customers():
                    if cost_evaluator.is_feasible(new_route_volume - candidate_node.demand):
                        if candidate_node not in extended_chain.forbidden_nodes:
                            search_relocation_chains_from(
                                valid_relocations_chain=valid_relocations_chain,
                                cost_evaluator=cost_evaluator,
                                node_to_move=candidate_node,
                                max_depth=max_depth,
                                current_depth=current_depth + 1,
                                cur_chain=extended_chain
                            )


def search_relocation_chains(
        cost_evaluator: CostEvaluator,
        start_nodes: list[Node],
        max_depth: int,
) -> list[RelocationChain]:
    # update pre-processed insertion and removal costs
    cost_evaluator.update_relocation_costs()

    found_moves = []
    for start_node in start_nodes:
        search_relocation_chains_from(
            found_moves,
            cost_evaluator,
            start_node,
            max_depth
        )
    return sorted(found_moves)
