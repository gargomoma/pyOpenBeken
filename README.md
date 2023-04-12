# pyOpenBeken
An easier way to manage your [OpenBeken](https://github.com/openshwprojects/OpenBK7231T_App) devices.

The purpose of this project is to ease the control of multiple devices avoiding all manual tasks.

### Features
* Send commands
* Setup mqtt & HA autodiscovery
* Read file system
* Push OTAs and restore FS

### Planned features
* Scan for devices
* Set pins (Roles, Channels)
* Control device
* Set other options


### Examples
* GitHub Token:
Nobody likes to get limited by APIs quotas, get your GH API token [here](https://github.com/settings/tokens?type=beta)

* Connect to a single board:
```sh
import pyopenbeken
your_device = pyopenbeken.device( IP_HERE )

#Get board info
your_device.info

#Update board
your_device.check_ota()
your_device.push_ota(fileAddress)
```

* Connect to a series of boards by providing a list of IPs:
```sh
list_ips = [LIST OF IPS]
gh_api_token = 'GitHub API Token' or None

import pyopenbeken
devmgr = pyopenbeken.deviceManager(list_ips=list_ips,gh_token=gh_api_token)

#Get boards info
devmgr.devices

#Update boards
devmgr.update_devices()
```

#### Web Manager
Update your boards with just one click.
* Any help is welcome to make a convinient network scanner and a docker container =)
![plot](docs/pyOpenBeken_WebScreenshot.png)

### TO DO:
* Create documentation
* Add more methods and commands to interact with the boards
* Ability to scan local network for OpenBeken devices (WIP).
* Docker container for the Web Manager?