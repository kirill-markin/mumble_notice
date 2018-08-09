# mumble_notice

Notice in telegram and jabber when someone enters or leaves mumble room on the same server.

## Dependencies

```
import re
import select
import systemd.journal
import requests
import json
import threading
import time
import logging
import copy

import sys
import logging
import getpass
from optparse import OptionParser
import sleekxmpp
```

## Config

Requires one more file on the same directory `conf.json` with the structure:
```
{
  "BotKey"       : "...",
  "ChatId"       : "...",
  "Jid"          : "...@jabber.ru",
  "Jpass"        : "...",
  "Jmucroom"     : "...",
  "Jmucnic"      : "god_notice",
  "Delay"        : 60
}
```
For telegram:
* BotKey
* ChatId

For jabber:
* Jid
* Jpass
* Jmucroom
* Jmucnic

Common
* Delay 

## Commands

Start on the server:
```systemctl --user start mumble_notice```

Restart on the server:
```systemctl --user restart mumble_notice```

Get logs:
```systemctl --user status mumble_notice```

Stop on the server:
```systemctl --user stop mumble_notice```
