### Automated airOS devices setup (Python)

## Requirements

Install required packages: `pip install -r requirements.txt`

---

## setup-dev-oop.py

### Usage

See Help Page: `python setup-dev-oop.py -h`

### Detailed usage

`usage: setup-dev-oop.py [-h] [--do-restart] [--new-password NEW_PASSWORD] [--smart-passwords SMART_PASSWORDS] net_address mask uname passwords`

argument | format | description
-------- | ------ | -----------
`net_address` | IP Address | Network address to configure devices in
`mask` | Mask Address | Mask address of network
`uname` | String | User name on all devices (for now it has to be the same)
`passwords` | File path or string | Path to file with list of passwords for devices or list of password serparated by space
`--do-restart` | None | When enabled devices will be rebooted after configuration
`--new-passwords` | String | Single password that will be set on all devices
`--smart-passwords` | File path | Path to file with specified new passwords for each IP Address

### Smart passwords file format

To correctly specify password for each ip address create file with list of ip addresses and passwords like this: `IP_ADDRESS$to$PASSWORD`

And put every record in new line.

---

## reboot-devices.py

Script that set reboot job for random time between specified hours.

### Usage

Help page: `python reboot-devices.py -h`

### Mode `reboot`

Create reboot jobs on devices in network/

Syntax for this mode: `python reboot-devices.py reboot address mask uname passwords time`

argument | type | description
-------- | ---- | -----------
`address` | IP Address | Network addres to work on
`mask` | Mask Address | Mask address of network
`uname` | String | User name on all devices
`passwords` | File path or string | List of passwords or file with list of passwords
`time` | String | Time interval in which devices should reboot (START_TIME-END_TIME, eg. 22:00-23:00)

### Mode `clear`

Removes all pending reboots on devices in network.

Syntax for this mode: `python reboot-devices.py clear address mask uname passwords`

argument | type | description
-------- | ---- | -----------
`address` | IP Address | Network addres to work on
`mask` | Mask Address | Mask address of network
`uname` | String | User name on all devices
`passwords` | File path or string | List of passwords or file with list of passwords
