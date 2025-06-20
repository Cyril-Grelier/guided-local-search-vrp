import logging
import sys

from kgls import KGLS
from kgls.log import init_logging, finish_logging


file_path = sys.argv[1]

output_dir = ""
if len(sys.argv) >= 3:
    output_dir = sys.argv[2]

instance_name = file_path.split("/")[-1].split(".vrp")[0]
seed = 0

init_logging(output_dir, instance_name, seed, output_dir == "")


logging.info(["#instance_name", "seed"])
logging.info(["#" + instance_name, seed])


# Let us use default parameters
kgls = KGLS(file_path)

nb_clients = int(instance_name.split("-n")[1].split("-k")[0])
nb_minutes_per_100_clients = 6

kgls.set_abortion_condition(
    "max_runtime", int(nb_clients * 60 * nb_minutes_per_100_clients / 100)
)
# kgls.add_abortion_condition("max_iterations", 100)
# kgls.add_abortion_condition("runtime_without_improvement", 120)
# kgls.add_abortion_condition("iterations_without_improvement", 100)


kgls.run(visualize_progress=False)
finish_logging(output_dir, instance_name, seed)
# collects run stats
# kgls.print_time_distribution()
