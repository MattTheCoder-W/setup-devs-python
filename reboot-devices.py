from classes.finder import Finder
from classes.address import Address
from classes.connector import Executor
from classes.port import Port
from classes.sshtools import find_ssh_password

import random
from argparse import ArgumentParser
import datetime
import dateutil.parser
import os

parser = ArgumentParser(description="Randomly reboot devices between two points in time.")
parser.add_argument("address", type=str, help="Network address")
parser.add_argument("mask", type=str, help="Mask address")
parser.add_argument("uname", type=str, help="Username on all devices")
parser.add_argument("passwords", type=str, help="Password list or path to file with password list in it")
parser.add_argument("time", type=str, help="Time Inverval (START-END)")
args = vars(parser.parse_args())

if not os.path.exists(args['passwords']) or not os.path.isfile(args['passwords']):
    passwds = args['passwords'].split(" ")
else:
    with open(args['passwords'], "r") as f:
        passwds = [line.strip() for line in f.readlines()]

uname = args['uname']

start, end = args['time'].split("-")
start = dateutil.parser.parse(start)
end = dateutil.parser.parse(end)

if (start - datetime.datetime.now()).total_seconds() < 0:
    start += datetime.timedelta(days=1)
    end += datetime.timedelta(days=1)

devices = Finder(Address(args['address']), Address(args['mask'])).find_all()

print("Found", len(devices), "devices!")
print("Generating random minutes...")

choosen = []
minutes = list(range(0, int((end-start).total_seconds()//60)))

for _ in range(len(devices)):
    delta = random.choice(minutes)
    cur_date = start + datetime.timedelta(minutes=delta)
    choosen.append(cur_date)
    minutes.remove(delta)

print("Random minutes generated!")

for i, addr in enumerate(devices):
    if not bool(Port(addr, 22)):
        continue

    exec_time = choosen[i]
    print(f"{addr} will reboot at {exec_time}")

    passwd = find_ssh_password(addr, uname, passwds)
    if passwd is None:
        print(f"Correct password not found for {addr}!")
        continue
    
    try:
        airos = Executor(str(addr), 22, uname, passwd)
        print(f"Logged in with uname={uname}, passwd={passwd}")
    except NoValidConnectionsError:
        print(f"{addr} not SSH")
        continue
    except AuthenticationException:
        raise ValueError(f"Password `{passwd}` is not valid!")

    target_seconds = int(round((exec_time - datetime.datetime.now()).total_seconds(), 0))
    print(f"Device will reboot in {target_seconds} seconds")
    if len(airos.exec(f"sleep {target_seconds} && reboot &")[1]):
        print("Error occured while executing command!")
    
print("All devices done!")
