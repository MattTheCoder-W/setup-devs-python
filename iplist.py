import unittest  # For class testing
from typing import Union, TypeVar  # Custom value types
import copy  # For copying objects
import os  # For pinging
import socket  # For port checking
import concurrent.futures  # For multithreading

from classes.icomparators import icomparators  # For comparing addresses
from classes.mathematics import imathematics  # For math on addresses
from classes.binary import binary_sum, binary_sub  # For binary math

TAddress = TypeVar("TAddress", bound="Address")


class Address(icomparators, imathematics):
	"""
	Address value class. Used for representing IPv4 addresses.

	Attributes:
		Positional:
			octets (str|list|int): address octets values
		
		Optional:
			is_binary (bool): flag for creating Address from binary values
			is_mask (bool): flag for creating mask Address
			ping_timeout (float): timeout in seconds to wait for validating connection
	"""
	_octets = []
	_binary = []
	_mask = False
	_ping_timeout = 0.1
	def __init__(self, octets: Union[str, list, int], is_mask: bool = False, ping_timeout: float = 0.1):
		self.ping_timeout = ping_timeout
		self.octets = octets
		self.mask = is_mask

	@property
	def ping_timeout(self) -> float:
		return self._ping_timeout
	
	@ping_timeout.setter
	def ping_timeout(self, value: float) -> None:
		if type(value) is not float:
			raise TypeError(f"Input value in wrong type! Got type: {type(value)}")
		self._ping_timeout = value

	@property
	def octets(self) -> list:
		return self._octets

	@octets.setter
	def octets(self, value: Union[str, list, int]) -> None:
		if type(value) is str or type(value) is list:
			if self._is_binary(value):
				value = self._binary_to_list(value)
			elif type(value) is str:
				value = [int(x) for x in value.split(".")]
		elif type(value) is int:
			if value not in range(0, 31):
				raise ValueError(f"Numerical address value not in range 0-30. Got value: {value}")
			value = [f"{'1'*int(value)}{'0'*(32-int(value))}"[x*8:(x+1)*8] for x in range(4)]
			value = self._binary_to_list(value)
			self.is_mask = True
		else:
			raise TypeError(f"Input value in wrong file! type: {type(value)}")
		if type(value) is not list:
			raise TypeError(f"Error while converting value to list! type: {type(value)}")
		for octet in value:
			if int(octet) not in range(0, 256):
				raise ValueError(f"Input value is not correct address! Got value: {value}")
		self._octets = value
		self.binary = [format(int(x), "#010b")[2:] for x in value]
	
	@property
	def binary(self) -> list:
		return self._binary
	
	@binary.setter
	def binary(self, value: Union[str, list]) -> None:
		if type(value) is str:
			value = [value[x*8:(x+1)*8] for x in range(4)]
		if type(value) is not list:
			raise TypeError(f"Input value in wrong type! Got type: {type(value)}")
		decimal = [int(str(x), 2) for x in value]
		self._binary = value
		self._octets = decimal
	
	@property
	def mask(self) -> bool:
		return self._mask
	
	@mask.setter
	def mask(self, value: bool) -> None:
		if type(value) is not bool:
			raise TypeError(f"Input value in wrong type! Got type: {type(value)}")
		self._mask = value

	def _binary_to_list(self, value: Union[str, list]) -> list:
		"""
		Convert binary address input into decimal octet list.

		Parameters:
			value (str|list): value to be converted
		
		Returns:
			list: list of decimal octets (ex. [192, 168, 0, 1])
		"""
		if type(value) is str:
			return [int(value[x*8:(x+1)*8], 2) for x in range(4)]
		elif type(value) is list:
			return [int(str(x), 2) for x in value]
		else:
			raise TypeError("Can convert binary to list only from string or list!")

	def _is_binary(self, value: Union[str, list]) -> bool:
		"""
		Check if input value is binary address.

		Parameters:
			value (str|list): address value to be checked
		
		Returns:
			bool: True -> Address is in binary format
		"""
		if type(value) is list:
			value = ''.join([str(x) for x in value])
		if value.count("1") + value.count("0") == len(value) and len(value) == 32:
			return True
		return False

	def get_binary(self, value: list = None, not_list: bool = False) -> Union[list, str]:
		"""
		Converts object octets into binary strings.

		Parameters (Optional):
			value (list): Convert given value, not objects addr
			not_list (bool): Returns binary value in one string
		
		Returns:
			list|str: octets in binary format
		"""
		binary_addr = [format(int(part), '#010b')[2:] for part in self._octets] if value is None else [format(int(part), '#010b') for part in value]
		if not_list:
			binary_addr = ''.join(binary_addr)
		return binary_addr

	# Find in which class given address is
	def get_class(self) -> str:
		"""
		Find class of objects address.

		Returns:
			str: class letter (A-E)
		"""
		classes = "ABCD"
		first_part = self._binary[0]
		for i in range(4):
			if first_part[i] == '0':
				return classes[i]
		return "E"
	
	# Check if address is private
	def get_private_network(self) -> Union[None, list]:
		"""
		Gives private addresses network based on objects class.

		Returns:
			None: Address doesn't have private addresses network
			or
			list: List of private network address and mask - [Address, Mask]
		"""
		addr_class = self.get_class()
		nets = {
			"A": [Address("10.0.0.0"), Address(8, is_mask=True)],
			"B": [Address("172.16.0.0"), Address(16, is_mask=True)],
			"C": [Address("192.168.0.0"), Address(24, is_mask=True)]
		}
		try:
			priv_net = nets[addr_class]
		except KeyError:
			return None
		return priv_net
	
	# Get default mask address based on class
	def get_def_mask(self) -> Union[None, TAddress]:
		"""
		Gives default address mask of objects class.

		Returns:
			None: Address doesn't have default mask
			or
			Address: Default mask address.
		"""
		def_masks = { "A": 8, "B": 16, "C": 24}
		try:
			def_mask = def_masks[self.get_class()]
		except KeyError:
			return None
		return Address(def_mask)

	def increment(self, value: int, mask: TAddress = None, only_return: bool = False) -> TAddress:
		"""
		Increment address by numerical value.

		Parameters:
			value (int): value to increment address by

			Optional:
				mask (Address): Difference mask for increment (used for subnets)
				only_return (bool): If True -> Doesn't update address of object
		
		Returns:
			Address: Incremented address
		"""
		str_addr = ''.join(self.get_binary())
		if mask is not None:
			mask = mask.get_binary(not_list = True)
			start, end = [mask.find("1"), mask.rfind("1")+1]
			str_part = binary_sum(str_addr[start:end], str(bin(value))[2:])
			str_addr = f"{str_addr[:start]}{str_part}{str_addr[end:]}"
		else:
			str_addr = binary_sum(str_addr, str(bin(value))[2:])
		if not only_return:
			self.binary = [str_addr[x*8:(x+1)*8] for x in range(4)]
			return self
		else:
			return Address(str_addr)
		
	def __bool__(self) -> bool:
		return True if os.system(f"ping -c 1 -W {self.ping_timeout} {str(self)} > /dev/null") == 0 else False

	def __str__(self):
		return f"{self.octets[0]}.{self.octets[1]}.{self.octets[2]}.{self.octets[3]}"

	def __iter__(self):
		return iter(list([int(x) for x in self.octets]))

	def __int__(self):
		if not self.mask:
			raise ValueError("Cannot describe not mask as decimal!")
		return ''.join(self.get_binary()).count("1")
	
	def __eq__(self, b: TAddress) -> bool:
		for i in range(4):
			if self.octets[i] != b.octets[i]:
				return False
		return True
	
	def __gt__(self, b: TAddress) -> bool:
		addr_sum = int(self.get_binary(not_list=True), 2)
		addr2_sum = int(b.get_binary(not_list=True), 2)
		return addr_sum > addr2_sum
	
	def __lt__(self, b: TAddress) -> bool:
		addr_sum = int(self.get_binary(not_list=True), 2)
		addr2_sum = int(b.get_binary(not_list=True), 2)
		return addr_sum < addr2_sum
	
	def __ge__(self, b: TAddress) -> bool:
		return self > b or self == b

	def __le__(self, b: TAddress) -> bool:
		return self < b or self == b

	def __ne__(self, b: TAddress) -> bool:
		return not self == b

	def __add__(self, value: int) -> TAddress:
		new_octets = copy.copy(self.octets)
		new_octets[-1] += value
		while max(new_octets) > 255:
			for i in range(4)[::-1]:
				if new_octets[i] > 255:
					if i-1 < 0:
						raise ValueError("Addition out of range!")
					new_octets[i-1] += 1
					new_octets[i] -= 255
		return Address(new_octets)
	
	def __sub__(self, value: int) -> TAddress:
		new_octets = copy.copy(self.octets)
		new_octets[-1] -= value
		while min(new_octets) < 0:
			for i in range(4)[::-1]:
				if new_octets[i] < 0:
					if i-1 < 0:
						raise ValueError("Substraction out of range!")
					new_octets[i-1] -= 1
					new_octets[i] += 255
		return Address(new_octets)
	
	def __iadd__(self, value: int) -> TAddress:
		self.octets = str(self + value)
		return self

	def __isub__(self, value: int) -> TAddress:
		self.octets = str(self - value)
		return self


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
			raise ValueError("Address should be an `Address` object!")
		self._addr = value
	
	def _check_state(self) -> bool:
		"""
		Check if this Port object is up in network. (Port is open)

		Returns:
			bool: Port state (Open/Closed)
		"""
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(0.1)
		state = sock.connect_ex((str(self._addr), self._value))
		sock.close()
		return True if state == 0 else False

	def __int__(self) -> int:
		return self._value
	
	def __bool__(self) -> bool:
		return True if bool(self._addr) and self._check_state() else False
	
	def __str__(self) -> str:
		return f"{self.addr}:{self.value}"


