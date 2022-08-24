##############################################
# Automatic Configuration of Ubiquiti Devices
# Author: MattTheCoder-W
##############################################

import os.path
import argparse
from copy import deepcopy
from paramiko.ssh_exception import SSHException, NoValidConnectionsError, AuthenticationException

from classes.finder import Finder
from classes.address import Address, Port
from classes.connector import Executor
from classes.sshtools import find_ssh_password


class Configurator:
    """Edit ubiquiti device configuration.

    This class does not upload configuration onto device!
    It only modify downloaded configuration.

    Arguments:
        cfg (dict) -- Configuration from ubnt device.

    Methods:
        set_dns -- Set DNS addresses
        set_snmp -- Set SNMP info
        set_ntp -- Set NTP address
        set_timezone -- Set device timezone
        change_passwd -- Change ubnt user password
        enable_compliance_test -- Enable compliance test
        disable_compliance_test -- Disable compliance test
        set_hostname -- Set device hostname
        change_language -- Change device Web Configuration language
    """

    cfg = {}  # Device configuration -- {property_name: property_value}
    languages = ["pl_PL", "en_US"]  # Supported languages
    
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
 
    @cfg.setter
    def cfg(self, value: dict) -> None:
        if not isinstance(value, dict):
            raise TypeError("Configuration must be dictionary!")
        self.cfg = value

    def set_dns(self, dns1: Address, dns2: Address = None) -> None:
        """Set DNS addresses (only one is required)."""
        self.cfg["resolv.nameserver.1.ip"] = str(dns1)
        self.cfg["resolv.nameserver.1.status"] = "enabled"
        if dns2 is not None:
            self.cfg["resolv.nameserver.2.status"] = "enabled"
            self.cfg["resolv.nameserver.2.ip"] = str(dns2)

    def set_snmp(self, community: str, contact: str, location: str) -> None:
        """Set SNMP related information."""
        self.cfg["snmp.status"] = "enabled"
        self.cfg["snmp.community"] = community
        self.cfg["snmp.contact"] = contact
        self.cfg["snmp.location"] = location

    def set_ntp(self, addr: Address) -> None:
        """Set NTP address."""
        self.cfg["ntpclient.status"] = "enabled"
        self.cfg["ntpclient.1.status"] = "enabled"
        self.cfg["ntpclient.1.server"] = str(addr)

    def set_timezone(self, number: str) -> None:
        """Set timezone in `GMTX` format."""
        self.cfg["system.timezone"] = f"GMT{number}"

    def change_passwd(self, uname: str, new_password: str, airos: Executor) -> None:
        """Change password on ubnt device and apply it to system configuration.

        In order to change password on ubnt devices permanently:
            - Change it in terminal using SSH (paramiko).
            - Get new password hash from `/etc/passwd`.
            - Write new password hash to conf file in `users.1.password` field.
        
        Parameters:
            uname (str) -- Account username on device.
            new_password (str) -- New password.
            airos (Executor) -- Executor calss object with active connection.
        """
        airos.change_password(new_password)  # SSH part
        
        # Get hash from /etc/passwd
        passwd_hash = airos.read_file("/etc/passwd")  
        for line in passwd_hash:
            if uname in line:
                passwd_hash = line.split(":")
                break
        for i, elem in enumerate(passwd_hash):
            if uname in elem:
                passwd_hash = passwd_hash[i+1]
                break

        self.cfg['users.1.password'] = passwd_hash  # Apply hash in configuration

    def enable_compliance_test(self, airos: Executor) -> None:
        """Enable Compliance Test."""
        airos.exec("touch /etc/persistent/ ct")
        self.cfg['radio.1.countrycode'] = "511"
        self.cfg['radio.countrycode'] = "511"
        self.cfg['radio.1.dfs.status'] = "disabled"
    
    def disable_compliance_test(self, airos: Executor) -> None:
        """Disable Compliance Test"""
        airos.exec("rm /etc/persistent/ct 2>/dev/null")
        self.cfg['radio.1.countrycode'] = "616"
        self.cfg['radio.countrycode'] = "616"
        self.cfg['radio.1.dfs.status'] = "enabled"

    def set_hostname(self, hostname: str) -> None:
        """Set device hostname."""
        self.cfg["resolv.host.1.status"] = "enabled"
        self.cfg["resolv.host.1.name"] = hostname
    
    def change_language(self, language: str) -> None:
        """Change device Web Configuration language."""
        if language not in self.languages:
            print("Language not in language list!")
            return
        self.cfg["gui.language"] = language


