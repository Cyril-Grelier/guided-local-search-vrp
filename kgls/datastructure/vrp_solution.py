from collections import defaultdict

from .node import Node
from .route import Route
from .vrp_problem import VRPProblem


class VRPSolution:
    def __init__(self, problem: VRPProblem, routes: list[Route]):
        self.routes = routes
        self.problem = problem
        self.solution_stats: defaultdict[str, float] = defaultdict(float)
        self._plot_progress = False

    def start_plotting(self):
        self._plot_progress = True

        self._fig = plt.figure(figsize=(10, 6))
        gs = GridSpec(3, 4, figure=self._fig)  # 3 rows, 4 columns grid
        self._ax_routes = self._fig.add_subplot(gs[:, :3])  # Large panel for routes
        self._ax_chart = self._fig.add_subplot(gs[0, 3])  # Small panel for chart
        self._time_steps = []
        self._solution_values = []

        plt.ion()

        self._node_scatter = None
        self._plotted_edges = []

        self._initialize_plots()
        plt.show()

    def validate(self):
        # All routes are OK
        for route in self.routes:
            route.validate()

        for route in self.routes:
            assert route.volume <= self.problem.capacity, \
                "Capacity violation"

        # All customers have been visited exactly once
        visited_customers = []

        for route in self.routes:
            visited_customers.extend(
                route.get_customers()
            )

        assert len(visited_customers) == len(set(visited_customers)), \
            "Some customers have been planned more than once"

        assert len(visited_customers) == len(self.problem.customers), \
            "Not all customers have been planned"

    def __copy__(self):
        return VRPSolution(
            self.problem,
            self.routes
        )

    def print_stats(self):
        for key, value in self.solution_stats:
            print(f'{key}: {value}')

    def remove_nodes(self, nodes_to_be_removed: list[Node]):
        route = nodes_to_be_removed[0].route

        # nodes might be reversed
        if len(nodes_to_be_removed) > 1 and nodes_to_be_removed[0].next != nodes_to_be_removed[1]:
            prev_left_neighbor = nodes_to_be_removed[-1].prev
            prev_right_neighbor = nodes_to_be_removed[0].next
        else:
            prev_left_neighbor = nodes_to_be_removed[0].prev
            prev_right_neighbor = nodes_to_be_removed[-1].next

        prev_left_neighbor.next = prev_right_neighbor
        prev_right_neighbor.prev = prev_left_neighbor
        route.size -= len(nodes_to_be_removed)

        for node in nodes_to_be_removed:
            route.volume -= node.demand
            assert node.is_depot is False, 'A depot is removed from a route'

    def add_route(self, nodes: list[Node]):
        self.routes.append(
            Route(nodes)
        )

    def insert_nodes_after(self, nodes_to_be_inserted: list[Node], move_after_node: Node):
        new_route = move_after_node.route

        for index, node in enumerate(nodes_to_be_inserted):
            if index + 1 < len(nodes_to_be_inserted):
                node.next = nodes_to_be_inserted[index + 1]
                nodes_to_be_inserted[index + 1].prev = node

            new_route.volume += node.demand
            node.route = new_route
            assert node.is_depot is False, 'A depot is inserted into a route'

        old_next_node = move_after_node.next
        move_after_node.next = nodes_to_be_inserted[0]
        nodes_to_be_inserted[0].prev = move_after_node

        nodes_to_be_inserted[-1].next = old_next_node
        old_next_node.prev = nodes_to_be_inserted[-1]

        new_route.size += len(nodes_to_be_inserted)

    def _initialize_plots(self):
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpec

        # Initialize route lines
        colors = plt.cm.get_cmap("tab20c")
        for route_index in range(len(self.problem.customers)):  # max number of possible routes
            line, = self._ax_routes.plot([], [], color=colors(route_index % 20))
            self._plotted_edges.append(line)

        # draw nodes
        for node in self.problem.nodes:
            if node.is_depot:
                self._ax_routes.plot(node.x_coordinate, node.y_coordinate, color='black', marker='s')
            else:
                self._ax_routes.plot(node.x_coordinate, node.y_coordinate, color='grey', marker='o')

        self._ax_routes.axis('off')

        # layout of chart
        self._ax_chart.set_box_aspect(1)  # Make the chart square-ish
        self._ax_chart.spines['top'].set_visible(False)
        self._ax_chart.spines['right'].set_visible(False)
        self._ax_chart.spines['bottom'].set_color('grey')
        self._ax_chart.spines['left'].set_color('grey')
        self._ax_chart.grid(False)
        self._ax_chart.set_xticks([])  # Remove x-axis ticks
        self._ax_chart.set_yticks([])  # Remove y-axis ticks

        self._chart_line, = self._ax_chart.plot([], [], label="", color='black')

        self._fig.canvas.draw()
        self._fig.canvas.flush_events()

    def plot(self, solution_value: float):
        if self._plot_progress:
            # update routes
            for route_index, route in enumerate(self.routes):
                x_coordinates = [route.depot.x_coordinate] + [node.x_coordinate for node in route.get_nodes()]
                y_coordinates = [route.depot.y_coordinate] + [node.y_coordinate for node in route.get_nodes()]
                self._plotted_edges[route_index].set_data(x_coordinates, y_coordinates)

            # update value chart
            current_gap = 100 * (solution_value - self.problem.bks) / self.problem.bks
            self._time_steps.append(len(self._time_steps) + 1)
            self._solution_values.append(current_gap)
            self._chart_line.set_data(self._time_steps, self._solution_values)
            self._ax_chart.relim()  # Recompute the axis limits
            self._ax_chart.autoscale_view()
            self._ax_chart.set_title(f'Current Gap to BKS: {current_gap: .2f}%', fontsize=10, loc='center')

            self._fig.canvas.draw_idle()
            self._fig.canvas.flush_events()