class IPList:
	"""
	Class for getting info about networks.

	Methods:
		get_info(addr: Address,
				mask: Address) -> dict: returns info about given network
		get_subnets(net_ip: Address,
				mask: Address,
				sub_mask: Address) -> dict: returns info about subnets in network
	"""
	def __init__(self):
		pass

	# Calculate differance mask between two given masks (mask1 - mask2)
	def get_diff_mask(self, mask1: Address, mask2: Address) -> Address:
		"""
		Calculate difference mask for subnet calculation.

		Parameters:
			mask1 (Address): First mask (of outer network)
			mask2 (Address): Second mask (of subnets)
		
		Returns:
			Address: Difference mask address
		"""
		str_mask1, str_mask2 = [mask1.get_binary(not_list=True), mask2.get_binary(not_list=True)]
		str_diff_mask = ""
		for i in range(32):
			if str_mask1[i] != str_mask2[i]:
				str_diff_mask += "1"
			else:
				str_diff_mask += "0"
		return Address(str_diff_mask)

	# Check if ip is in given network
	def is_ip_in_net(self, addr: Address, net_addr: Address, mask: Address) -> bool:
		"""
		Check if given ip is in given network.

		Parameters:
			addr (Address): Address to check
			net_addr (Address): Netowrk address
			mask (Address): Mask of network
		
		Returns:
			bool: True -> IP is in network, False -> IP is not in network
		"""
		net_addr = self.get_net_addr(net_addr, mask)
		broad_addr = self.get_broadcast(net_addr, mask)
		return addr >= net_addr and addr <= broad_addr
	
	def is_addr_private(self, addr: Address, mask: Address) -> bool:
		"""
		Check if address is private.

		Parameters:
			addr (Address): IP Address
			mask (Address): Mask Address
		
		Returns:
			bool: True -> Address is private, False -> Address is not private
		"""
		priv_net = addr.get_private_network()
		return self.is_ip_in_net(addr, priv_net[0], priv_net[1]) if priv_net is not None else False

	# Get network address based on given host address
	def get_net_addr(self, addr: Address, mask: Address) -> Address:
		"""
		Get network address of host.

		Parameters:
			addr (Address): Host IP address
			mask (Address): Mask of network
		
		Returns:
			Address: Address of hosts network
		"""
		bin_addr = addr.get_binary()
		bin_mask = mask.get_binary()
		net_addr = [''.join(["0" if bin_mask[i][j] == '0' else bin_addr[i][j] for j in range(8)]) for i in range(4)]
		return Address(net_addr)
	
	def get_broadcast(self, addr: Address, mask: Address) -> Address:
		"""
		Get boradcast address of host network.

		Parameters:
			addr (Address): Host IP address
			mask (Address): Mask of network
		
		Returns:
			Address: Broadcast address of hosts network
		"""
		bin_addr = addr.get_binary()
		bin_mask = mask.get_binary()
		broad_addr = [''.join(["1" if bin_mask[i][j] == '0' else bin_addr[i][j] for j in range(8)]) for i in range(4)]
		return Address(broad_addr)

	# Get all host addresses
	def get_range(self, addr: Address, mask: Address) -> list:
		"""
		Give list of addresses in given network.

		Parameters:
			addr (Address): Address of network
			mask (Address): Mask of network
		
		Returns:
			list: List of addresses [Address, ..., Address]
		"""
		n_addr = 2**(32 - int(mask))

		addresses = []
		net_addr = self.get_net_addr(addr, mask)

		with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
			for i in range(n_addr):
				executor.map(addresses.append(net_addr + i))
		return addresses

	# Get info of given address + mask
	def get_info(self, addr: Address, mask: Address) -> dict:
		"""
		Give info about host.

		Parameters:
			addr (Address): Host/Network Address
			mask (Address): Mask Address
		
		Returns:
			dict: Dictionary with info about host/network
		"""
		n_host = (2**(32 - int(mask))) - 2
		net_addr = self.get_net_addr(addr, mask)
		addresses = self.get_range(addr, mask)
		addr_class = addr.get_class()
		private = self.is_addr_private(addr, mask)

		info = {
			"address": addr,
			"mask": mask,
			"n_host": n_host,
			"network": net_addr,
			"broadcast": addresses[-1],
			"class": addr_class,
			"hosts": addresses[1:-1],
			"all_addr": addresses,
			"is_private": private,
			"class_mask": addr.get_def_mask()
		}
		return info

	# Get info about subnets
	def get_subnets(self, net_ip: Address, mask: Address, sub_mask: Address) -> dict:
		"""
		Give info about subnets with given mask

		Parameters:
			net_ip (Address): Address of network
			mask (Address): Mask of main network
			sub_mask (Address): Mask Address of sub-networks
		
		Returns:
			dict: Dictionary with info about all subnets
		"""
		net_addr = self.get_net_addr(net_ip, mask)
		n_subnets = 2**abs(int(mask) - int(sub_mask))

		diff_mask = self.get_diff_mask(mask, sub_mask)

		subnets_info = {
			"global_net_addr": net_addr,
			"n_subnets": n_subnets,
			"subnets": []
		}

		cur_net_addr = net_addr
		for i in range(n_subnets):
			cur_info = self.get_info(cur_net_addr, sub_mask)
			subnets_info['subnets'].append(cur_info)
			cur_net_addr.increment(1, mask=diff_mask)
		return subnets_info


