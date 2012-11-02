import unittest
import os.path
import datetime
import sys
import time

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
from weipan import session, client, request

class TestClient(unittest.TestCase):
    setup_once = False
    remote_dir = None
    def setUp(self):
        self.session = session.WeipanSession(self.app_key, self.app_secret, self.callback, self.access_type)
        self.session.set_token(self.token)
        self.client = client.WeipanClient(self.session, debug=True, delay=self.delay)
        self.local_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'app')
        self.local_pic = os.path.join(self.local_dir, 'weipan.png')
        self.local_txt = os.path.join(self.local_dir, 'test.txt')

        # Only initialize once.
        if self.setup_once == False:
            remote_dir = '/' + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            self.__class__.setup_once = True
            self.__class__.remote_dir = remote_dir

            rst = self.client.create_folder(remote_dir)
            self.assert_dir(rst)



    def print_title(self, title):
        print "\n"+'* '*10 + ' ' + title + ' ' + '* '*10

    def dict_has(self, dictionary, *args, **kwargs):
        """Convenience method to check if a dictionary contains the specified
        keys and key-value pairs"""
        for key in args:
            self.assertTrue(key in dictionary)
        for (key, value) in kwargs.items():
            self.assertEqual(value, dictionary[key])

    def assert_file(self, data, *args, **kwargs):
        default_args = (
            'size',
            'rev',
            'thumb_exists',
            'bytes',
            'modified',
            'path',
            'is_dir',
            'root',
            'icon',
            'mime_type',
            'revision',
            'md5',
            'sha1'
        )
        default_kwargs = dict(
            is_dir = False,
            root = self.session.root
        )
        combined_args = default_args + args
        combined_kwargs = dict(default_kwargs.items() + kwargs.items())
        self.dict_has(data, *combined_args, **combined_kwargs)

    def assert_dir(self, data, *args, **kwargs):
        default_args = (
            'size',
            'bytes',
            'thumb_exists',
            'rev',
            'path',
            'is_dir',
            'icon',
            'root',
            'revision'
        )
        default_kwargs = dict(
            size = '0 bytes',
            bytes = '0',
            thumb_exists = False,
            is_dir = True,
            root= self.session.root
        )
        combined_args = default_args + args
        combined_kwargs = dict(default_kwargs.items() + kwargs.items())
        self.dict_has(data, *combined_args, **combined_kwargs)

    def test_account_info(self):
        self.print_title('test_account_info')

        account_info = self.client.account_info()
        #print account_info
        self.dict_has(account_info, 
            'sina_uid',
            'uid',
            'quota_info'
        )

    def test_delta(self):
        self.print_title('test_delta')
        rst = self.client.delta()
        self.dict_has(rst,
            'reset',
            'cursor',
            'has_more',
            'entries'
        )

    def test_put_file(self):
        self.print_title('test_put_file')

        rst = self.client.put_file(self.remote_dir+'/put_test.txt', self.local_txt)
        #print rst
        self.assert_file(rst)

    def test_post_file(self):
        self.print_title('test_post_file')

        rst = self.client.post_file(self.remote_dir+'/post_test.txt', self.local_txt)
        #print rst
        self.assert_file(rst)

    def test_get_file(self):
        self.print_title('test_get_file')

        self.client.put_file(self.remote_dir+'/get_test.txt', self.local_txt)
        time.sleep(1)
        rst = self.client.get_file(self.remote_dir+'/get_test.txt')
        self.assertEqual(rst, 'test content')

    def test_get_file_url(self):
        self.print_title('test_get_file_url')

        self.client.put_file(self.remote_dir+'/get_file_url_test.txt', self.local_txt)
        rst = self.client.get_file_url(self.remote_dir+'/get_file_url_test.txt')
        self.assertEqual(rst[:4], 'http')

    def test_metadata(self):
        self.print_title('test_metadata')

        #dir
        rst = self.client.metadata(self.remote_dir)
        self.assert_dir(rst,
            'hash',
            'contents'
        )

        #file
        rst = self.client.put_file(self.remote_dir+'/metadata_test.txt', self.local_txt)
        self.assert_file(rst)

    def test_revisions(self):
        self.print_title('test_revisions')

        self.client.put_file(self.remote_dir+'/revisions_test.txt', self.local_txt)

        time.sleep(1)
        
        rst = self.client.revisions(self.remote_dir+'/revisions_test.txt')
        self.assertIsInstance(rst, list)
        self.assertEqual(len(rst), 1)

        #todo: modify
        
        
    def test_restore(self):
        self.print_title('test_revisions')

        remote_path = self.remote_dir+'/restore_test.txt'
        self.client.put_file(remote_path, self.local_txt)
        rst = self.client.delete(remote_path)
        self.dict_has(rst,
            is_deleted=True
        )

        #todo: modify
        
    def test_search(self):
        self.print_title('test_search')

        self.client.create_folder(self.remote_dir + '/test_search')
        self.client.create_folder(self.remote_dir + '/test_search/hello python')
        self.client.put_file(self.remote_dir+'/test_search/python_search_test.txt', self.local_txt)
        rst = self.client.search(self.remote_dir + '/test_search', 'python')
        self.assertIsInstance(rst, list)
        self.assertEqual(len(rst), 2)
        self.assert_dir(rst[0])
        self.assert_file(rst[1])

    def test_shares(self):
        self.print_title('test_shares')

        test_dir = self.remote_dir + '/test_shares'
        test_file = test_dir + '/test.txt'

        self.client.create_folder(test_dir)

        self.client.put_file(test_file, self.local_txt)

        # share file
        rst = self.client.shares(test_file)
        self.dict_has(rst, 
            'url'
        )

        # cancel file
        rst = self.client.shares(test_file, cancel = True)
        self.assert_file(rst,
            share=False
        )

        if self.session.root == 'basic':
            # dir share is only supported by basic apps
            
            rst = self.client.shares(test_dir)
            self.dict_has(rst,
                'url'
            )

            # cancel dir
            rst = self.client.shares(test_dir, cancel = False)
            self.assert_dir_metadata(
                is_public = False
            )

    def test_copy_ref(self):
        self.print_title('test_shares')

        self.client.put_file(self.remote_dir + '/copy_ref_test.txt', self.local_txt)
        rst = self.client.copy_ref(self.remote_dir + '/copy_ref_test.txt')
        self.dict_has(
            'copy_ref'
        )

    def test_media(self):
        self.print_title('test_media')

        self.client.put_file(self.remote_dir + '/media_weipan.png', self.local_pic)

        time.sleep(1)

        rst = self.client.media(self.remote_dir + '/media_weipan.png')
        # print rst
        self.dict_has(rst,
            'url',
            'flv_url',
            'mp3_url',
            'mp4_url',
            #'fid',
            'expires'
        )

    def test_thumbnails(self):
        self.print_title('test_thumbnails')

        self.client.put_file(self.remote_dir + '/thumbnails_weipan.png', self.local_pic)

        time.sleep(1)

        self.client.get_thumbnail(self.remote_dir + '/thumbnails_weipan.png', 's')
        rst = self.client.get_thumbnail_url(self.remote_dir + '/thumbnails_weipan.png', 's')
        self.assertEqual(rst[:4], 'http')

    def test_copy(self):
        self.print_title('test_copy')

        self.client.create_folder(self.remote_dir + '/test_copy')
        self.client.create_folder(self.remote_dir + '/test_copy/dir_a')
        self.client.put_file(self.remote_dir + '/test_copy/test.txt', self.local_txt)

        #file copy
        rst = self.client.copy(self.remote_dir + '/test_copy/test.txt', self.remote_dir + '/test_copy/dir_a/copy_test.txt')
        self.assert_file(rst)

        #dir copy
        rst = self.client.copy(self.remote_dir + '/test_copy/dir_a', self.remote_dir + '/test_copy/dir_b')
        self.assert_dir(rst)

    def test_create_folder(self):
        self.print_title('test_create_folder')

        rst = self.client.create_folder(self.remote_dir+'/test_create_folder')
        # print rst
        self.assert_dir(rst, 
            path=self.remote_dir + '/test_create_folder'
        )

    def test_delete(self):
        self.print_title('test_delete')

        self.client.create_folder(self.remote_dir + '/test_delete')

        self.client.put_file(self.remote_dir + '/test_delete/delete_test.txt', self.local_txt)

        rst = self.client.delete(self.remote_dir + '/test_delete/delete_test.txt')
        # print rst
        # note md5 and sha1 are not in rst
        self.dict_has(rst,
            is_deleted=True
        )

        rst = self.client.delete(self.remote_dir + '/test_delete')
        self.assert_dir(rst,
            'modified',
            is_deleted=True
        )

    def test_move(self):
        self.print_title('test_move')

        self.client.create_folder(self.remote_dir + '/test_move')
        self.client.put_file(self.remote_dir + '/move_test.txt', self.local_txt)

        time.sleep(1)

        # move file
        rst = self.client.move(self.remote_dir + '/move_test.txt', self.remote_dir + '/test_move/move_new_test.txt')
        self.assert_file(rst,
            'modified'
        )

        rst = self.client.move(self.remote_dir + '/test_move', self.remote_dir + '/test_move_new')
        self.assert_dir(rst,
            'modified'
        )

    def test_share_media(self):
        self.print_title('test_share_media')

        self.client.put_file(self.remote_dir + 'share_media_test.txt', self.local_txt)
        rst = self.client.copy_ref(self.remote_dir + 'share_media_test.txt')
        rst = self.client.share_media(rst['copy_ref'])
        self.dict_has(rst,
            'url',
            'flv_url',
            'mp3_url',
            'mp4_url',
            'expires'
        )



if __name__ == '__main__':
    TestClient.app_key = None
    TestClient.app_secret = None
    TestClient.callback = None
    TestClient.access_type = 'basic' in sys.argv and 'basic' or 'sandbox'
    TestClient.token = sys.argv[1]
    sys.argv[1:] = []
    TestClient.delay = 0.5
    unittest.main()