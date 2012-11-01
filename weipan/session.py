# -*- coding: utf-8 -*-

from . import request
from .config import *

class WeipanSession:

    def __init__(self, appkey, appsecret, callback, access_type='sandbox'):
        self.APP_KEY = appkey
        self.APP_SECRET = appsecret
        assert access_type in ['basic', 'sandbox'], "expected access_type of 'basic' or 'sandbox'"
        self.callback = callback
        self.root = access_type
        self.token = None


    def build_oauth2_url(self, path, params=None):
        return request.append_url(AUTH_URL+path, params)

    def build_authorize_url(self, response_type='code', state='', display='default'):
        params = {
            'redirect_uri': self.callback,
            'client_id': self.APP_KEY,
            'response_type': response_type,
            'state': state,
            'display': display
        }
        return self.build_oauth2_url('authorize', params)

    def access_token_with_code(self, code):
        params = {
            'client_id': self.APP_KEY,
            'client_secret': self.APP_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': self.callback,
            'code': code
        }
        return request.Request.post(self.build_oauth2_url('access_token'), params, format='json')

    def access_token_with_password(self, username, password):
        params = {
            'client_id': self.APP_KEY,
            'client_secret': self.APP_SECRET,
            'grant_type': 'password',
            'username': username,
            'password': password
        }

        return request.Request.post(self.build_oauth2_url('access_token'), params, format='json')

    def refresh_token(self, refresh_token):
        params = {
            'client_id': self.APP_KEY,
            'client_secret': self.APP_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }

        return request.Request.post(self.build_oauth2_url('access_token'), params, format='json')

    def set_token(self, token):
        self.token = token

    def is_linked(self):
        return bool(self.token)

    def unlink(self):
        self.token = None

