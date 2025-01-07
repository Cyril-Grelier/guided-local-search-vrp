
import logging
import os
from pathlib import Path

from kgls import KGLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


instance_path = os.path.join(Path(__file__).resolve().parent, 'instances')
all_instances = sorted([f for f in os.listdir(instance_path) if f.endswith('.vrp')])[50:60]

for file in all_instances:
    logger.info(f'Solving {file}')
    file_path = os.path.join(instance_path, file)

    kgls = KGLS(file_path)
    #kgls.set_abortion_condition("iterations_without_improvement", 100)
    kgls.set_abortion_condition("runtime_without_improvement", 120)
    kgls.run(visualize_progress=False)

    """
    import cProfile
    import pstats
    cProfile.run('kgls.run(visualize_progress=False)')#, 'output.prof')
    with open("output.prof") as f:
      p = pstats.Stats(f)
    p.sort_stats("cumulative").print_stats(10)
    """