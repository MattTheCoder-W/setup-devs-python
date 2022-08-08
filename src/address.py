from typing import Union, TypeVar
import copy
import os

from .octet import Octet

TAddress = TypeVar("TAddress", bound="Address")

class Address:
    _octets = []
    _mask = False
    def __init__(self, octets: Union[str, int, list]) -> None:
        self.octets = octets
    
    @property
    def octets(self) -> list:
        return self._octets
    
    @octets.setter
    def octets(self, value: Union[str, int, list]) -> None:
        if type(value) is int:
            value = [f"{'1'*value}{'0'*(32-value)}"[x*8:(x+1)*8] for x in range(4)]
            self._mask = True
        elif type(value) is str:
            if "." in value:
                if value.count(".") != 3:
                    raise ValueError(f"Value {value} is not correct address!")
                value = value.split(".")
            else:
                if len(value) != 32:
                    raise ValueError(f"Value {value} is not correct address!")
                value = [value[x*8:(x+1)*8] for x in range(4)]
        
        if type(value) is not list:
            raise ValueError(f"Cannot create address from type: {type(value)}")
        
        if all([True if isinstance(x, Octet) else False for x in value]):
            self._octets = value
        else:
            self._octets = [Octet(x) for x in value]

        if not self._mask:
            if "01" not in self.get_binary():
                self._mask = True

    @property
    def mask(self) -> bool:
        return self._mask
    
    @mask.setter
    def mask(self, value: bool) -> None:
        if type(value) is not bool:
            raise TypeError(f"Incorrect value type! Got type: {type(value)}")
        self._mask = value

    def get_binary(self) -> str:
        return f"{self._octets[0].get_binary()}{self._octets[1].get_binary()}{self._octets[2].get_binary()}{self._octets[3].get_binary()}"

    def __str__(self) -> str:
        return f"{self._octets[0]}.{self._octets[1]}.{self._octets[2]}.{self._octets[3]}"
    
    def __int__(self) -> int:
        if not self._mask:
            raise NotImplementedError("Cannot represent not mask as integer")
        return self.get_binary().count("1")
    
    def __bool__(self) -> bool:
        return True if os.system(f"ping -c 1 -W 0.5 {str(self)} > /dev/null") == 0 else False
    
    ### Comparing

    def __gt__(self, other: TAddress) -> bool:
        if isinstance(other, Address):
            sum_other = int(other.get_binary(), 2)
            return int(self.get_binary(), 2) > sum_other
        else:
            raise TypeError(f"Cannot compare Address with {type(other)}")

    def __lt__(self, other: TAddress) -> bool:
        if isinstance(other, Address):
            sum_other = int(other.get_binary(), 2)
            return int(self.get_binary(), 2) < sum_other
        else:
            raise TypeError(f"Cannot compare Address with {type(other)}")
    
    def __eq__(self, other: TAddress) -> bool:
        if isinstance(other, Address):
            sum_other = int(other.get_binary(), 2)
            return int(self.get_binary(), 2) == sum_other
        else:
            raise TypeError(f"Cannot compare Address with {type(other)}")
    
    def __ge__(self, other: TAddress) -> bool:
        return self > other or self == other
    
    def __le__(self, other: TAddress) -> bool:
        return self < other or self == other

    def __ne__(self, other: TAddress) -> bool:
        return not self == other

    ### Math

    def __add__(self, other: int) -> TAddress:
        if type(other) is not int:
            raise TypeError(f"Cannot add value of type `{type(other)}` to Address")
        new_octets = copy.copy(self._octets)
        new_octets[-1] += other
        while max(new_octets) > 255:
            for i in range(len(new_octets)):
                if new_octets[i] > 255:
                    if i-1 < 0:
                        raise ValueError(f"Cannot add {other} to {str(self)}! Value is too high!")
                    new_octets[i-1] += 1
                    new_octets[i] -= 255
        return Address(new_octets)
    
    def __sub__(self, other: int) -> TAddress:
        if type(other) is not int:
            raise TypeError(f"Cannot add value of type `{type(other)}` to Address")
        new_octets = copy.copy(self._octets)
        new_octets[-1] -= other
        while min(new_octets) < 0:
            for i in range(len(new_octets)):
                if new_octets[i] < 0:
                    if i-1 < 0:
                        raise ValueError(f"Cannot substract {other} from {str(self)}! Value is too high!")
                    new_octets[i-1] -= 1
                    new_octets[i] += 255
        return Address(new_octets)
