import hashlib
import os
import requests
import shutil
import tempfile

from dasdaemon.managers import RequestsManager
import dasdaemon.utils as utils

import test.common as common
from test.unit import DaServerUnitTest


class DaSDRemoteUnitTests(DaServerUnitTest):

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
        json = self.helper.create_packaged_torrent('File1.bin', total_size=self.test_filesize)

        # Save test file info
        self.test_filename = json[0]['filename']
        self.test_filehash = json[0]['sha256']
        self.url = self._get_download_url(self.test_filename)
        self.download_path = os.path.join(self.tmp, self.test_filename)

    def tearDown(self):
        # Remove temp directory
        shutil.rmtree(self.tmp)

        # Delete remote file
        self.helper.delete_packaged_torrent(self.test_filename)

    def _get_download_url(self, path):
        return self.download_url + path

    def _write_request_to_file(self, r, path, mode='wb'):
        # Write to local file
        with open(path, mode) as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    def test_dasdremote_download(self):
        # Send request
        r = self.rm.get_file_stream(self.url)

        # Verify http status code
        self.assertEqual(requests.codes.partial_content, r.status_code)

        # Write to local file
        self._write_request_to_file(r, self.download_path)

        # Verify size and sha256 of local file
        self.assertEqual(self.test_filesize, os.path.getsize(self.download_path))
        sha256 = utils.hash.sha256_file(self.download_path)
        self.assertEqual(self.test_filehash, sha256)

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

        # Verify size and sha256 of local file
        self.assertEqual(self.test_filesize, os.path.getsize(self.download_path))
        sha256 = utils.hash.sha256_file(self.download_path)
        self.assertEqual(self.test_filehash, sha256)
