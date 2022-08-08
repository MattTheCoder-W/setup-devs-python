from iplist import IPList, Address
from argparse import ArgumentParser
import os
import concurrent.futures


class Finder:
    def __init__(self, addr: Address, mask: Address) -> None:
        self.addr = addr
        self.mask = mask
        self.found = []

    def find_all(self) -> list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            executor.map(self.check_host, IPList().get_range(self.addr, self.mask))
        return self.found

    def check_host(self, addr: Address) -> bool:
        if bool(addr):
            self.found.append(addr)
            return True
    