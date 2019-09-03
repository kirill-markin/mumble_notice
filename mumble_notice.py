#!/usr/bin/env python3

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


class GodNotifier:
    def __init__(self, delay, notify_target):
        self._users_online = set()
        self._prev_users_online = set()
        self._conclusion_thread = None
        self._lock = threading.Lock()
        self._notify_target = notify_target
        self._delay = delay
        self._logger = logging.getLogger("GodNotifier")

    def update(self, line):
        match_in = re.search(r'=> <([0-9]*):(?P<user>[^ ]*)\(-?([0-9]*)\)> Authenticated', line)
        match_out = re.search(r'=> <([0-9]*):(?P<user>[^ ]*)\(-?([0-9]*)\)> Connection closed', line)
        with self._lock:
            if match_in:
                user = match_in.group('user')
                if not user.startswith('_'):
                    self._logger.info(f"User {user} is online")
                    self._users_online.add(user)
                    self._run_conclusion_if_not()
            elif match_out:
                user = match_out.group('user')
                if not user.startswith('_'):
                    self._logger.info(f"User {user} is offline")
                    self._users_online.discard(user)
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


with open('conf.json', 'r') as f:
    config = json.load(f)

delay = config['Delay']

bot_key = config['BotKey']
chat_id = config['ChatId']

j_id = config['Jid']
j_pass = config['Jpass']
j_mucroom = config['Jmucroom']
j_muc_nick = config['Jmucnic']

logging.basicConfig(level=logging.DEBUG)

j = systemd.journal.Reader()
j.log_level(systemd.journal.LOG_INFO)
j.add_match(SYSLOG_IDENTIFIER='murmurd')

j.seek_tail()
p = select.poll()
p.register(j, j.get_events())

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
    if len(nick) <= 1:
        return nick
    else:
        # Zero-width no-break space
        return nick[:1] + "\uFEFF" + nick[1:]

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

god_notice = GodNotifier(delay, run_god_notice)

try:
    while p.poll():
        if j.process() != systemd.journal.APPEND:
            continue
        for entry in j:
            god_notice.update(entry['MESSAGE'])
except KeyboardInterrupt:
    pass
