# -*- coding: utf-8 -*-

import os.path
import httplib
import urlparse
import urllib
import socket
import json
import mimetypes

from .config import *

def append_url(url, params):
    if type(params) == dict:
        params = urllib.urlencode(params)
    if not params:
        return url
    if '?' not in url:
        return url + '?' + params
    return url + '&' + params

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    
    see: http://code.activestate.com/recipes/146306/
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

class RequestObject:
    https_connect = None
    http_connect = None
    def request(self, method, url, params=None, body=None, headers=None, follow=False, format=None):
        """
        Send HTTP or HTTPS request, and get the response
        """
        params = params or {}
        headers = headers or {}
        headers['User-Agent'] = 'WeipanPythonClient/' + SDK_VERSION

        if method != 'POST' and params:
            # For none POST method, params is appended to url
            url = append_url(url, params)
        elif method == 'POST' and params:
            if body:
                raise ValueError("body should not be used with POST params")
            # check file and send with multipart/form-data
            
            mf_files = []
            mf_fields = []
            for k in params.keys():
                if k.startswith('@'):
                    with open(params[k], 'rb') as fh:
                        file_content = fh.read()
                    mf_files.append((k[1:], os.path.basename(params[k]), file_content))
                else:
                    mf_fields.append((k, params[k]))

            if mf_files:
                content_type, body = encode_multipart_formdata(mf_fields, mf_files)
            else:
                content_type = "application/x-www-form-urlencoded"
                body = urllib.urlencode(params)
            headers["Content-type"] = content_type

        urlinfo = urlparse.urlparse(url)
        host = urlinfo.hostname
        scheme= urlinfo.scheme

        # HTTP and HTTPS handled by different classes
        if(scheme == 'https'):
            if self.https_connect is None:
                self.https_connect = httplib.HTTPSConnection
            conn = self.https_connect(host)
        else:
            if self.http_connect is None:
                self.http_connect = httplib.HTTPConnection
            conn = self.http_connect(host)

        try:
            conn.request(method, url, body, headers)
        except socket.error, e:
            raise SocketError(e)

        response = conn.getresponse()
        if follow and response.status == 302:
            #follow location
            redirect = response.getheader('location')
            return self.request('GET', redirect, follow=True, format=format)

        if response.status != 200:
            raise ErrorResponse(response, format)

        if format in ['json', 'plain']:
            content = response.read()
            conn.close()
            if format == 'plain':
                return content
            else:
                try: 
                    j = json.loads(content)
                except ValueError:
                    raise ErrorResponse(response, format)
                return j
        else:
            return response

    def get(self, url, params = None, headers = None, follow=False, format=None):
        """
        Send request with GET method
        """
        return self.request('GET', url, params=params, headers=headers, follow=follow, format=format);

    def post(self, url, params = None, headers=None, follow=False, format=None):
        """
        Send request with POST method
        """
        return self.request('POST', url, params=params, headers=headers, follow=follow, format=format)

    def put(self, url, params = None, body=None, headers=None, follow=False, format=None):
        """
        Send request with PUT method
        """
        return self.request('PUT', url, params=params, body=body, headers=headers, follow=follow, format=format)

class Request:
    """
    Request wrapper
    """
    IMPL = RequestObject()

    @classmethod
    def request(cls, *args, **kwargs):
        return cls.IMPL.request(*args, **kwargs)

    @classmethod
    def get(cls, *args, **kwargs):
        return cls.IMPL.get(*args, **kwargs)

    @classmethod
    def post(cls, *args, **kwargs):
        return cls.IMPL.post(*args, **kwargs)

    @classmethod
    def put(cls, *args, **kwargs):
        return cls.IMPL.put(*args, **kwargs)

def ensure_json(response):
    if type(response) == str:
        try:
            response = json.loads(response)
        except ValueError:
            raise ResponseJsonError("Response is not formated in JSON")

    return response


class SocketError(socket.error):
    pass

class ErrorResponse(Exception):
    def getheader(self, info):
        for k, v in self.headers:
            if k == info:
                return v
        return None

    def __init__(self, http_resp, format=None):
        self.status = http_resp.status
        self.reason = http_resp.reason
        self.body = http_resp.read()
        self.headers = http_resp.getheaders()
        self.json = None

        if format == 'json':
            try:
                self.json = json.loads(self.body)
            except ValueError:
                pass

    def __str__(self):
        msg = "Error parsing response body or headers: " +\
              "Body - %s Headers - %s" % (self.body, self.headers)

        return "[%d] %s" % (self.status, repr(msg))