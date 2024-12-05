class Node:
    node_id: int
    x_coordinate: float
    y_coordinate: float
    is_depot: bool

    def __init__(
            self,
            node_id: int,
            x_coordinate: float,
            y_coordinate: float,
            demand: int = 0,
            is_depot: bool = False
    ):
        from kgls.datastructure.route import Route

        self.node_id: int = node_id
        self.x_coordinate: float = x_coordinate
        self.y_coordinate: float = y_coordinate
        self.demand: int = demand
        self.is_depot: bool = is_depot

        self.prev: Node = None  # Previous node in the route
        self.next: Node = None  # Next node in the route
        self.route: Route = None

    def __repr__(self):
        return str(self.node_id)

    def __lt__(self, other):
        return self.node_id > other.node_id

    def __eq__(self, other):
        return self.node_id == other.node_id

    def __hash__(self):
        return self.node_id

    def copy(self):
        return Node(
            self.node_id,
            self.x_coordinate,
            self.y_coordinate,
            self.demand,
            self.is_depot
        )

    def set_depot(self):
        self.is_depot = True

    def set_demand(self, demand):
        self.demand = demand

    def get_neighbours(self) -> list:
        return [self.prev, self.next]

    def get_neighbour(self, direction: int):
        if self.is_depot:
            return None

        if direction == 1:
            return self.next
        else:
            return self.prev