if __name__ == "__main__":
    # Parse user arguments using argparse
    parser = argparse.ArgumentParser(description="Automated airos ssh configuration tool")
    parser.add_argument("net_address", type=str, help="Network address")
    parser.add_argument("mask", type=str, help="Mask address")
    parser.add_argument("uname", type=str, help="User name on devices")
    parser.add_argument("passwords", type=str, help="Password list or path to file with list")
    parser.add_argument("--do-restart", "-r", action="store_true", help="Perform reboot after saving configuration")
    parser.add_argument("--new-password", "-p", type=str, help="New password to set on all devices")
    parser.add_argument("--smart-passwords", type=str, help="Path to file with new passwords assigned to specific ip addresses. (format: IP:PASS)")
    args = vars(parser.parse_args())

    # Check if user provided password file path or list of passwords
    if not os.path.exists(args['passwords']) or not os.path.isfile(args['passwords']):
        passwords = args['passwords'].split(" ")
    else:
        with open(args['passwords'], "r") as f:
            passwords = [line.strip() for line in f.readlines()]

    # Get active devices in network
    devices = Finder(Address(args['net_address']), Address(int(args['mask']))).find_all()

    if not devices:
        print("No devices in network!")
        exit(0)

    do_restart: bool = args['do_restart']  # Flag for performing restart after saving configuration
    uname: str = args['uname'] 
    change_passwd = smart_passwords = True  # Password changing related flags
    new_passwd: str = args['new_password']

    # Load password assigned to specific IP Addresses
    if args['smart_passwords'] is not None:
        # Check if file exists
        if not os.path.exists(args['smart_passwords']) or not os.path.isfile(args['smart_passwords']):
            raise FileNotFoundError("Specified smart passwords file does not exist:", args['smart_passwords'])
        
        smart_passwords, new_passwds = [True, {}]
        with open(args['smart_passwords'], "r") as f:
            for line in [line.strip() for line in f.readlines()]:
                try:
                    ip_addr, passwd = line.split("$to$")
                except ValueError:  # Exception when `$to$` is not in any line of file
                    raise ValueError("Incorrect smart passwords file content!")
                new_passwds[ip_addr] = passwd  # Put values into new_passwds dict
        print("Loaded smart passwords!")

    CONFIGURED = 0  # Configured devices counter
    
    # Configuration of all devices in network
    for addr in devices:
        print(f"Trying: {str(addr)}")

        if not bool(Port(addr, 22)):
            print(f"SSH port not open at {addr}")
            continue

        print("Searching for password...")
        passwd = find_ssh_password(addr, uname, passwords)  # Function from `classes/sshtools.py`
        if new_passwd is None:
            change_passwd = False
            new_passwd = passwd
        if passwd is None:
            print("Correct password was not found!")
            continue
        print(f"Password found: {passwd}")

        try:
            airos = Executor(str(addr), 22, uname, passwd)
            print(f"Logged in with uname={uname}, passwd={passwd}", SUCCESS)
        except NoValidConnectionsError:
            print(f"{addr} not SSH", ERROR)
            continue
        except AuthenticationException:
            raise ValueError(f"Password `{passwd}` is not valid!")

        airos.exec("cp /tmp/system.cfg ~/system.cfg.bak")  # Backup current configuration

        raw_cfg = [x.strip().split("=") for x in airos.read_file("/tmp/system.cfg")]
        def_cfg = {}
        for elem in raw_cfg:
            def_cfg[elem[0]] = elem[1]

        # Main configuration part
        conf = Configurator(copy.deepcopy(def_cfg))
        conf.set_dns(Address("91.232.50.10"), Address("91.232.52.10"))
        conf.set_snmp("local", "test.skryptu.bez.restartu@test.local", "Banino")
        conf.set_ntp(Address("91.232.52.123"))
        conf.set_timezone("-1")
        conf.disable_compliance_test(airos)
        
        # Change password
        if smart_passwords:
            try:
                new_passwd = new_passwds[str(addr)]
            except KeyError:
                new_passwd = passwd  # Don't change password when device is not in smart-pass dict
                
        if change_passwd or smart_passwords:
            airos.change_password(new_passwd)
            conf.change_passwd(uname, new_passwd, airos)

        # Convert cfg dictionary into list of strings (for saving into file)
        new_cfg = conf.cfg
        new_cfg_lines = [f"{elem_key}={new_cfg[elem_key]}\n" for elem_key in list(new_cfg.keys())]

        if new_cfg_lines != raw_cfg:  # Only upload if any configuration change was made
            open("local-system.cfg", "w").writelines(new_cfg_lines)  # Save to local file
            print(f"Trying to upload configuration file with `{new_passwd}` password")

            # Try to upload file over ssh using new password (if changed)
            if os.system(f'sshpass -p "{new_passwd}" scp -o StrictHostKeyChecking=no -O local-system.cfg {uname}@{str(addr)}:/tmp/system.cfg') == 0:
                print("Configuration saved!")
                airos.exec("cfgmtd -w && reboot") if do_restart else airos.exec("cfgmtd -w")
                print("Configuration applied!")
            else:
                raise Exception("Error while uploading configuration file!")
            os.remove("local-system.cfg")

        airos.close()  # Close current connection
        CONFIGURED += 1

print(f"Successfully configured {CONFIGURED} devices!")
