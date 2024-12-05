from typing import List

from .edge import Edge
from .node import Node


class Route:
    def __init__(self, nodes: List[Node]):
        # Initialize the route with the depot as both the first and last node.
        assert nodes[0].is_depot, 'First node of a route has to be a depot.'
        assert nodes[-1].is_depot, 'Last node of a route has to be a depot.'
        assert nodes[0] == nodes[-1], 'Start and return depot has to be the same'

        size = 0
        volume = 0
        self.depot = nodes[0]

        # link each node by setting references to prev and next node in the route
        for index, node in enumerate(nodes):
            if index + 1 < len(nodes):
                node.next = nodes[index + 1]
            if index > 0:
                node.prev = nodes[index - 1]
            node.route = self

            if not node.is_depot:
                size += 1
                volume += node.demand

        self.size = size  # Number of customers (not including depot)
        self.volume = volume  # Sum of demand of all customers of the route

        self.validate()

    def __repr__(self):
        self.print()

    def get_customers(self) -> list[Node]:
        customers = []
        cur_node = self.depot
        while not cur_node.next.is_depot:
            customers.append(cur_node.next)
            cur_node = cur_node.next

        return customers

    def get_nodes(self) -> list[Node]:
        all_nodes = self.get_customers()
        all_nodes.append(self.depot)
        return all_nodes

    def validate(self):
        cur_node = self.depot
        size = 0
        volume = 0
        return_depot_seen = False

        while not return_depot_seen:
            if not cur_node.is_depot:
                size += 1
                volume += cur_node.demand

            # assert that links are correct
            assert cur_node.next.prev == cur_node, 'Prev and next links are not consistent'
            assert cur_node.route == self, 'Wrong route assigned'

            if size > self.size:
                raise Exception('A depot is missing in the route or the size is wrong')

            cur_node = cur_node.next
            if cur_node.is_depot:
                return_depot_seen = True

        assert size == self.size, 'Route is shorter than should be'
        assert volume == self.volume, 'The volume has been computed incorrectly'

    def print(self) -> str:
        cur_node = self.depot
        route_string = str(cur_node.node_id)
        return_depot_seen = False

        while not return_depot_seen:
            cur_node = cur_node.next
            route_string = route_string + '-' + str(cur_node.node_id)
            if cur_node.is_depot:
                return_depot_seen = True

        return route_string

    def get_edges(self) -> list[Edge]:
        edges = []
        cur_node = self.depot
        return_depot_seen = False

        while not return_depot_seen:
            edges.append(Edge(cur_node, cur_node.next))
            cur_node = cur_node.next
            if cur_node.is_depot:
                return_depot_seen = True

        return edges
