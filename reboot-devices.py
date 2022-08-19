##################################################
# Automatic Reboot Scheduler for Ubiquiti Devices
# Author: MattTheCoder-W
##################################################

import os.path
import random
import datetime
import dateutil.parser
from argparse import ArgumentParser
from paramiko.ssh_exception import SSHException, NoValidConnectionsError, AuthenticationException

from classes.finder import Finder
from classes.address import Address, Port
from classes.connector import Executor
from classes.sshtools import find_ssh_password

# Parse user arguments using argaprse in two modes:
# mode: reboot (plan reboots on devices)
# mode: clear (remove all planed reboots from devices)
parser = ArgumentParser(description="Randomly reboot devices between two points in time.")
subparsers = parser.add_subparsers(help="sub-command help")

# Reboot mode arguments
reboot_parser = subparsers.add_parser("reboot", help="Reboot devices in network")
reboot_parser.add_argument("address", type=str, help="Network address")
reboot_parser.add_argument("mask", type=str, help="Mask address")
reboot_parser.add_argument("uname", type=str, help="Username on all devices")
reboot_parser.add_argument("passwords", type=str, help="Password list or path to file with password list in it")
reboot_parser.add_argument("time", type=str, help="Time Inverval (START-END)")

# Clear mode arguments
undo_parser = subparsers.add_parser("clear", help="Clear all pending reboots")
undo_parser.add_argument("address", type=str, help="Network address")
undo_parser.add_argument("mask", type=str, help="Mask address")
undo_parser.add_argument("uname", type=str, help="Username on all devices")
undo_parser.add_argument("passwords", type=str, help="Password list or path to file with password list in it")

args = vars(parser.parse_args())

# Check if user specified passwords file path or password list
if not os.path.exists(args['passwords']) or not os.path.isfile(args['passwords']):
    passwds = args['passwords'].split(" ")
else:
    with open(args['passwords'], "r") as f:
        passwds = [line.strip() for line in f.readlines()]

uname = args['uname']

if "time" in args:  # "time" is in args dict when user run `reboot` mode
    start, end = args['time'].split("-")
    start = dateutil.parser.parse(start)
    end = dateutil.parser.parse(end)

    # When specified interval is in the past, move it to next day
    if (start - datetime.datetime.now()).total_seconds() < 0:
        start += datetime.timedelta(days=1)
        end += datetime.timedelta(days=1)

# Get all active devices in network
devices = Finder(Address(args['address']), Address(args['mask'])).find_all()

print("Found", len(devices), "devices!")
if "time" in args:  # Reboot mode
    print("Generating random minutes...")

    choosen = []
    minutes = list(range(0, int((end-start).total_seconds()//60)))  # List of possible minutes

    for _ in range(len(devices)):
        # For every device pick random minute and add it to start time
        delta = random.choice(minutes)
        cur_date = start + datetime.timedelta(minutes=delta)
        choosen.append(cur_date)
        minutes.remove(delta)

    print("Random minutes generated!")

for i, addr in enumerate(devices):
    if not bool(Port(addr, 22)):  # Check for ssh connection
        continue

    if "time" in args:
        exec_time = choosen[i]
        print(f"{addr} will reboot at {exec_time}")

    passwd = find_ssh_password(addr, uname, passwds)  # Function from `classes/sshtools.py`
    if passwd is None:
        print(f"Correct password not found for {addr}!")
        continue
    
    try:
        # Connect to device
        airos = Executor(str(addr), 22, uname, passwd)
        print(f"Logged in with uname={uname}, passwd={passwd}")
    except NoValidConnectionsError:  # SSH was closed
        print(f"{addr} not SSH")
        continue
    except AuthenticationException:  # Wrong password
        raise ValueError(f"Password `{passwd}` is not valid!")

    if "time" in args:
        # Convert picked delay in minutes into seconds
        target_seconds = int(round((exec_time - datetime.datetime.now()).total_seconds(), 0))
        print(f"Device will reboot in {target_seconds} seconds")
        # Reboot device after `target_seconds` seconds
        if len(airos.exec(f"sleep {target_seconds} && reboot &")[1]):
            print("Error occured while executing command!")
    else:  # Clear mode
        _, err = airos.exec("killall sleep")  # Kill all sleep processes (scheduled reboots)
        if err:
            print("error while executing killall command:", err)
        else:
            print(f"Pending reboots cleared for {addr}")
    
print("All devices done!")
