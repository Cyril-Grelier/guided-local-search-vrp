import os
from pathlib import Path

from kgls import KGLS
from kgls.log import init_logging


instance = "X-n101-k25"

instance_path = os.path.join(Path(__file__).resolve().parent, "instances")
file_path = os.path.join(instance_path, instance + ".vrp")

init_logging("", instance, 0, True)

kgls = KGLS(file_path, depth_lin_kernighan=2)
kgls.set_abortion_condition("runtime_without_improvement", 10)
kgls.run(visualize_progress=True)
kgls.print_time_distribution()
