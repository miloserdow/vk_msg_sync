#!/usr/bin/python

# Vladimir Miloserdov (c) 2014
__author__ = 'Vladimir Miloserdov'
__license__ = 'GPLv2'

import sys
import auth
import os.path
import time

access_token_pth = '.access_token'
app_id = '4372631' # milosApp id
scope = '4096' # 'messages' privileges
expire_time = 86400 # 24 hours

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
        print('Pass: ', end="")
        passw = input()
        new_token = auth.auth(login, passw, app_id, scope)
        token_file.write(time.asctime(time.localtime()) + '\n')
        token_file.write(new_token[0] + '\n')
        token_file.write(new_token[1] + '\n')

# Parsing token file
with open(access_token_pth, encoding='utf-8') as token_file:
    token_file.readline()
    token = token_file.readline().rstrip()
    user_id = token_file.readline().rstrip()
    print('Your token is', token)
    print('Your id is', user_id)
