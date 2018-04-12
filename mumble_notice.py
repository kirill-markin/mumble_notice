#!/usr/bin/env python3

import re
import select
from systemd import journal
import requests
import json

import sys
import logging
import getpass
from optparse import OptionParser
import sleekxmpp

with open('conf.json', 'r') as f:
    config = json.load(f)

BotKey = config['BotKey']
ChatId = config['ChatId']

Jid = config['Jid']
Jpass = config['Jpass']
Jmucroom = config['Jmucroom']
Jmucnic = config['Jmucnic']

def god_notice(line):
    curr_mess = ''
    match_in = re.search(r'=> <([0-9]*):(?P<user>[^ ]*)\(-([0-9]*)\)> Authenticated', line)
    #match_out = re.search(r'=> <([0-9]*):(?P<user>[^ ]*)\(-([0-9]*)\)> Connection closed', line)
    if match_in:
        curr_mess = match_in.group('user') + ' in mumble'
    #elif match_out:
    #    curr_mess = match_out.group('user') + ' out of mumble'
    return curr_mess

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
                                        # If a room password is needed, use:
                                        # password=the_room_password,
                                        wait=True)
        self.send_message(mto=self.room,
                          mbody=self.test_notice,
                          mtype='groupchat')
        self.disconnect(wait=True)

def jabber_notice(text_notice):
    xmpp = MUCBot(Jid, Jpass, Jmucroom, Jmucnic, text_notice)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0045') # Multi-User Chat
    xmpp.register_plugin('xep_0199') # XMPP Ping

    if xmpp.connect():
        xmpp.process(block=True)
    else:
        print("Unable to connect to jabber.")

j = journal.Reader()
j.log_level(journal.LOG_INFO)
j.add_match(SYSLOG_IDENTIFIER='murmurd')

j.seek_tail()
p = select.poll()
p.register(j, j.get_events())

try:
    while p.poll():
        if j.process() != journal.APPEND:
            continue
        for entry in j:
            notice_str = god_notice(entry['MESSAGE'])
            if notice_str != '':
                requests.post('https://api.telegram.org/bot' + BotKey + '/sendMessage', 
                              data = {'chat_id':ChatId, 'text':notice_str})
                jabber_notice(notice_str)
except KeyboardInterrupt:
    pass
