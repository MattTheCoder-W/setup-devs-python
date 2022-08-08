from finder import Finder
from iplist import Address
from connector import Executor

from paramiko.ssh_exception import SSHException
from paramiko.ssh_exception import NoValidConnectionsError
import os
import copy


class Configurator:
    _cfg = {}
    def __ini__(self, cfg: dict) -> None:
        pass

    @property
    def cfg(self) -> dict:
        return self._cfg
    
    @cfg.setter
    def cfg(slef, value: dict) -> None:
        if not isinstance(value, dict):
            raise TypeError("Cfg value must be dictionary!")
        self._cfg = value

    def set_dns(self) -> None:
        self._cfg["resolv.nameserver.1.ip"] = "91.232.50.10"
        self._cfg["resolv.nameserver.2.ip"] = "91.232.52.10"
        self._cfg["resolv.nameserver.1.status"] = "enabled"
        self._cfg["resolv.nameserver.2.status"] = "enabled"

    def set_snmp(self) -> None:
        self._cfg["snmp.status"] = "enabled"
        self._cfg["snmp.community"] = "local"
        self._cfg["snmp.contact"] = "test-skryptu@net.com"
        self._cfg["snmp.location"] = "Banino"

    def set_ntp(self) -> None:
        self._cfg["ntpclient.status"] = "enabled"
        self._cfg["ntpclient.1.status"] = "enabled"
        self._cfg["ntpclient.1.server"] = "91.232.52.123"

    def set_timezone(self, number: int) -> None:
        if not isinstance(number, int):
            raise TypeError("Timezone number should be int!")
        self._cfg["system.timezone"] = f"GMT-{number}"

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


finder = Finder(Address("192.168.1.0"), Address(24, is_mask=True))
devices = finder.find_all()

if not len(devices):
    print("No devices in network!")
    exit(0)

uname = "ubnt"
passwd = "1234"
new_passwd = "1234"
for addr in devices:
    print("Trying:", str(addr))
    try:
        airos = Executor(str(addr), 22, uname, passwd)
    except NoValidConnectionsError:
        print(f"{addr} not SSH")
        continue

    airos.exec("cp /tmp/system.cfg ~/system.cfg.bak")

    raw_cfg = [x.strip().split("=") for x in airos.read_file("/tmp/system.cfg")]
    def_cfg = {}
    for elem in raw_cfg:
        def_cfg[elem[0]] = elem[1]

    conf = Configurator(copy.deepcopy(def_cfg))
    conf.set_dns()
    conf.set_snmp()
    conf.set_ntp()
    conf.set_timezone("-1")
    airos.change_password(new_passwd)
    conf.change_passwd(uname, new_passwd, airos)
    conf.set_complience_test(airos)

    new_cfg = conf.cfg
    new_cfg_lines = [f"{elem_key}={new_cfg[elem_key]}\n" for elem_key in list(new_cfg.keys())]

    if new_cfg_lines != raw_cfg:
        print(new_cfg_lines)
        open("local-system.cfg", "w").writelines(new_cfg_lines)
        if os.system(f'sshpass -p "{new_passwd}" scp -O local-system.cfg {uname}@{str(addr)}:/tmp/system.cfg') == 0:
            print("Configuration saved!")
            print(airos.exec("cfgmtd -w && reboot"))
        else:
            raise Exception("Error while uploading configuration file!")

    airos.close()
    