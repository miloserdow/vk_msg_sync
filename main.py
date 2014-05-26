#!/usr/bin/python

# Vladimir Miloserdov (c) 2014
__author__ = 'Vladimir Miloserdov'
__license__ = 'GPLv2'

import sys
import auth
import getpass
import os.path
import time
from collections import defaultdict
import urllib
import json

access_token_pth = '.access_token'
app_id = '4372631' # milosApp id
scope = '4096' # 'messages' privileges
expire_time = 86400 # 24 hours
maxcnt = 200 # Max messages count per request
total_cnt = None
token = None
msg_dir = None
msgs = defaultdict(list)

# Get full name by id
def get_name(id):
    res = urllib.request.urlopen('https://api.vk.com/method/users.get?user_ids='+str(id)+'&v=5.8')
    code = json.loads(res.read().decode('utf-8'))
    return code['response'][0]['first_name'], code['response'][0]['last_name']

# Write messges into files
def msg_process(msgs):
    for id in msgs:
        name = get_name(id)
        fname, lname = name[0], name[1]
        with open(msg_dir+'/'+fname+'_'+lname+'.msg', 'a+', encoding='utf-8') as cur_file:
            for cur_msg in msgs[id]:
                tim = time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(int(cur_msg[0])))
                cur_file.write('['+tim+'] '+(cur_msg[1] and 'me' or fname) +': '+cur_msg[2]+'\n')

# This function loads messanges from the remote
def msg_fetch(pos, cnt, is_out):
    if token is None:
        raise RuntimeError('Token undefined: not authorized')
    res = urllib.request.urlopen('https://api.vk.com/method/messages.get?out='+str(is_out)+'&offset='+str(pos)+'&count='
                                 +str(cnt)+'&access_token='+token)
    code = json.loads(res.read().decode('utf-8'))
    total_cnt = code['response'][0]
    for i in range(1, cnt + 1):
        msgs[code['response'][i]['uid']].append((code['response'][i]['date'], code['response'][i]['out'], code['response'][i]['body']))
    #msg_process(msgs)

# Program starts HERE!
print('This program will download all your VK messages and save them into files')
print('Copyright (C) 2014 Vladimir Miloserdov <milosvova@gmail.com>\n')
print('This program is free software: you can redistribute it and/or modify')
print('it under the terms of the GNU General Public License as published by')
print('the Free Software Foundation...\n')
print('This program is distributed in the hope that it will be useful,')
print('but WITHOUT ANY WARRANTY; without event the implied warranty of')
print('MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the')
print('GNU General Public License for more details.')

while True:
    try:
        print('Please specify message directory: ', end="")
        msg_dir = input()
        msg_dir.encode('ascii')
        # Creating msg directory if not exists
        if not os.path.exists(msg_dir + '/'):
            os.makedirs(msg_dir + '/')
        else:
            print('Directory already exists, conflicts are possible, continue [y/N]? ', end="")
            ans = input()
            if not (ans == 'y' or ans == 'Y' or ans == 'yes' or ans == 'YES'):
                continue
    except UnicodeEncodeError:
        print('Use only ASCII characters!')
    except OSError:
        print('Smth is wrong with the specified directory')
    else:
        break

# Checking if token hasn't expired yet
if os.path.isfile(access_token_pth):
    with open(access_token_pth, encoding='utf-8') as token_file:
        start_time = time.strptime(token_file.readline().rstrip())
        start_time = time.mktime(start_time)
        cur_time = time.mktime(time.localtime())
        if cur_time - start_time > expire_time:
            os.remove(access_token_pth)

# Getting new token, if it doesn't exist            
if not os.path.isfile(access_token_pth):
    with open(access_token_pth, 'w+', encoding='utf-8') as token_file:
        print('Authorization required to proceed\n')
        print('Login: ', end="")
        login = input()
        passw = getpass.getpass('Pass: ')
        new_token = auth.auth(login, passw, app_id, scope)
        token_file.write(time.asctime(time.localtime()) + '\n')
        token_file.write(new_token[0] + '\n')
        token_file.write(new_token[1] + '\n')

# Parsing token file
with open(access_token_pth, encoding='utf-8') as token_file:
    token_file.readline()
    token = token_file.readline().rstrip()
    user_id = token_file.readline().rstrip()
    print('Your id is', user_id)

for i in range(0, 2):    
    res = urllib.request.urlopen('https://api.vk.com/method/messages.get?out='+str(i)+'&offset=0&count=1&access_token='+token)
    code = json.loads(res.read().decode('utf-8'))
    remain = total_cnt = code['response'][0]
    print('Total ' +(i == 0 and 'inbox' or 'sent') + ' message count:', total_cnt)
    
    # Progress bar :)
    bar_width = 50
    bar_state = 0
    part = maxcnt / total_cnt
    step = bar_width / part
    print(part, step)
    sys.stdout.write("[%s]" % (" " * bar_width))
    sys.stdout.flush()
    sys.stdout.write("\b" * (bar_width+1))

    # Fetching & processing messages
    try:
        while remain > maxcnt:
            msg_fetch(total_cnt - remain, maxcnt, i)
            remain -= maxcnt
            progress += step
            if progress * 2 > bar_state:
                sys.stdout.write("-" * int(step))
                sys.stdout.flush()
                bar_state += int(step)
        if remain > 0:
            msg_fetch(total_cnt - remain, remain, i)
        sys.stdout.write("-" * ((100 - bar_state) // 2))
        sys.stdout.write("\n")

    # This could happen if smth goes wrong, e.g. request failure
    except IndexError:
        print('Error getting messages')
        exit(1)

for x in msgs:
    msgs[x].sort()
msg_process(msgs)
# TODO: Sort messages by timestamps
print('Program has been finished successfully')
