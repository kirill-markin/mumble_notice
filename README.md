# mumble_notice

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

Start on the server:
```systemctl --user start mumble_notice```

Restart on the server:
```systemctl --user restart mumble_notice```

Get logs:
```systemctl --user status mumble_notice```

Stop on the server:
```systemctl --user stop mumble_notice```
