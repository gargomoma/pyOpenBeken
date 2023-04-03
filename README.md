# pyOpenBeken
An easier way to manage your OpenBeken devices.

### Examples

Connect to a single board:
```sh
import pyopenbeken
your_device = pyopenbeken.device( IP_HERE )

#Get board info
your_device.board_info

#Update boards
your_device.check_ota()
your_device.push_ota(fileAddress)
```

Connect to a series of boards by providing a list of IPs:
```sh
list_ips = [LIST OF IPS]
gh_api_token = 'GitHub API Token'

import pyopenbeken
boardMgr = pyopenbeken.BoardManager(list_ips=list_ips,gh_token=gh_api_token)

#Get boards info
boardMgr.boards

#Update boards
boardMgr.update_boards()
```