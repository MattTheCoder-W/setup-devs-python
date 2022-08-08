from abc import ABC, abstractmethod


class ilt(ABC):
    @abstractmethod
    def __lt__(slef):
        pass


class ile(ABC):
    @abstractmethod
    def __le__(self):
        pass


class ieq(ABC):
    @abstractmethod
    def __eq__(self):
        pass


class ine(ABC):
    @abstractmethod
    def __ne__(self):
        pass


class igt(ABC):
    @abstractmethod
    def __gt__(self):
        pass


class ige(ABC):
    @abstractmethod
    def __ge__(self):
        pass


class icomparators(ieq, ige, igt, ile, ilt, ine):
    pass
