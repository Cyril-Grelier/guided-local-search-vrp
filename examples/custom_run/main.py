import logging
import os
from pathlib import Path

from kgls import KGLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


instance_path = os.path.join(Path(__file__).resolve().parent, "instances")
file_path = os.path.join(instance_path, "X-n101-k25.vrp")

# start with a quick search and 'light' parameters
kgls_light = KGLS(
    path_to_instance_file=file_path,
    depth_lin_kernighan=2,
    depth_relocation_chain=3,
    num_perturbations=3,
    neighborhood_size=10,
    moves=["segment_move", "relocation_chain"],
)
kgls_light.set_abortion_condition("runtime_without_improvement", 1)
kgls_light.run(visualize_progress=False)

kgls_light.print_time_distribution()
kgls_light.best_solution_to_file("interim_solution.txt")

# continue from above solution with a longer search and 'more heavy' parameters
kgls_heavy = KGLS(
    path_to_instance_file=file_path,
    depth_lin_kernighan=5,
    depth_relocation_chain=3,
    num_perturbations=3,
    neighborhood_size=30,
    moves=["segment_move", "cross_exchange", "relocation_chain"],
)
kgls_heavy.set_abortion_condition("runtime_without_improvement", 120)
kgls_heavy.start_from_solution("interim_solution.txt", False)

kgls_light.best_solution_to_file("final_solution.txt")
