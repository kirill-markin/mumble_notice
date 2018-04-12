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
    
    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick
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
                          mbody="test",
                          mtype='groupchat')
        self.disconnect(wait=True)

def jabber_notice(text_notice):
    if __name__ == '__main__':
        # Setup the command line arguments.
        optp = OptionParser()

        # Output verbosity options.
        optp.add_option('-q', '--quiet', help='set logging to ERROR',
                        action='store_const', dest='loglevel',
                        const=logging.ERROR, default=logging.INFO)
        optp.add_option('-d', '--debug', help='set logging to DEBUG',
                        action='store_const', dest='loglevel',
                        const=logging.DEBUG, default=logging.INFO)
        optp.add_option('-v', '--verbose', help='set logging to COMM',
                        action='store_const', dest='loglevel',
                        const=5, default=logging.INFO)

        # JID and password options.
        optp.add_option("-j", "--jid", dest="jid",
                        help="JID to use")
        optp.add_option("-p", "--password", dest="password",
                        help="password to use")
        optp.add_option("-r", "--room", dest="room",
                        help="MUC room to join")
        optp.add_option("-n", "--nick", dest="nick",
                        help="MUC nickname")

        opts, args = optp.parse_args()

        # Setup logging.
        logging.basicConfig(level=opts.loglevel,
                            format='%(levelname)-8s %(message)s')

        if opts.jid is None:
            opts.jid = Jid
        if opts.password is None:
            opts.password = Jpass
        if opts.room is None:
            opts.room = Jmucroom
        if opts.nick is None:
            opts.nick = Jmucnic

        xmpp = MUCBot(opts.jid, opts.password, opts.room, opts.nick)
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0045') # Multi-User Chat
        xmpp.register_plugin('xep_0199') # XMPP Ping

        if xmpp.connect():
            xmpp.process(block=True)
            print("Done")
        else:
            print("Unable to connect.")

j = journal.Reader()
j.log_level(journal.LOG_INFO)
j.add_match(SYSLOG_IDENTIFIER='murmurd')

j.seek_tail()
j.get_previous()

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
                jabber_notice('123')
except KeyboardInterrupt:
    pass
