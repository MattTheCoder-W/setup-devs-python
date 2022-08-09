from finder import Finder
from iplist import Address
from connector import Executor

from paramiko.ssh_exception import SSHException
from paramiko.ssh_exception import NoValidConnectionsError
from paramiko.ssh_exception import AuthenticationException
import os
import copy


class Configurator:
    _cfg = {}
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg

    @property
    def cfg(self) -> dict:
        return self._cfg
    
    @cfg.setter
    def cfg(self, value: dict) -> None:
        if not isinstance(value, dict):
            raise TypeError("Cfg value must be dictionary!")
        self._cfg = value

    def set_dns(self, dns1: Address, dns2: Address) -> None:
        self._cfg["resolv.nameserver.1.ip"] = str(dns1)
        self._cfg["resolv.nameserver.2.ip"] = str(dns2)
        self._cfg["resolv.nameserver.1.status"] = "enabled"
        self._cfg["resolv.nameserver.2.status"] = "enabled"

    def set_snmp(self, community: str, contact: str, location: str) -> None:
        self._cfg["snmp.status"] = "enabled"
        self._cfg["snmp.community"] = community
        self._cfg["snmp.contact"] = contact
        self._cfg["snmp.location"] = location

    def set_ntp(self, addr: Address) -> None:
        self._cfg["ntpclient.status"] = "enabled"
        self._cfg["ntpclient.1.status"] = "enabled"
        self._cfg["ntpclient.1.server"] = addr

    def set_timezone(self, number: str) -> None:
        self._cfg["system.timezone"] = f"GMT{number}"

    def change_passwd(self, uname: str, new_password: str, airos: Executor) -> None:
        airos.change_password(new_password)
        passwd_hash = airos.read_file("/etc/passwd")
        for line in passwd_hash:
            if uname in line:
                passwd_hash = line
                break
        passwd_hash = passwd_hash.split(":")
        for i, elem in enumerate(passwd_hash):
            if uname in elem:
                passwd_hash = passwd_hash[i+1]
                break
        self._cfg['users.1.password'] = passwd_hash

    def set_complience_test(self, airos: Executor) -> None:
        airos.exec("touch /etc/persistent/ ct")


passwords = [
    "ubnt",
    "Qwerty12",
    "haslo123"
]

finder = Finder(Address("192.168.1.0"), Address(24, is_mask=True))
devices = finder.find_all()

if not len(devices):
    print("No devices in network!")
    exit(0)

uname = "ubnt"
for addr in devices:
    print("Trying:", str(addr))
    skip = False
    for passwd in passwords:
        try:
            airos = Executor(str(addr), 22, uname, passwd)
            new_passwd = passwd
            print(f"Logged in with uname={uname}, passwd={passwd}")
        except NoValidConnectionsError:
            print(f"{addr} not SSH")
            skip = True
        except AuthenticationException:
            print(f"Password `{passwd}` is not valid, trying another")
            continue
        break

    if skip:
        continue

    airos.exec("cp /tmp/system.cfg ~/system.cfg.bak")

    raw_cfg = [x.strip().split("=") for x in airos.read_file("/tmp/system.cfg")]
    def_cfg = {}
    for elem in raw_cfg:
        def_cfg[elem[0]] = elem[1]

    conf = Configurator(copy.deepcopy(def_cfg))
    conf.set_dns(Address("91.232.50.10"), Address("91.232.52.10"))
    conf.set_snmp("local", "test.skryptu@test.local", "Banino")
    conf.set_ntp(Address("91.232.52.123"))
    conf.set_timezone("-1")
    # airos.change_password(new_passwd)
    # conf.change_passwd(uname, new_passwd, airos)
    conf.set_complience_test(airos)

    new_cfg = conf.cfg
    new_cfg_lines = [f"{elem_key}={new_cfg[elem_key]}\n" for elem_key in list(new_cfg.keys())]

    if new_cfg_lines != raw_cfg:
        print(new_cfg_lines)
        open("local-system.cfg", "w").writelines(new_cfg_lines)
        print(f"Trying to upload configuration file with `{new_passwd}` password")
        if os.system(f'sshpass -p "{new_passwd}" scp -o StrictHostKeyChecking=no -O local-system.cfg {uname}@{str(addr)}:/tmp/system.cfg') == 0:
            print("Configuration saved!")
            print(airos.exec("cfgmtd -w && reboot"))
        else:
            raise Exception("Error while uploading configuration file!")

    airos.close()
    