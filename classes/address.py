#################################
# Classes for Address management
# Author: MattTheCoder-W
#################################

import os
import copy
import socket
from typing import Union, TypeVar

from .binary import binary_sum, binary_sub
from .octet import Octet

# Custom types
TAddress = TypeVar("TAddress", bound="Address")
TOctet = TypeVar("TOctet", bound="Octet")


class Address:
    """Class for representation of IPv4 Address.

    Arguments:
        octets (str|int|list) -- Octet values of address
            str -- "x.x.x.x" format
            int -- 0-30 format (for masks)
            list -- list of 4 values in [Octet|str|int] format
    """

    _octets = []  # List for octet values
    _mask = False  # Mask mode flag
    
    def __init__(self, octets: Union[str, int, list]) -> None:
        self.octets = octets
    
    @property
    def octets(self) -> list:
        return self._octets
    
    @octets.setter
    def octets(self, value: Union[str, int, list]) -> None:
        if type(value) is int or (type(value) is str and value.isnumeric() and int(value) in range(0, 31)):
            value = int(value)
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
        """Return binary representation of address in 32-bit binary string format."""
        return f"{self._octets[0].get_binary()}{self._octets[1].get_binary()}{self._octets[2].get_binary()}{self._octets[3].get_binary()}"

    def increment_with_difference_mask(self, difference_mask: TAddress, value = 1) -> TAddress:
        """Increment address using difference mask (used for calculating sub-network addresses)."""
        if not isinstance(difference_mask, type(self)):
            raise TypeError("Difference mask should be `Address` object")
        str_addr = ''.join(self.get_binary())

        mask = difference_mask.get_binary()
        start, end = [mask.find("1"), mask.rfind("1")+1]
        str_part = binary_sum(str_addr[start:end], str(bin(value))[2:])
        str_addr = f"{str_addr[:start]}{str_part}{str_addr[end:]}"

        return Address(str_addr)
    
    ### Returning specific format

    def __str__(self) -> str:
        return f"{self._octets[0]}.{self._octets[1]}.{self._octets[2]}.{self._octets[3]}"
    
    def __int__(self) -> int:
        if not self._mask:
            raise NotImplementedError("Cannot represent not mask as integer")
        return self.get_binary().count("1")
    
    def __bool__(self) -> bool:
        return True if os.system(f"ping -c 1 -W 0.2 {str(self)} > /dev/null") == 0 else False
    
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


class Port:
    """Class for socket representation.

    Attributes:
        addr (Address) -- Address value of socket.
        value (int) -- Port value of socket.
    """
    __slots__ = ["_value", "_addr"]
    def __init__(self, addr: Address, value: int):
        self.value = value
        self.addr = addr
    
    @property
    def value(self) -> int:
        return self._value
    
    @value.setter
    def value(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Port value should be int!")
        value = int(value)
        if value not in range(0, 65536):
            raise ValueError("Port number out of range!")
        self._value = value
    
    @property
    def addr(self) -> Address:
        return self._addr
    
    @addr.setter
    def addr(self, value: Address) -> None:
        if not isinstance(value, Address):
            raise TypeError("Address should be an `Address` object!")
        self._addr = value
    
    def _check_state(self) -> bool:
        """Check if Port is up in network.

        Returns:
            bool -- Port state.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)
        state = sock.connect_ex((str(self._addr), self._value))
        sock.close()
        return True if state == 0 else False

    def __int__(self) -> int:
        return self._value
    
    def __bool__(self) -> bool:
        return True if bool(self._addr) and self._check_state() else False
    
    def __str__(self) -> str:
        return f"{self.addr}:{self.value}"


class Octet:
    """Class for representing address Octet value.

    Arguments:
        value (int|str) -- Value of octet (in range 0-255).
        ignore_range [opt] (bool) -- Allow for value out of 0-255 range (Default: False).
    """

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
        """Check if value is 8-bit binary."""
        return True if len(value) == (value.count("1") + value.count("0")) and len(value) == 8 else False

    def get_binary(self) -> str:
        """Return binary representation of octet value."""
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
