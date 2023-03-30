"""Send a reply from the proxy without sending any data to the remote server."""
from mitmproxy import http
import hashlib
import os
import json
import re 

home = './store/'

def request(flow: http.HTTPFlow) -> None:
    flow.request.anticache()
    
def response(flow: http.HTTPFlow) -> None:
    print('check ' + flow.request.pretty_url)

    url = home + flow.request.pretty_host + '-' + hashlib.sha256(bytes(flow.request.pretty_url, encoding='utf8')).hexdigest()
    ftype = flow.request.pretty_url.split("?", 1)[0]
    ftype = re.search(r'\.[a-zA-Z]{3,4}$', ftype)
    ftype = "" if ftype == None else ftype.group(0)
    url = url + ftype

    #if flow.response and not os.path.isfile(url + '.json'):
    if flow.response:
        # os.makedirs(os.path.dirname(url), exist_ok=True)
        print(url + '.json')
        with open(url + '.json', "w") as f:
            f.write(json.dumps([flow.request.pretty_url, flow.response.status_code, dict(flow.response.headers)]))
        
        if flow.response.content:
            with open(url, "wb") as f:
                f.write(flow.response.content)

