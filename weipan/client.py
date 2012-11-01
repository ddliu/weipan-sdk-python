# -*- coding: utf-8 -*-

from . import request, session
from .config import *
import re
import time

def format_path(path):
    """Normalize path for use with the Weipan API.

    This function turns multiple adjacent slashes into single
    slashes, then ensures that there's a leading slash but
    not a trailing slash.
    """
    if not path:
        return path

    path = re.sub(r'/+', '/', path)

    if path == '/':
        return (u"" if isinstance(path, unicode) else "")
    else:
        return '/' + path.strip('/')

class WeipanClient:
    """
    Weipan API client
    """

    def __init__(self, session, debug=False, delay=None):
        """
        delay: fix api delay
        """
        self.session = session
        self.is_debug = debug
        self.delay = delay

    def debug(self, message = None):
        """
        Show debug message
        """
        if message is None:
            self.is_debug = True
        elif self.is_debug:
            print "[DEBUG] %s" % message

    def build_api_url(self, target, params=None):
        return request.append_url("://" in target and target or (API_URL + target), params)

    def request(self, method, target, params=None, body=None, follow=False, format='json'):
        """
        format: json|raw
        """

        # delay request(prevent API server delay)
        if self.delay:
            time.sleep(self.delay)

        url = self.build_api_url(target, {
            'access_token': self.session.token
        })
        self.debug("[%s %s] %s" % (method, format, url))
        return request.Request.request(method, url, params, body, follow=follow, format=format)

    def get(self, target, params=None, follow=False, format='json'):
        return self.request('GET', target, params, follow=follow, format=format)
        
    def post(self, target, params=None, follow=False, format='json'):
        return self.request('POST', target, params, follow=follow, format=format)

    def put(self, target, params=None, body=None, follow=False, format='json'):
        return self.request('PUT', target, params, body, follow=follow, format=format)

    def account_info(self):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#account_info
        """
        return self.get('account/info')

    def delta(self, cursor=None):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#delta
        """
        params = {}
        if cursor is not None:
            params['cursor'] = cursor
        return self.get('delta/' + self.session.root, params)

    def get_file(self, from_path, rev=None, return_content=True):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#files_get
        """
        path = "files/%s%s" % (self.session.root, format_path(from_path))

        params = {}
        if rev is not None:
            params['rev'] = rev
        return self.get(path, params, follow=True, format=return_content and 'plain' or 'response')

    def get_file_url(self, from_path, rev=None):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#files_get
        """
        path = "files/%s%s" % (self.session.root, format_path(from_path))
        params = {}
        if rev is not None:
            params['rev'] = rev
        try:
            r = self.get(path, params, format=None)
            raise request.ErrorResponse(r)
        except request.ErrorResponse, e:
            if e.status == 302:
                return e.getheader('location')
            else:
                raise e

    def put_file(self, path, file_obj, overwrite = True, parent_rev = None):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#files_put
        """
        path = "%sfiles_put/%s%s" % (UPLOAD_URL, self.session.root, format_path(path))

        params = {
            'overwrite': overwrite and 'true' or 'false'
        }

        if parent_rev is not None:
            params['parent_rev'] = parent_rev

        return self.put(path, params, file_obj)

    def post_file(self):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#files_post
        todo
        """
        pass

    def metadata(self, path, list=True, hash=None, include_deleted=False):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#metadata
        """
        path = "metadata/%s%s" % (self.session.root, format_path(path))
        params = {
            'list': list and 'true' or 'false',
            'include_deleted': include_deleted and 'true' or 'false'
        }
        if hash is not None:
            params['hash'] = hash
        return self.get(path, params)

    def revisions(self, path, rev_limit=None):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#revisions
        """
        path = "revisions/%s%s" % (self.session.root, format_path(path))
        params = {}
        if rev_limit is not None:
            params['rev_limit'] = rev_limit
        return self.get(path, params)

    def restore(self, path, rev):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#restore
        """
        path = "restore/%s%s" % (self.session.root, format_path(path))
        params = {
            'rev': rev
        }
        return self.post(path, params)

    def search(self, path, query, file_limit = None, include_deleted = False):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#search
        """
        path = "search/%s%s" % (self.session.root, format_path(path))
        params = {
            'query': query,
            'include_deleted': include_deleted and 'true' or 'false'
        }
        return self.get(path, params)

    def shares(self, path, cancel=False):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#shares
        """
        path = "shares/%s%s" % (self.session.root, format_path(path))
        params = {
            'cancel': cancel and 'true' or 'false'
        }
        return self.post(path, params)

    def copy_ref(self, path):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#copy_ref
        """
        path = "copy_ref/%s%s" % (self.session.root, format_path(path))
        return self.post(path)

    def media(self, path):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#media
        """
        path = "media/%s%s" % (self.session.root, format_path(path))
        return self.get(path)

    def get_thumbnail(self, path, size, return_content=True):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#thumbnails
        """
        path = "thumbnails/%s%s" % (self.session.root, format_path(path))
        params = {
            'size': size
        }
        return self.get(path, params, follow=True, format=return_content and 'plain' or None)

    def get_thumbnail_url(self, path, size):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#thumbnails
        """
        path = "thumbnails/%s%s" % (self.session.root, format_path(path))
        params = {
            'size': size
        }
        try:
            r = self.get(path, params, format=None)
            raise request.ErrorResponse(r)
        except request.ErrorResponse, e:
            if e.status == 302:
                return e.getheader('location')
            else:
                raise e

    def copy(self, from_path, to_path, from_copy_ref=None):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#fileops_copy
        """
        params = {
            'root': self.session.root,
            'to_path': to_path
        }
        if from_copy_ref is None:
            params['from_path'] = from_path
        else:
            params['from_copy_ref'] = from_copy_ref
        return self.post('fileops/copy', params)

    def create_folder(self, path):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#create_folder
        """
        params = {
            'root': self.session.root,
            'path': path
        }
        return self.post('fileops/create_folder', params)

    def delete(self, path):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#delete
        """
        params = {
            'root': self.session.root,
            'path': path
        }
        return self.post('fileops/delete', params)

    def move(self, from_path, to_path):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#move
        """
        params = {
            'root': self.session.root,
            'from_path': from_path,
            'to_path': to_path
        }
        return self.post('fileops/move', params)

    def share_media(self, from_copy_ref):
        """
        see: http://vdisk.weibo.com/developers/index.php?module=api&action=apidoc#shareops_media
        """
        params = {
            'from_copy_ref': from_copy_ref
        }
        return self.get('shareops/media', params)