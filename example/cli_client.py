#!/usr/bin/env python

import cmd
import locale
import os
import pprint
import shlex
import sys
import webbrowser
import getpass
import re
import urlparse

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from weipan import client, request, session, local

# XXX Fill in your consumer key and secret below
# You can find these at http://vdisk.weibo.com/developers
APP_KEY = ''
APP_SECRET = ''
CALLBACK = ''
ACCESS_TYPE = 'sandbox'

def command(login_required=True):
    """a decorator for handling authentication and exceptions"""
    def decorate(f):
        def wrapper(self, args):
            if login_required and not self.sess.is_linked():
                self.stdout.write("Please 'login' to execute this command\n")
                return

            try:
                return f(self, *args)
            except TypeError, e:
                self.stdout.write(str(e) + '\n')
            except request.ErrorResponse, e:
                msg = str(e)
                self.stdout.write('Error: %s\n' % msg)

        wrapper.__doc__ = f.__doc__
        return wrapper
    return decorate

class WeipanTerm(cmd.Cmd):
    def __init__(self, app_key, app_secret, callback, access_type):
        cmd.Cmd.__init__(self)
        self.sess = StoredSession(app_key, app_secret, callback, access_type)
        self.api_client = client.WeipanClient(self.sess)
        self.current_path = ''
        self.prompt = "Weipan> "

        self.sess.load_creds()

    @command()
    def do_ls(self):
        """list files in current remote directory"""
        resp = self.api_client.metadata(self.current_path)

        if 'contents' in resp:
            for f in resp['contents']:
                name = os.path.basename(f['path'])
                encoding = locale.getdefaultlocale()[1]
                self.stdout.write(('%s\n' % name).encode(encoding))

    @command()
    def do_cd(self, path):
        """change current working directory"""
        if path == "..":
            self.current_path = "/".join(self.current_path.split("/")[0:-1])
        else:
            self.current_path += "/" + path

    @command(login_required=False)
    def do_login(self):
        """log in to a Weipan account"""
        try:
            self.sess.link('auth')
        except request.ErrorResponse, e:
            self.stdout.write('Error: %s\n' % str(e))

    @command()
    def do_logout(self):
        """log out of the current Weipan account"""
        self.sess.unlink()
        self.current_path = ''

    @command()
    def do_cat(self, path):
        """display the contents of a file"""
        f = self.api_client.get_file(self.current_path + "/" + path)
        self.stdout.write(f)
        self.stdout.write("\n")

    @command()
    def do_mkdir(self, path):
        """create a new directory"""
        self.api_client.create_folder(self.current_path + "/" + path)

    @command()
    def do_rm(self, path):
        """delete a file or directory"""
        self.api_client.delete(self.current_path + "/" + path)

    @command()
    def do_mv(self, from_path, to_path):
        """move/rename a file or directory"""
        self.api_client.move(self.current_path + "/" + from_path,
                                  self.current_path + "/" + to_path)

    @command()
    def do_account_info(self):
        """display account information"""
        f = self.api_client.account_info()
        pprint.PrettyPrinter(indent=2).pprint(f)

    @command(login_required=False)
    def do_exit(self):
        """exit"""
        return True

    @command()
    def do_get(self, from_path, to_path):
        """
        Copy file from Weipan to local file.

        Examples:
        Weipan> get file.txt ~/weipan-file.txt
        """
        to_file = open(os.path.expanduser(to_path), "wb")

        f = self.api_client.get_file(self.current_path + "/" + from_path)
        to_file.write(f)

    @command()
    def do_thumbnail(self, from_path, to_path, size='l'):
        """
        Copy an image file's thumbnail to a local file.

        Examples:
        Weipan> thumbnail file.txt ~/weipan-file.txt m
        """
        to_file = open(os.path.expanduser(to_path), "wb")

        f = self.api_client.get_thumbnail(
                self.current_path + "/" + from_path, size)
        to_file.write(f)

    @command()
    def do_put(self, from_path, to_path):
        """
        Copy local file to Weipan

        Examples:
        Weipan> put ~/test.txt weipan-copy-test.txt
        """
        from_file = open(os.path.expanduser(from_path), "rb")

        self.api_client.put_file(self.current_path + "/" + to_path, from_file)

    @command()
    def do_search(self, string):
        """Search Weipan for filenames containing the given string."""
        results = self.api_client.search(self.current_path, string)
        for r in results:
            self.stdout.write("%s\n" % r['path'])

    @command(login_required=False)
    def do_help(self):
        # Find every "do_" attribute with a non-empty docstring and print
        # out the docstring.
        all_names = dir(self)
        cmd_names = []
        for name in all_names:
            if name[:3] == 'do_':
                cmd_names.append(name[3:])
        cmd_names.sort()
        for cmd_name in cmd_names:
            f = getattr(self, 'do_' + cmd_name)
            if f.__doc__:
                self.stdout.write('%s: %s\n' % (cmd_name, f.__doc__))

    # the following are for command line magic
    def emptyline(self):
        pass

    def do_EOF(self, line):
        self.stdout.write('\n')
        return True

    def parseline(self, line):
        parts = shlex.split(line)
        if len(parts) == 0:
            return None, None, line
        else:
            return parts[0], parts[1:], line


class StoredSession(session.WeipanSession):
    """a wrapper around WeipanSession that stores a token to a file on disk"""
    TOKEN_FILE = "weipan_token.txt"

    def load_creds(self):
        try:
            stored_creds = open(self.TOKEN_FILE).read()
            self.set_token(stored_creds)
            print "[loaded access token]"
        except IOError:
            pass # don't worry if it's not there

    def write_creds(self, token):
        f = open(self.TOKEN_FILE, 'w')
        f.write(token)
        f.close()

    def delete_creds(self):
        os.unlink(self.TOKEN_FILE)

    def link(self, type='auth'):
        if type == 'auth':
            # link with code
            url = self.build_authorize_url()
            webbrowser.open(url)
            urlinfo = urlparse.urlparse(self.callback)
            if urlinfo.hostname in ['localhost', '127.0.0.1']:
                print "Please authorize in the browser."
                code = local.receive_code(urlinfo.port is None and '80' or urlinfo.port)
                if code == False:
                    print "Authorization failed."
                    return
                else:
                    print "Authorization succeeded."
            else:
                print "url:", url
                print "Please authorize in the browser, and input authorization code below."
                code = raw_input("Authorization code: ")
                
            token = self.access_token_with_code(code)        
        else:
            # not supported yet
            username = raw_input("Username: ")
            password = getpass.getpass("Password: ")
            token = self.access_token_with_password(username, password)

        self.token = token['access_token']
        self.write_creds(self.token)

    def unlink(self):
        self.delete_creds()
        session.WeipanSession.unlink(self)


def main():
    # try to get configs from weipan-sdk-python/shAdOw.py
    try:
        from shAdOw import APP_KEY, APP_SECRET, CALLBACK, ACCESS_TYPE
    except:
        pass

    if APP_KEY == '' or APP_SECRET == '':
        exit("You need to set your APP_KEY and APP_SECRET!")
    term = WeipanTerm(APP_KEY, APP_SECRET, CALLBACK, ACCESS_TYPE)
    term.cmdloop()

if __name__ == '__main__':
    main()
