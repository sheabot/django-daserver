import hashlib
import os
import requests
import shutil
import tempfile

from django.test import TestCase

import common
from dasdaemon.managers import RequestsManager


class DaSDRemoteDownloadTests(TestCase):

    def setUp(self):
        # Get test config
        self.config = common.load_test_config()
        self.download_url = self.config['PackageDownloader']['download_url']

        # Create requests manager
        self.rm = RequestsManager(config=self.config)

        # Create test helper
        self.helper = common.TestHelper(config=self.config, requests_manager=self.rm)

        # Create temp directory
        self.tmp = tempfile.mkdtemp()

        # Create test file
        self.test_filesize = 1048576
        r = self.helper.create_packaged_torrent('File1.bin', total_size=self.test_filesize)
        self.assertEqual(r.status_code, 200)

        # Save test file info
        data = r.json()[0]
        self.test_filename = data['filename']
        self.test_filehash = data['md5']
        self.url = self._get_download_url(self.test_filename)
        self.download_path = os.path.join(self.tmp, self.test_filename)

    def tearDown(self):
        # Remove temp directory
        shutil.rmtree(self.tmp)

        # Delete remote file
        r = self.helper.delete_packaged_torrent(self.test_filename)

    def _get_download_url(self, path):
        return self.download_url + path

    def _write_request_to_file(self, r, path, mode='wb'):
        # Write to local file
        with open(path, mode) as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    def _compute_md5(self, path):
        md5 = hashlib.md5()
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                md5.update(chunk)
        return md5.hexdigest()

    def test_dasdremote_download(self):
        # Send request
        r = self.rm.get_file_stream(self.url)

        # Verify http status code
        self.assertEqual(requests.codes.partial_content, r.status_code)

        # Write to local file
        self._write_request_to_file(r, self.download_path)

        # Verify md5 of local file
        md5 = self._compute_md5(self.download_path)
        self.assertEqual(self.test_filehash, md5)

    def test_dasdremote_download_resume(self):
        # Send request for half of file
        length = self.test_filesize / 2
        r = self.rm.get_file_stream(self.url, start=0, stop=length-1)

        # Verify http status code
        self.assertEqual(requests.codes.partial_content, r.status_code)

        # Write to local file
        self._write_request_to_file(r, self.download_path)

        # Verify local filesize
        self.assertEqual(length, os.path.getsize(self.download_path))

        # Send request for second half of file
        r = self.rm.get_file_stream(self.url, start=length)

        # Verify http status code
        self.assertEqual(requests.codes.partial_content, r.status_code)

        # Append to local file
        self._write_request_to_file(r, self.download_path, mode='ab')

        # Verify md5 of local file
        md5 = self._compute_md5(self.download_path)
        self.assertEqual(self.test_filehash, md5)

