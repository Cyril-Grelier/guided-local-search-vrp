
import logging
import os
from pathlib import Path

from kgls import KGLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Get the absolute path of the current script's parent directory
instance_path = os.path.join(Path(__file__).resolve().parent, 'instances')
all_instances = sorted([f for f in os.listdir(instance_path) if f.endswith('.vrp')])[1:19]

for file in all_instances:
    logger.info(f'Solving {file}')
    file_path = os.path.join(instance_path, file)

    kgls = KGLS(file_path)
    kgls.set_abortion_condition("iterations_without_improvement", 100)
    kgls.run(visualize_progress=False)

    # import cProfile
    # import pstats
    # cProfile.run('run_knowledge_guided_search(problem)')#, 'output.prof')
    # with open("output.prof") as f:
    #   p = pstats.Stats(f)
    # p.sort_stats("cumulative").print_stats(10)
