# -*- coding: utf-8 -*-

"""
Local app helpers for OAuth2.0 callback
"""

import re
from threading import Thread
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import time
_CODE = None
_STARTED = False
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _CODE

        rst = re.match(r'.*\bcode=(\w+).*', self.path)
        if rst:
            _CODE = rst.group(1)
            self.send_response(302)
            self.send_header("Location", "http://vdisk.weibo.com")
            self.end_headers()
            #rst = 'Success'
            #self.wfile.write(rst)
            
    def log_message(self, format, *args):
        return

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def serve_on_port(port):
    server = ThreadingHTTPServer(("localhost",port), Handler)
    server.serve_forever()

def receive_code(port):
    """
    Start local http server and waiting for authrization callback
    """
    global _CODE
    global _STARTED
    _CODE = None
    if not _STARTED:
        t = Thread(target=serve_on_port, args=[port])
        t.setDaemon(True)
        t.start()
        t.join(1)
        _STARTED = True
    try:
        while True:
            time.sleep(0.1)
            if _CODE is not None:
                if _CODE == '21300':
                    return False
                return _CODE
    except KeyboardInterrupt:
        return False