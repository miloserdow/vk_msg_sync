#!/usr/bin/python

# This is module for VK OAuth authorization
# Source originally forked from https://github.com/dzhioev/vk_api_auth/blob/master/vk_auth.py
# Vladimir Miloserdov (c) 2014
__author__ = 'Vladimir Miloserdov'
__license__ = 'GPLv2'

import http.cookiejar
import urllib.request
import urllib.parse
from html.parser import HTMLParser

class FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.url = None
        self.params = {}
        self.in_form = False
        self.form_parsed = False
        self.method = "GET"

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "form":
            self.in_form = True
        if not self.in_form:
            return
        attrs = dict((name.lower(), value) for name, value in attrs)
        if tag == "form":
            self.url = attrs["action"]
            if "method" in attrs:
                self.method = attrs["method"].upper()
        elif tag == "input" and "type" in attrs and "name" in attrs:
            if attrs["type"] in ["hidden", "text", "password"]:
                self.params[attrs["name"]] = attrs["value"] if "value" in attrs else ""

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "form":
            if not self.in_form:
                raise RuntimeError("Unexpected end of <form>")
            self.in_form = False
            self.form_parsed = True

def auth(email, password, client_id, scope):
    def split_key_value(kv_pair):
        kv = kv_pair.split("=")
        return kv[0], kv[1]

    # Authorization form
    def auth_user(email, password, client_id, scope, opener):
        response = opener.open(
            "http://oauth.vk.com/oauth/authorize?" + \
            "redirect_uri=http://oauth.vk.com/blank.html&response_type=token&" + \
            "client_id=%s&scope=%s&display=wap" % (client_id, ",".join(scope))
            )
        doc = response.read()
        parser = FormParser()
        parser.feed(doc.decode('utf-8'))
        parser.close()
        if not parser.form_parsed or parser.url is None or "pass" not in parser.params or \
          "email" not in parser.params:
              raise RuntimeError("Authorization failure")
        parser.params["email"] = email
        parser.params["pass"] = password
        if parser.method == "POST":
            response = opener.open(parser.url, urllib.parse.urlencode(parser.params).encode('utf-8'))
        return response.read(), response.geturl()

    # Permission request form
    def give_access(doc, opener):
        parser = FormParser()
        parser.feed(doc.decode('utf-8'))
        parser.close()
        if not parser.form_parsed or parser.url is None:
              raise RuntimeError("Something wrong")
        if parser.method == "POST":
            response = opener.open(parser.url, urllib.parse.urlencode(parser.params).encode('utf-8'))
        return response.geturl()


    if not isinstance(scope, list):
        scope = [scope]
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        urllib.request.HTTPRedirectHandler())
    doc, url = auth_user(email, password, client_id, scope, opener)
    if urllib.request.urlparse(url).path != "/blank.html":
        # Need to give access to requested scope
        url = give_access(doc, opener)
    if urllib.request.urlparse(url).path != "/blank.html":
        raise RuntimeError("Authorization failure")
    answer = dict(split_key_value(kv_pair) for kv_pair in urllib.request.urlparse(url).fragment.split("&"))
    if "access_token" not in answer or "user_id" not in answer:
        raise RuntimeError("Authorization failure")
    return answer["access_token"], answer["user_id"]

#debug_key= auth('email', 'pass', '4372631', '4096') # 4096 for messages permissions
#print(debug_key)
