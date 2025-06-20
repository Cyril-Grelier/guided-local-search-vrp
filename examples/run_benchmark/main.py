import logging
import os
from pathlib import Path

from kgls import KGLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


instance_path = os.path.join(Path(__file__).resolve().parent, "instances")
all_instances = sorted([f for f in os.listdir(instance_path) if f.endswith(".vrp")])[
    1:35
]

gaps = dict()
run_times = dict()

for file in all_instances:
    logger.info(f"Solving {file}")
    file_path = os.path.join(instance_path, file)

    # Let us use default parameters
    kgls = KGLS(file_path)
    kgls.set_abortion_condition("runtime_without_improvement", 120)
    kgls.run(visualize_progress=False)

    # collects run stats
    kgls.print_time_distribution()
    gaps[file] = kgls.best_found_gap
    run_times[file] = kgls.total_runtime

logger.info("Benchmark summary")
logger.info(f"Average gap: {sum(gaps.values()) / len(gaps):.2f}")
logger.info(f"Average run_time: {sum(run_times.values()) / len(run_times):.0f}")
logger.info("Detailed Results")
logger.info(f"{'Instance':<20}{'Time':<5}{'Gap':<5}")
logger.info("-" * 30)
for instance in gaps.keys():
    logger.info(f"{instance:<20}{int(run_times[instance]):<5}{gaps[instance]:.2f}")
