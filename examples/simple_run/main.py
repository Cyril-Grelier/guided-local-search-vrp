import logging
import os
from pathlib import Path

from kgls import KGLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


instance_path = os.path.join(Path(__file__).resolve().parent, "instances")
file_path = os.path.join(instance_path, "X-n101-k25.vrp")

kgls = KGLS(file_path, depth_lin_kernighan=2)
kgls.set_abortion_condition("runtime_without_improvement", 10)
kgls.run(visualize_progress=True)
kgls.print_stats()
