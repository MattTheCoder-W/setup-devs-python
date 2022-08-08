from abc import ABC, abstractmethod


class iadd(ABC):
    @abstractmethod
    def __add__(self):
        pass


class isub(ABC):
    @abstractmethod
    def __sub__(self):
        pass


class imathematics(iadd, isub):
    pass
