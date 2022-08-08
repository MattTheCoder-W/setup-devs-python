from finder import Finder
from iplist import Address
from connector import Executor

from paramiko.ssh_exception import SSHException
from paramiko.ssh_exception import NoValidConnectionsError
import re
import os
import copy


def set_dns(cfg: dict) -> dict:
    cfg["resolv.nameserver.1.ip"] = "91.232.50.10"
    cfg["resolv.nameserver.2.ip"] = "91.232.52.10"
    cfg["resolv.nameserver.1.status"] = "enabled"
    cfg["resolv.nameserver.2.status"] = "enabled"
    return cfg

def set_snmp(cfg: dict) -> dict:
    cfg["snmp.status"] = "enabled"
    cfg["snmp.community"] = "local"
    cfg["snmp.contact"] = "test-skryptu@net.com"
    cfg["snmp.location"] = "Banino"
    return cfg

def set_ntp(cfg: dict) -> dict:
    cfg["ntpclient.status"] = "enabled"
    cfg["ntpclient.1.status"] = "enabled"
    cfg["ntpclient.1.server"] = "91.232.52.123"
    return cfg

def set_timezone(cfg: dict) -> dict:
    cfg["system.timezone"] = "GMT-1"
    return cfg

def change_passwd(uname: str, new_password: str, airos: Executor, cfg: dict) -> dict:
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
    cfg['users.1.password'] = passwd_hash
    return cfg

def set_complience_test(airos: Executor) -> None:
    airos.exec("touch /etc/persistent/ ct")

finder = Finder(Address("192.168.1.0"), Address(24, is_mask=True))

devices = finder.find_all()

if not len(devices):
    print("No devices in network!")
    exit(0)

uname = "ubnt"
passwd = "1234"
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

    new_cfg = copy.deepcopy(def_cfg)
    new_cfg = set_dns(def_cfg)
    new_cfg = set_snmp(new_cfg)
    new_cfg = set_ntp(new_cfg)
    new_cfg = set_timezone(new_cfg)
    airos.change_password("1234")
    new_cfg = change_passwd("ubnt", "1234", airos, new_cfg)
    set_complience_test(airos)

    new_cfg_lines = [f"{elem_key}={new_cfg[elem_key]}\n" for elem_key in list(new_cfg.keys())]

    if new_cfg_lines != raw_cfg:
        print(new_cfg_lines)
        open("local-system.cfg", "w").writelines(new_cfg_lines)
        if os.system('sshpass -p "1234" scp -O local-system.cfg ubnt@192.168.1.20:/tmp/system.cfg') == 0:
            print("Configuration saved!")
            print(airos.exec("cfgmtd -w && reboot"))
        else:
            raise Exception("Error while uploading file!")

    airos.close()
    