#!/usr/bin/env python3

import Murmur, Ice
import re
import requests
import json
import threading
import time
import logging
import copy

import sys
import logging
from optparse import OptionParser
import sleekxmpp


class GodNotifier:
    def __init__(self, proxy, delay, notify_target):
        self._users_online = set()
        self._prev_users_online = set()
        self._conclusion_thread = None
        self._lock = threading.Lock()
        self._notify_target = notify_target
        self._delay = delay
        self._logger = logging.getLogger("GodNotifier")
        meta = Murmur.MetaPrx.checkedCast(proxy)
        self._server = meta.getAllServers()[0]

    def update(self):
        users = self._server.getUsers()
        users_online = set()
        for user in users.values():
            if not user.name.startswith('_'):
                users_online.add(user.name)
        with self._lock:
            if self._users_online != users_online:
                self._users_online = users_online
                self._run_conclusion_if_not()

    def _wait_and_conclude(self):
        time.sleep(self._delay)
        old_users = None
        new_users = None
        with self._lock:
            self._logger.debug(f"Comparing after delay, old users {self._prev_users_online}, new users {self._users_online}")
            if self._users_online != self._prev_users_online:
                new_users = self._users_online
                old_users = self._prev_users_online
                self._prev_users_online = copy.copy(self._users_online)
                if len(self._prev_users_online) != 0:
                    self._run_conclusion()
                else:
                    self._conclusion_thread = None
            else:
                self._conclusion_thread = None
        if old_users is not None:
            self._logger.info("Notifying, old users {old_users}, new users {new_users}")
            thread = threading.Thread(target=self._notify_target, args=(old_users, new_users))
            thread.start()

    def _run_conclusion_if_not(self):
        if self._conclusion_thread is None:
            self._run_conclusion()

    def _run_conclusion(self):
        self._logger.debug("Starting conclusion delay thread")
        self._conclusion_thread = threading.Thread(target=self._wait_and_conclude, daemon=True)
        self._conclusion_thread.start()


class MUCBot(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, room, nick, text_notice):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick
        self.test_notice = text_notice
        self.add_event_handler("session_start", self.start)

    def start(self, event):
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        wait=True)
        self.send_message(mto=self.room,
                          mbody=self.test_notice,
                          mtype='groupchat')
        self.disconnect(wait=True)


with open(sys.argv[1], 'r') as f:
    config = json.load(f)

address = config['Address']
delay = config['Delay']

bot_key = config['BotKey']
chat_id = config['ChatId']

j_id = config['Jid']
j_pass = config['Jpass']
j_mucroom = config['Jmucroom']
j_muc_nick = config['Jmucnic']

logging.basicConfig(level=logging.DEBUG)

def jabber_notice(text_notice):
    xmpp = MUCBot(j_id, j_pass, j_mucroom, j_muc_nick, text_notice)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0045') # Multi-User Chat
    xmpp.register_plugin('xep_0199') # XMPP Ping

    if xmpp.connect():
        xmpp.process(block=True)
    else:
        print("Unable to connect to jabber.")

def mangle_nick(nick):
    # Zero-width no-break space
    return "\uFEFF".join(nick)

def list_nicks(nicks, mangle_func=None):
    prepared = sorted(nicks)
    if mangle_func is not None:
        prepared = map(mangle_func, prepared)
    return ", ".join(prepared)

def run_god_notice(old_users, new_users, mangle_func=mangle_nick):
    left_users = old_users.difference(new_users)
    joined_users = new_users.difference(old_users)

    strs = []
    mangled_strs = []

    def append_line(line, nicks=None):
        nonlocal strs, mangled_strs

        if nicks is None:
            strs.append(line)
            mangled_strs.append(line)
        else:
            strs.append(line.format(list_nicks(nicks)))
            mangled_strs.append(line.format(list_nicks(nicks, mangle_func=mangle_nick)))

    if len(new_users) == 0:
        append_line("No Mumble users online")
    else:
        append_line("Mumble users online: {}", new_users)
    if len(joined_users) > 0:
        append_line("Users joined: {}", joined_users)
    if len(left_users) > 0:
        append_line("Users left: {}", left_users)

    notice_str = "\n".join(strs)
    mangled_notice_str = "\n".join(mangled_strs)

    requests.post('https://api.telegram.org/bot' + bot_key + '/sendMessage',
        data = {'chat_id':chat_id, 'text':notice_str})
    jabber_notice(mangled_notice_str)

if __name__ == "__main__":
    with Ice.initialize() as communicator:
        proxy = communicator.stringToProxy("Meta:" + address)
        god_notice = GodNotifier(proxy, delay, run_god_notice)
        try:
            while True:
                god_notice.update()
                time.sleep(1)
        except KeyboardInterrupt:
            pass
