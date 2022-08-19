from classes.finder import Finder
from classes.address import Address
from classes.connector import Executor
from classes.port import Port
from classes.sshtools import find_ssh_password

from paramiko.ssh_exception import SSHException, NoValidConnectionsError, AuthenticationException
import os
import copy
import argparse


class Configurator:
    """
    Klasa Configurator ma na celu odpowiednią zmianę
    konfiguracji przekazanej w postaci słownika.

    Sama klasa nie wgrywa konfiguracji na urządzenie.
    """
    _cfg = {}  # Configuration variable
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.languages = ["pl_PL", "en_US"]

    @property
    def cfg(self) -> dict:
        return self._cfg
    
    @cfg.setter
    def cfg(self, value: dict) -> None:
        if not isinstance(value, dict):
            raise TypeError("Cfg value must be dictionary!")
        self._cfg = value

    def set_dns(self, dns1: Address, dns2: Address = None) -> None:
        # Ustawianie adresów DNS
        self._cfg["resolv.nameserver.1.ip"] = str(dns1)
        self._cfg["resolv.nameserver.1.status"] = "enabled"
        if dns2 is not None:
            self._cfg["resolv.nameserver.2.status"] = "enabled"
            self._cfg["resolv.nameserver.2.ip"] = str(dns2)

    def set_snmp(self, community: str, contact: str, location: str) -> None:
        # Ustawianie parametrów SNMP
        self._cfg["snmp.status"] = "enabled"
        self._cfg["snmp.community"] = community
        self._cfg["snmp.contact"] = contact
        self._cfg["snmp.location"] = location

    def set_ntp(self, addr: Address) -> None:
        # Ustawianie adresu NTP
        self._cfg["ntpclient.status"] = "enabled"
        self._cfg["ntpclient.1.status"] = "enabled"
        self._cfg["ntpclient.1.server"] = addr

    def set_timezone(self, number: str) -> None:
        # Ustawianie strefy czasowej (w formacie GMT-X)
        self._cfg["system.timezone"] = f"GMT{number}"

    def change_passwd(self, uname: str, new_password: str, airos: Executor) -> None:
        # Zmiana hasła na urządzeniu
        airos.change_password(new_password)  # Najpierw, zmieniane jest hasło poprzez SSH
        
        # Następnie pozyskiwany jest hash hasła z pliku /etc/passwd
        passwd_hash = airos.read_file("/etc/passwd")
        for line in passwd_hash:
            if uname in line:
                passwd_hash = line.split(":")
                break
        for i, elem in enumerate(passwd_hash):
            if uname in elem:
                passwd_hash = passwd_hash[i+1]
                break

        # Pozyskany hash zapisywany jest w konfiguracji urządzenia
        # Dzięki temu nie zostanie przywrócone stare hasło po ponownym uruchomieniu.
        self._cfg['users.1.password'] = passwd_hash

    def enable_compliance_test(self, airos: Executor) -> None:
        # Włączanie "Compliance test"
        airos.exec("touch /etc/persistent/ ct")
        self._cfg['radio.1.countrycode'] = "511"
        self._cfg['radio.countrycode'] = "511"
        self._cfg['radio.1.dfs.status'] = "disabled"
    
    def disable_compliance_test(self, airos: Executor) -> None:
        # Wyłączanie "Compliance test"
        airos.exec("rm /etc/persistent/ct 2>/dev/null")
        self._cfg['radio.1.countrycode'] = "616"
        self._cfg['radio.countrycode'] = "616"
        self._cfg['radio.1.dfs.status'] = "enabled"

    def set_hostname(self, hostname: str) -> None:
        # Ustawianie nazwy hosta
        self._cfg["resolv.host.1.status"] = "enabled"
        self._cfg["resolv.host.1.name"] = hostname
    
    def change_language(self, language: str) -> None:
        # Zmiana języka (pl_PL lub en_US)
        if language not in self.languages:
            print("Language not in language list!")
            return
        self.cfg["gui.language"] = language


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated airos ssh configuration tool")
    parser.add_argument("net_address", type=str, help="Network address")
    parser.add_argument("mask", type=str, help="Mask address")
    parser.add_argument("uname", type=str, help="User name on devices")
    parser.add_argument("passwords", type=str, help="Password list or path to file with list")
    parser.add_argument("--do-restart", "-r", action="store_true", help="Perform reboot after saving configuration")
    parser.add_argument("--new-password", "-p", type=str, help="New password to set on all devices")
    parser.add_argument("--smart-passwords", type=str, help="Path to file with new passwords assigned to specific ip addresses. (format: IP:PASS)")
    args = vars(parser.parse_args())

    # Sprawdzanie czy użytkownik jako argument podał ścieżkę do pliku z hasłami czy listę haseł.
    if not os.path.exists(args['passwords']) or not os.path.isfile(args['passwords']):
        passwords = args['passwords'].split(" ")
    else:
        with open(args['passwords'], "r") as f:
            passwords = [line.strip() for line in f.readlines()]

    # Pozyskiwanie listy urządzeń w wybranej sieci
    devices = Finder(Address(args['net_address']), Address(int(args['mask']))).find_all()

    if not len(devices):
        # Brak urządzeń w sieci
        print("No devices in network!")
        exit(0)

    # Zmienne do sposobu konfiguracji urządzeń
    do_restart = args['do_restart']
    uname = args['uname']
    change_passwd = smart_passwords = True
    new_passwd = args['new_password']

    if args['smart_passwords'] is not None:
        # Wczytywanie haseł przypisanych do adresów ip z podanej ścieżki

        if not os.path.exists(args['smart_passwords']) or not os.path.isfile(args['smart_passwords']):
            raise FileNotFoundError("Specified smart passwords file does not exist:", args['smart_passwords'])
        
        smart_passwords, new_passwds = [True, {}]
        with open(args['smart_passwords'], "r") as f:
            for line in [line.strip() for line in f.readlines()]:
                try:
                    ip_addr, passwd = line.split("$to$")
                except ValueError:
                    raise ValueError("Incorrect smart passwords file content!")
                new_passwds[ip_addr] = passwd
        print("Loaded smart passwords!")

    # Konfiguracja wszystkich urządzeń w sieci
    for addr in devices:
        print(f"Trying: {str(addr)}")
        if not bool(Port(addr, 22)):
            print(f"SSH port not open at {addr}")
            continue

        print("Searching for password...")
        passwd = find_ssh_password(addr, uname, passwords)  # Funkcja z pliku classes/sshtools.py
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

        airos.exec("cp /tmp/system.cfg ~/system.cfg.bak")

        raw_cfg = [x.strip().split("=") for x in airos.read_file("/tmp/system.cfg")]
        def_cfg = {}
        for elem in raw_cfg:
            def_cfg[elem[0]] = elem[1]

        # Główna konfiguracja
        conf = Configurator(copy.deepcopy(def_cfg))
        conf.set_dns(Address("91.232.50.10"), Address("91.232.52.10"))
        conf.set_snmp("local", "test.skryptu.bez.restartu@test.local", "Banino")
        conf.set_ntp(Address("91.232.52.123"))
        conf.set_timezone("-1")
        conf.disable_compliance_test(airos)
        
        # Zmiana hasła
        if smart_passwords:
            try:
                new_passwd = new_passwds[str(addr)]
            except KeyError:
                new_passwd = passwd
                
        if change_passwd or smart_passwords:
            airos.change_password(new_passwd)
            conf.change_passwd(uname, new_passwd, airos)

        # Konwersja słownika nowej konfiguracji do listy linijek tekstu (do zapisu na urządzeniu)
        new_cfg = conf.cfg
        new_cfg_lines = [f"{elem_key}={new_cfg[elem_key]}\n" for elem_key in list(new_cfg.keys())]

        if new_cfg_lines != raw_cfg:  # Jeżeli nastąpiła jakakolwiek zmiana w konfiguracji
            open("local-system.cfg", "w").writelines(new_cfg_lines)  # Zapis lokalnego pliku nowej konfiguracji.
            print(f"Trying to upload configuration file with `{new_passwd}` password")

            # Próba przesłania pliku na urządzenie (z wykorzystaniem nowego hasła jeżeli zostało ono zmienione)
            if os.system(f'sshpass -p "{new_passwd}" scp -o StrictHostKeyChecking=no -O local-system.cfg {uname}@{str(addr)}:/tmp/system.cfg') == 0:
                print("Configuration saved!")
                airos.exec("cfgmtd -w && reboot") if do_restart else airos.exec("cfgmtd -w")
                print("Configuration applied!")
            else:
                raise Exception("Error while uploading configuration file!")
            os.remove("local-system.cfg")

        airos.close()

    print("Successfully configured all devices!")