# Class methods tests
class Tests(unittest.TestCase):
	"""
	Tests for Port, Address and IPList classes.
	"""
	def test_add_to_addr(self):
		self.assertEqual(str(Address([192, 168, 0, 1]).increment(5)), str(Address([192, 168, 0, 6])), "Wrong address sum!")
		self.assertEqual(str(Address([192, 168, 0, 255]).increment(1)), str(Address([192, 168, 1, 0])), "Wrong address sum!")

	def test_get_diff_mask(self):
		self.assertEqual(str(IPList().get_diff_mask(Address([255, 255, 255, 0]), Address([255, 255, 255, 192]))), str(Address([0, 0, 0, 192])), "Wrong diff mask!")

	def test_numeric_to_std(self):
		self.assertEqual(str(Address(24)), str(Address([255, 255, 255, 0])), "Wrong numeric to ipv4 conversion!")
		self.assertEqual(str(Address(20)), str(Address([255, 255, 240, 0])), "Wrong numeric to ipv4 conversion!")
	
	def test_mask_to_num(self):
		self.assertEqual(int(Address([255, 255, 255, 0], is_mask=True)), 24, "Wrong mask to numeric conversion!")
		self.assertEqual(int(Address([255, 255, 240, 0], is_mask=True)), 20, "Wrong mask to numeric conversion!")
		self.assertEqual(int(Address([255, 255, 255, 252], is_mask=True)), 30, "Wrong mask to numeric conversion!")
		self.assertEqual(int(Address([255, 0, 0, 0], is_mask=True)), 8, "Wrong mask to numeric conversion!")
	
	def test_check_addr(self):
		self.assertRaises(ValueError, lambda: Address("192.djf.123.123"))
		self.assertRaises(ValueError, lambda: Address("192.38445.123.123"))
		self.assertRaises(ValueError, lambda: Address("192.."))
		self.assertRaises(ValueError, lambda: Address(50))

	def test_ip_to_bin(self):
		self.assertEqual(Address([192, 168, 0, 52]).get_binary(), ["11000000", "10101000", "00000000", "00110100"], "Wrong IPv4 to binary conversion!")

	def test_bin_to_ip(self):
		self.assertEqual(str(Address(["11000000", "10101000", "00000000", "00110100"])), str(Address([192, 168, 0, 52])), "Wrong bianry to IPv4 conversion!")

	def test_get_class(self):
		self.assertEqual(Address([192, 168, 0, 1]).get_class(), "C", "Wrong class identifiaction!")

	def test_is_ip_in_net(self):
		self.assertEqual(IPList().is_ip_in_net(Address([192,168,0,1]), Address([192,168,0,0]), Address([255, 255, 255, 0], is_mask=True)), True, "Wrong IP in network confirmation!")
		self.assertEqual(IPList().is_ip_in_net(Address([192,168,0,1]), Address([10,0,0,0]), Address([255, 0, 0, 0], is_mask=True)), False, "Wrong IP in network confirmation!")

	def test_get_net_addr(self):
		self.assertEqual(str(IPList().get_net_addr(Address([192,168,0,52]), Address([255, 255, 255, 0], is_mask=True))), str(Address([192,168,0,0])), "Wrong Network Address calculation!")

	def test_is_addr_private(self):
		self.assertEqual(IPList().is_addr_private(Address([192, 168, 0, 10]), Address([255, 255, 255, 0], is_mask=True)), True, "Wrong Address private status!")
		self.assertEqual(IPList().is_addr_private(Address([192, 167, 0, 10]), Address([255, 255, 255, 0], is_mask=True)), False, "Wrong Address private status!")

	def test_get_def_mask(self):
		self.assertEqual(str(Address("10.0.0.1").get_def_mask()), str(Address([255, 0, 0, 0], is_mask=True)), "Wrong default mask!")
		self.assertEqual(str(Address("172.16.0.1").get_def_mask()), str(Address([255, 255, 0, 0], is_mask=True)), "Wrong default mask!")
		self.assertEqual(str(Address("192.168.0.1").get_def_mask()), str(Address([255, 255, 255, 0], is_mask=True)), "Wrong default mask!")

	def test_str_to_list(self):
		self.assertEqual(list(Address("192.168.0.1")), [192,168,0,1], "Wrong string to list!")

	def test_bin_to_list(self):
		self.assertEqual(Address("11000000101010000000000000110100").get_binary(), ["11000000", "10101000", "00000000", "00110100"], "Wrong bin-string to list!")
		self.assertEqual(str(Address("11000000101010000000000000110100")), "192.168.0.52", "Wrong bin-string to list with decoding!")

	### Port tests

	def test_port_value_str_to_int(self):
		self.assertEqual(Port(Address("127.0.0.1"), "80").value, 80, "Wrong port value type conversion!")
	
	def test_port_wrong_addr_detection(self):
		self.assertRaises(ValueError, lambda: Port("127.0.0.1", 80))
		self.assertRaises(ValueError, lambda: Port(24, 80))
		self.assertRaises(ValueError, lambda: Port(True, 80))
	
	### Test address camparing

	def test_address_comparing(self):
		addr1 = Address('192.168.0.1')
		addr2 = Address('192.168.0.1')
		self.assertEqual(addr1 == addr2, True, "Wrong address equal")
		self.assertEqual(addr1 > addr2, False, "Wrong address greater than")
		self.assertEqual(addr1 < addr2, False, "Wrong address less than")
		self.assertEqual(addr1 >= addr2, True, "Wrong address greater or equal")
		self.assertEqual(addr1 <= addr2, True, "Wrong address less or equal")
		self.assertEqual(addr1 != addr2, False, "Wrong address not equal")

		addr1 = Address('10.0.0.1')
		addr2 = Address('192.168.0.1')
		self.assertEqual(addr1 == addr2, False, "Wrong address equal")
		self.assertEqual(addr1 > addr2, False, "Wrong address greater than")
		self.assertEqual(addr1 < addr2, True, "Wrong address less than")
		self.assertEqual(addr1 >= addr2, False, "Wrong address greater or equal")
		self.assertEqual(addr1 <= addr2, True, "Wrong address less or equal")
		self.assertEqual(addr1 != addr2, True, "Wrong address not equal")
	
	### Test address math

	def test_address_math(self):
		addr = Address('192.168.0.1')
		self.assertEqual(str(addr + 1), "192.168.0.2", "Wrong address math add")
		self.assertEqual(str(addr + 255), "192.168.1.1", "Wrong address math add")
		self.assertEqual(str(addr - 1), "192.168.0.0", "Wrong address math substract")
		self.assertEqual(str(addr - 30), "192.167.254.226", "Wrong address math substract")

		addr = Address('192.168.0.1')
		addr += 1
		self.assertEqual(str(addr), "192.168.0.2", "Wrong iadd")

		addr = Address('192.168.0.1')
		addr -= 1
		self.assertEqual(str(addr), "192.168.0.0", "Wrong isub")


if __name__ == "__main__":
	unittest.main()
