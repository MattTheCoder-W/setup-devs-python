from paramiko import SSHClient
from paramiko import AutoAddPolicy


class Executor:
    """
    Klasa Executor pozwala na komunikację z urządzeniem ubiquiti.
    """
    _addr = _port = _uname = _passwd = None
    def __init__(self, addr: str, port: int, uname: str, passwd: str) -> None:
        self._addr = addr
        self._port = port
        self._uname = uname
        self._passwd = passwd

        # Połączenie SSH
        self.client = SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.client.connect(self._addr, port=self._port, username=self._uname, password=self._passwd, banner_timeout=60)
        self.transport = self.client.get_transport()  # `transport` do sprawdzania czy połączenie jest aktywne
    
    @property
    def data(self) -> dict:
        # Zwraca podstawowe informacje o urządzeniu
        return {"addr": self._addr, "port": self._port, "uname": self._uname, "passwd": self._passwd}
    
    @property
    def active(self) -> bool:
        # Zwraca status połączenia
        return self.transport.is_active()

    def exec(self, cmd: str, path: str = None) -> list:
        # Wywołuje komendę na urządzniu (z opcjonalnym wyznaczeniem ścieżki wywołania)
        if not self.active:
            raise ConnectionAbortedError("Lost connection!")
        if path:
            cmd = f"cd {path}; {cmd}"
        stdin, stdout, stderr = self.client.exec_command(cmd)
        return [stdout.readlines(), stderr.readlines()]  # Zwaraca [Wynik wykonania, błedy wykonania]

    def exec_input(self, cmd: str, inpt: list) -> list:
        # Wywołuje komendę na urządzeniu z symulowaniem wejścia użytkownika
        # (co element z listy wciskany jest enter)
        if not self.active:
            raise ConnectionAbortedError("Lost connection!")
        stdin, stdout, stderr = self.client.exec_command(cmd)
        for line in inpt:
            stdin.write(line + "\n")
        stdin.close()
        return [stdout.readlines(), stderr.readlines()]  # Zwaraca [Wynik wykonania, błedy wykonania]

    def change_password(self, new_password: str) -> bool:
        # Zmienia hasło na urządzeniu
        if type(new_password) is not str:
            raise TypeError("Password should be string!")
        out, err = self.exec_input(f"passwd {self._uname}", [new_password, new_password])
        if len(err):
            print("Errors while changing password:")
            print(err)
            return False
        return True
    
    def list_files(self) -> list:
        # Zwraca listę plików znajdujących się w katalogu dommowym /etc/persistent
        out, err = self.exec("ls .")
        if len(err):
            print("Errors", err)
        return out
    
    def create_file(self, filename: str) -> bool:
        # Tworzy plik
        if type(filename) is not str:
            raise TypeError("Filename should be string!")
        if len(filename) == 0:
            raise ValueError("Filename should not be empty!")
        out, err = self.exec(f"touch {filename}")
        if len(err):
            print("Error while creating file:", err)
            return False
        return True

    def write_to_file(self, filename: str, lines: list, overwrite: bool = False) -> bool:
        # Wpisuje dane do pliku lub je dopisuje (opcja overwrite)
        if type(filename) is not str:
            raise TypeError("Filename should be string!")
        if len(filename) == 0:
            raise ValueError("Filename should not be empty!")
        if type(lines) is not list:
            raise TypeError("Lines should be a list!")
        if len(lines) == 0:
            raise ValueError("Cannor write empty lines list")
        mode = ">" if overwrite else ">>"
        out, err = self.exec(f'echo "' + '\n'.join(lines) + f'" {mode} {filename}')
        if len(err):
            print("Error while writing to file:", err)
            return False
        return True
    
    def read_file(self, filename: str) -> list:
        # Zwraca listę linijek tekstu z pliku
        if type(filename) is not str:
            raise TypeError("Filename should be string!")
        if len(filename) == 0:
            raise ValueError("Filename should not be empty!")
        out, err = self.exec(f'cat "{filename}"')
        if len(err):
            print("Error while reading file:", err)
            return []
        return out
    
    def get_location(self) -> str:
        # Zwraca ścieżkę katalogu domowego urządzenia 
        # (nie można stale zmieniać ścieżki,
        # gdyż co wywołanie polecenia przywracana jest do katalogu domowego)
        out, err = self.exec("pwd")
        if len(err):
            print("Error while getting location", err)
            return None
        return out[0].strip()

    def close(self):
        # Zamyka połączenie
        self.client.close()

    def __bool__(self) -> bool:
        # Zwraca status połączenia
        return self.active


def manual_test(airos: Executor):
    # Testy wywołania poleceń
    
    print("Lista plików", "="*25)
    for file in airos.list_files():
        print("File:", file.strip())
    
    print("Status", "="*25)
    print(bool(airos))

    print("Tworzenie pliku: created-by-python.txt", "="*25)
    print(airos.create_file("created-by-python.txt"))

    print("Wpisywanie do pliku: created-by-python.txt", "="*25)
    print(airos.write_to_file("created-by-python.txt", ['Hello', 'World!']))

    print("Czytanie z pliku: created-by-python.txt", "="*25)
    print(airos.read_file("created-by-python.txt"))

    print("Nadpisywanie pliku: created-by-python.txt", "="*25)
    print(airos.write_to_file("created-by-python.txt", ['Not', 'Any More!'], overwrite=True))
    
    print("Czytanie z pliku: created-by-python.txt", "="*25)
    print(airos.read_file("created-by-python.txt"))

    print("Domyślna lokalizacja użytkownika", "="*25)
    print("Pwd ->", airos.get_location())

    print("Wykonywanie komend w innym katalogu", "="*25)
    print(airos.exec("pwd", path="testdir"))
    

if __name__ == "__main__":
    airos = Executor("192.168.1.20", 22, "ubnt", "ubnt")
    manual_test(airos)
