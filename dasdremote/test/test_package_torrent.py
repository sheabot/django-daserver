import os
import shutil
import tempfile

from django.test import TestCase

from dasdaemon.remote.package_torrent import TorrentPackage, TorrentDoesNotExistException
import dasdaemon.utils as utils

SIZE_1MB = 1024 * 1024

class PackageTorrentTests(TestCase):

    def setUp(self):
        # Create temp directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove test directory
        shutil.rmtree(self.test_dir)

    def _create_file(self, path, size_bytes, block_size=SIZE_1MB):
        with open(path, 'wb') as f:
            bytes_written = 0
            # TODO: This math doesn't add up
            while bytes_written < size_bytes:
                f.write(os.urandom(block_size))
                bytes_written += block_size
            while bytes_written < size_bytes:
                f.write(os.urandom(1))
                bytes_written += block_size


    def test_package_file(self):
        # Create source file
        filename = 'test-file.bin'
        filesize = SIZE_1MB * 20
        source_path = os.path.join(self.test_dir, filename)
        self._create_file(source_path, filesize)

        # Create instance
        split_bytes = SIZE_1MB
        tp = TorrentPackage(source_path, self.test_dir, split_bytes)

        # Archive source
        archive_path = tp.archive_source()
        self.assertTrue(os.path.isfile(archive_path))

        # Split archive
        split_files = tp.split_archive()

        # Verify number of split files
        expected_num_split_files = filesize / split_bytes + 1
        num_split_files = len(split_files)
        self.assertEqual(expected_num_split_files, num_split_files)

        for sf in split_files:
            path = os.path.join(self.test_dir, sf)

            # Verify split file exist
            self.assertTrue(os.path.isfile(path))

            # Verify split file size
            self.assertLessEqual(os.path.getsize(path), split_bytes)

        # Remove archive
        tp.remove_archive()
        self.assertFalse(os.path.isfile(archive_path))

    def test_package_directory(self):
        # Create source directory
        dirname = 'test-dir'
        source_path = os.path.join(self.test_dir, dirname)
        utils.fs.mkdir_p(source_path)

        # Create file in source directory
        filename = 'test-file.bin'
        filesize = SIZE_1MB * 20
        filepath = os.path.join(source_path, filename)
        self._create_file(filepath, filesize)

        # Create instance
        split_bytes = SIZE_1MB
        tp = TorrentPackage(source_path, self.test_dir, split_bytes)

        # Archive source
        archive_path = tp.archive_source()
        self.assertTrue(os.path.isfile(archive_path))

        # Split archive
        split_files = tp.split_archive()

        # Verify number of split files
        expected_num_split_files = filesize / split_bytes + 1
        num_split_files = len(split_files)
        self.assertEqual(expected_num_split_files, num_split_files)

        for sf in split_files:
            path = os.path.join(self.test_dir, sf)

            # Verify split file exist
            self.assertTrue(os.path.isfile(path))

            # Verify split file size
            self.assertLessEqual(os.path.getsize(path), split_bytes)

        # Remove archive
        tp.remove_archive()
        self.assertFalse(os.path.isfile(archive_path))

    def test_package_nonexistant(self):
        with self.assertRaises(TorrentDoesNotExistException):
            # Create instance
            tp = TorrentPackage('does-not-exist.txt', self.test_dir, 1024)
