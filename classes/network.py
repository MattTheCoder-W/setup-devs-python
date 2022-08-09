from .address import Address
from .octet import Octet
from abc import ABC, abstractmethod, abstractproperty
import copy


class iNetwork(ABC):
    @abstractproperty
    def addr(self):
        pass

    @abstractproperty
    def net_addr(self):
        pass

    @abstractproperty
    def broad_addr(self):
        pass

    @abstractproperty
    def addresses(self):
        pass

    @abstractproperty
    def hosts(self):
        pass


class Network(iNetwork):
    _addr = _mask = _net_addr = _broad_addr = _addresses = _hosts = _n_hosts = None
    def __init__(self, addr: Address, mask: Address) -> None:
        self.addr = addr
        self.mask = mask
        self.net_setup()
    
    @property
    def addr(self) -> Address:
        return self._addr
    
    @addr.setter
    def addr(self, value: Address) -> None:
        if not isinstance(value, Address):
            raise TypeError("Network creation address have to be Address object!")
        self._addr = value

    @property
    def mask(self) -> Address:
        return self._mask
    
    @mask.setter
    def mask(self, value: Address) -> None:
        if not isinstance(value, Address):
            raise TypeError("Network creation address have to be Address object!")
        if "01" in value.get_binary():
            raise ValueError(f"{value} is not a mask address!")
        self._mask = value

    @property
    def net_addr(self) -> Address:
        return self._net_addr
    
    @net_addr.setter
    def net_addr(self, value: Address) -> None:
        if not isinstance(value, Address):
            raise TypeError("Cannot assign not Address to address value")
        self._net_addr = value

    @property
    def broad_addr(self) -> Address:
        return self._broad_addr

    @broad_addr.setter
    def broad_addr(self, value: Address) -> None:
        if not isinstance(value, Address):
            raise TypeError("Cannot assign not Address to address value")
        self._broad_addr = value

    @property
    def hosts(self) -> list:
        return self.addresses[1:-1]

    @hosts.setter
    def hosts(self, value: list) -> None:
        if type(value) is not list or not all([isinstance(x, Address) for x in value]):
            raise TypeError("Invalid types in hosts value!")
        self._hosts = value

    @property
    def addresses(self) -> list:
        if self._net_addr is None or self._broad_addr is None:
            raise ValueError("Network was not initialized!")
        addresses = []
        cur_addr = copy.copy(self._net_addr)
        while cur_addr < self._broad_addr:
            addresses.append(cur_addr)
            cur_addr += 1
        return addresses
    
    @addresses.setter
    def addresses(self, value: list) -> None:
        if type(value) is not list or not all([isinstance(x, Address) for x in value]):
            raise TypeError("Invalid types in hosts value!")
        self._addresses = value

    @property
    def n_hosts(self) -> int:
        return self._n_hosts
    
    @n_hosts.setter
    def n_hosts(self, _) -> None:
        raise Exception("Cannot set this value!")
    
    def net_setup(self) -> None:
        if self._addr is None or self._mask is None:
            raise ValueError("Address or mask is not set!")
        bin_net_addr = ''.join(["0" if self._mask.get_binary()[x] == "0" else self._addr.get_binary()[x] for x in range(32)])
        self._net_addr = Address(bin_net_addr)
        bin_broad_addr = ''.join(["1" if self._mask.get_binary()[x] == "0" else self._addr.get_binary()[x] for x in range(32)])
        self._broad_addr = Address(bin_broad_addr)
        self._n_hosts = 2**(32-int(self._mask)) - 2
    
    def get_difference_mask(self, sub_mask: Address) -> Address:
        if not isinstance(sub_mask, Address) or not sub_mask.mask:
            raise TypeError("Sub Mask should be Mask Address!")
        str_mask1, str_mask2 = [self._mask.get_binary(), sub_mask.get_binary()]
        str_diff_mask = ""
        for i in range(32):
            if str_mask1[i] != str_mask2[i]:
                str_diff_mask += "1"
            else:
                str_diff_mask += "0"
        return Address(str_diff_mask)

    def get_sub_networks(self, mask: Address) -> list:
        if not isinstance(mask, Address):
            raise TypeError("Mask address should be `Address` object")
        n_subnets = 2**abs(int(self._mask) - int(mask))
        diff_mask = self.get_difference_mask(mask)
        cur_net_addr = copy.deepcopy(self._net_addr)
        sub_nets = []
        for i in range(n_subnets):
            sub_nets.append(SubNetwork(self, copy.deepcopy(cur_net_addr), mask))
            cur_net_addr = cur_net_addr.increment_with_difference_mask(diff_mask)
        return sub_nets


class SubNetwork(Network):
    _parent = _mask = _addr = None
    def __init__(self, parent: Network, addr: Address, mask: Address) -> None:
        self.parent = parent
        self.mask = mask
        self.addr = addr
    
    @property
    def parent(self) -> Network:
        if self._parent is None:
            raise ValueError("Parent Network is not set!")
        return self._parent
    
    @parent.setter
    def parent(self, value: Network) -> None:
        if not isinstance(value, Network):
            raise TypeError("Wrong value type!")
        self._parent = value
    
    @property
    def addr(self) -> Address:
        if self._addr is None:
            raise ValueError("Address of SubNetwork is not set!")
        return self._addr

    @addr.setter
    def addr(self, value: Address) -> None:
        if not isinstance(value, Address):
            raise TypeError("Wrong value type!")
        bin_addr = ''.join(["0" if self._mask.get_binary()[x] == "0" else value.get_binary()[x] for x in range(32)])
        self._addr = Address(bin_addr)
    
    @property
    def mask(self) -> Address:
        if self._mask is None:
            raise ValueError("Mask of SubNetwork is not set!")
        return self._mask

    @mask.setter
    def mask(self, value: Address) -> None:
        if not isinstance(value, Address):
            raise TypeError("Wrong value type!")
        if "01" in value.get_binary():
            raise ValueError(f"{value} is not a mask address!")
        self._mask = value
