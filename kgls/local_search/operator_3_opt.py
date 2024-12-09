import logging

from kgls.datastructure import Node, Route, VRPSolution, CostEvaluator
from .local_search_move import LocalSearchMove

logger = logging.getLogger(__name__)


class SegmentMove(LocalSearchMove):

    def __init__(
            self,
            segment: list[Node],
            move_after: Node,
            improvement: float,
            insert_direction: int
    ):
        self.segment: list[Node] = segment
        self.move_after: Node = move_after
        self.improvement: float = improvement
        self.insert_direction = insert_direction

    def get_routes(self) -> set[Route]:
        return set([self.segment[0].route, self.move_after.route])

    def is_disjunct(self, other):
        if self.segment[0].route in [other.segment[0].route, other.move_after.route]:
            return False
        if self.move_after.route in [other.segment[0].route, other.move_after.route]:
            return False

        return True

    def execute(self, solution: VRPSolution):
        logger.debug(f'Executing Segment relocation with segment of size {len(self.segment)} '
                     f'with improvement of {int(self.improvement)}')

        solution.remove_nodes(self.segment)
        solution.insert_nodes_after(self.segment, self.move_after)


def search_3_opt_moves_from(
        cost_evaluator: CostEvaluator,
        start_node: Node,
        segment_directions: list[int] = [0, 1],
        insert_directions: list[int] = [0, 1]
) -> list[SegmentMove]:
    candidate_moves: list[SegmentMove] = []

    for segment_direction in segment_directions:
        for insert_direction in insert_directions:

            segment_1_prev = start_node.get_neighbour(1 - segment_direction)

            for insert_next_to in cost_evaluator.get_neighborhood(start_node):
                if insert_next_to.route != start_node.route:
                    # compute improvement of first edge changes
                    to_route = insert_next_to.route
                    insert_next_to_2 = insert_next_to.get_neighbour(insert_direction)

                    move_start_improvement = (
                        cost_evaluator.get_distance(start_node, segment_1_prev)
                        + cost_evaluator.get_distance(insert_next_to, insert_next_to_2)
                        - cost_evaluator.get_distance(insert_next_to, start_node)
                    )

                    if move_start_improvement > 0:
                        segment_end = start_node
                        segment_list = [segment_end]
                        route_2_new_volume = to_route.volume + segment_end.demand

                        while not segment_end.is_depot and cost_evaluator.is_feasible(route_2_new_volume):
                            segment_disconnect_2 = segment_end.get_neighbour(segment_direction)

                            move_end_improvement = (
                                    cost_evaluator.get_distance(segment_end, segment_disconnect_2)
                                    - cost_evaluator.get_distance(segment_1_prev, segment_disconnect_2)
                                    - cost_evaluator.get_distance(segment_end, insert_next_to_2)
                            )

                            improvement = move_start_improvement + move_end_improvement
                            if improvement > 0:
                                # store move
                                if insert_direction == 1:
                                    insert_after = insert_next_to
                                else:
                                    insert_after = insert_next_to_2

                                candidate_moves.append(
                                    SegmentMove(
                                        segment_list.copy(),
                                        insert_after,
                                        improvement,
                                        insert_direction
                                    )
                                )

                            # extend
                            segment_end = segment_end.get_neighbour(segment_direction)
                            if insert_direction == 1:
                                segment_list.append(segment_end)
                            else:
                                segment_list.insert(0, segment_end)
                            route_2_new_volume += segment_end.demand

    return candidate_moves


def search_3_opt_moves(
        cost_evaluator: CostEvaluator,
        start_nodes: list[Node],
) -> list[SegmentMove]:
    candidate_moves = []
    for start_node in start_nodes:
        candidate_moves.extend(
            search_3_opt_moves_from(cost_evaluator, start_node)
        )

    return sorted(candidate_moves)


