"""Send a reply from the proxy without sending any data to the remote server."""
from mitmproxy import http
import hashlib
import os
import json
import re

home = './store/'

def request(flow: http.HTTPFlow) -> None:
    print('check ' + flow.request.pretty_url)

    url = home + flow.request.pretty_host + '-' + hashlib.sha256(bytes(flow.request.pretty_url, encoding='utf8')).hexdigest()
    ftype = flow.request.pretty_url.split("?", 1)[0]
    ftype = re.search(r'\.[a-zA-Z]{3,4}$', ftype)
    ftype = "" if ftype == None else ftype.group(0)
    url = url + ftype

    print(url + '.json')
    if os.path.isfile(url + '.json'):
        print("ok\n")

        js = []
        with open(url + '.json', 'r') as file:
            data = file.read()
            js = json.loads(data)

        res = b''
        if os.path.isfile(url):
            with open(url, 'rb') as file:
                res = file.read()

        flow.response = http.Response.make(
            js[1],  # (optional) status code
            res,  # (optional) content
            js[2],  # (optional) headers
        )

    else:
        print("fail\n")
        flow.response = http.Response.make(404, b'')

