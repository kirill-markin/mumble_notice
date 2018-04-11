#!/usr/bin/env python3

import re
import select
from systemd import journal

def god_notice(line):
    curr_mess = ''
    match_in = re.search(r'=> <([0-9]*):(?P<user>[^ ]*)\(-([0-9]*)\)> Authenticated', line)
    match_out = re.search(r'=> <([0-9]*):(?P<user>[^ ]*)\(-([0-9]*)\)> Connection closed', line)
    if match_in:
        curr_mess = match_in.group('user') + ' in'
    elif match_out:
        curr_mess = match_out.group('user') + ' out'
    return curr_mess

j = journal.Reader()
j.log_level(journal.LOG_INFO)

j.seek_tail()
j.get_previous()

while p.poll():
    if j.process() != journal.APPEND:
        continue
    for entry in j:
        if entry['MESSAGE'] != "":
            print(str(entry['__REALTIME_TIMESTAMP'] )+ ' ' + entry['MESSAGE'])

#with open('test.txt', 'r') as tlogs:
#    logs = list(tlogs)
#    print(god_notice(logs[len(logs)-1]))
