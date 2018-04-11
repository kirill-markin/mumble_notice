#!/usr/bin/env python3

import re
import select
from systemd import journal
import requests
import os

def god_notice(line):
    curr_mess = ''
    match_in = re.search(r'=> <([0-9]*):(?P<user>[^ ]*)\(-([0-9]*)\)> Authenticated', line)
    #match_out = re.search(r'=> <([0-9]*):(?P<user>[^ ]*)\(-([0-9]*)\)> Connection closed', line)
    if match_in:
        curr_mess = match_in.group('user') + ' in'
    #elif match_out:
    #    curr_mess = match_out.group('user') + ' out'
    return curr_mess

j = journal.Reader()
j.log_level(journal.LOG_INFO)

j.seek_tail()
j.get_previous()

p = select.poll()
p.register(j, j.get_events())

print(os.environ)
print(type(os.environ))

#r = requests.get('https://api.telegram.org/bot'+ BotKey + '/getUpdates')
#print(r.text)
#r = requests.post('https://api.telegram.org/bot'+ BotKey + '/sendMessage', data = {'chat_id':'-277997760', 'text':'my sample text'})

while p.poll():
    if j.process() != journal.APPEND:
        continue
    for entry in j:
        if entry['SYSLOG_IDENTIFIER'] == 'murmurd':
            notice_str = god_notice(entry['MESSAGE'])
            if notice_str != '':
                print(notice_str)
