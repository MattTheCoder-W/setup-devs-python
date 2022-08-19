from .address import Address
from .network import Network
from argparse import ArgumentParser
import os
import concurrent.futures


class Finder:
    """
    Klasa Finder znajduje wszystkie aktywne adresy z danej sieci.
    """
    def __init__(self, addr: Address, mask: Address) -> None:
        self.addr = addr
        self.mask = mask
        self.found = []

    def find_all(self) -> list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            executor.map(self.check_host, Network(self.addr, self.mask).addresses)
        return self.found

    def check_host(self, addr: Address) -> bool:
        if bool(addr):
            self.found.append(addr)
            return True
    