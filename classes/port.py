import socket

from .address import Address


class Port:
    """
    Address + Port value. Representing socket with Address and Port values.

    Attributes:
        addr (Address): Address value of socket
        value (int): Port value of socket
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
        """
        Check if this Port object is up in network. (Port is open)

        Returns:
            bool: Port state (Open/Closed)
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
