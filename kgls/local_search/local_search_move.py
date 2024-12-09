from abc import ABC, abstractmethod

from kgls.datastructure import Route


class LocalSearchMove(ABC):
    improvement: int

    def __init__(self):
        pass

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def get_routes(self) -> list[Route]:
        pass

    def __lt__(self, other):
        return self.improvement > other.improvement

