from typing import Union, TypeVar

TOctet = TypeVar("TOctet", bound="Octet")


class Octet:
    _value = 0
    _ignore_range = False
    def __init__(self, value: Union[int, str], ignore_range: bool = False) -> None:
        self._ignore_range = ignore_range
        self.value = value
    
    @property
    def value(self) -> int:
        return int(self.value)
    
    @value.setter
    def value(self, value: Union[int, str]) -> None:
        if type(value) is str and Octet._check_binary(value):
            value = int(value, 2)
        else:
            value = int(value)

        if value not in range(0, 256) and not self._ignore_range:
            raise ValueError(f"Octet value out of range 0-255! Got: {value}, ignore_range: {self._ignore_range}")
        self._value = value
    
    @staticmethod
    def _check_binary(value: str) -> bool:
        return True if len(value) == (value.count("1") + value.count("0")) and len(value) == 8 else False

    def get_binary(self) -> str:
        return str(format(self._value, "#010b")[2:])
    
    def __int__(self) -> int:
        return int(self._value)
    
    def __str__(self) -> str:
        return str(self._value)

    ### Comparing

    def __gt__(self, other: Union[int, TOctet]) -> bool:
        if isinstance(other, Octet):
            return self._value > other._value
        elif type(other) is int:
            return self._value > other
        else:
            raise TypeError(f"Cannot compare Octet with {type(value)}!")
    
    def __lt__(self, other: Union[int, TOctet]) -> bool:
        if isinstance(other, Octet):
            return self._value < other._value
        elif type(other) is int:
            return self._value < other
        else:
            raise TypeError(f"Cannot compare Octet with {type(value)}!")

    def __ge__(self, other: Union[int, TOctet]) -> bool:
        return self > other or self == other
    
    def __le__(self, other: Union[int, TOctet]) -> bool:
        return self < other or self == other
    
    def __eq__(self, other: Union[int, TOctet]) -> bool:
        if isinstance(other, Octet):
            return self._value == other._value
        elif type(other) is int:
            return self._value == other
        else:
            raise TypeError(f"Cannot compare Octet with {type(value)}!")
    
    def __ne__(self, other: Union[int, TOctet]) -> bool:
        return not self == other

    def __add__(self, other: Union[int, TOctet]) -> TOctet:
        if isinstance(other, Octet):
            other = int(other)
        if type(other) is not int:
            raise TypeError(f"Cannot add value of type `{type(other)}` to octet!")
        return Octet(int(self) + other, ignore_range=True)
    
    def __sub__(self, other: Union[int, TOctet]) -> TOctet:
        if isinstance(other, Octet):
            other = int(other)
        if type(other) is not int:
            raise TypeError(f"Cannot substract value of type `{type(other)}` from octet!")
        return Octet(int(self) - other, ignore_range=True)
