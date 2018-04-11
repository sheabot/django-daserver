import os
import shutil
import tempfile

from django.test import TestCase

from dasdremote.torrent_package import TorrentPackage, TorrentDoesNotExistException
import dasdremote.utils as utils


class PackageTorrentTests(TestCase):

    def setUp(self):
        # Create temp directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove test directory
        shutil.rmtree(self.test_dir)

    def test_package_file(self):
        # Create source file
        filename = 'test-file.bin'
        filesize = 20*utils.size.MB
        source_path = os.path.join(self.test_dir, filename)
        utils.fs.write_random_file(source_path, filesize)

        # Create instance
        split_bytes = utils.size.MB
        tp = TorrentPackage(source_path, self.test_dir, min_package_file_size=split_bytes, max_package_files=1000)

        # Archive source
        archive_path = tp.archive_source()
        self.assertTrue(os.path.isfile(archive_path))

        # Split archive
        split_files = [split_file for split_file in tp.split_archive()]

        # Verify number of split files
        expected_num_split_files = filesize / split_bytes + 1
        num_split_files = len(split_files)
        self.assertEqual(expected_num_split_files, num_split_files)

        for sf in split_files:
            path = os.path.join(self.test_dir, sf['filename'])

            # Verify split file exist
            self.assertTrue(os.path.isfile(path))

            # Verify split file size
            self.assertLessEqual(os.path.getsize(path), split_bytes)

            # Verify split file sha256
            self.assertLessEqual(utils.hash.compute_sha256(path), sf['sha256'])

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
        filesize = 20*utils.size.MB
        filepath = os.path.join(source_path, filename)
        utils.fs.write_random_file(filepath, filesize)

        # Create instance
        split_bytes = utils.size.MB
        tp = TorrentPackage(source_path, self.test_dir, min_package_file_size=split_bytes, max_package_files=1000)

        # Archive source
        archive_path = tp.archive_source()
        self.assertTrue(os.path.isfile(archive_path))

        # Split archive
        split_files = [split_file for split_file in tp.split_archive()]

        # Verify number of split files
        expected_num_split_files = filesize / split_bytes + 1
        num_split_files = len(split_files)
        self.assertEqual(expected_num_split_files, num_split_files)

        for sf in split_files:
            path = os.path.join(self.test_dir, sf['filename'])

            # Verify split file exist
            self.assertTrue(os.path.isfile(path))

            # Verify split file size
            self.assertLessEqual(os.path.getsize(path), split_bytes)

            # Verify split file sha256
            self.assertLessEqual(utils.hash.compute_sha256(path), sf['sha256'])

        # Remove archive
        tp.remove_archive()
        self.assertFalse(os.path.isfile(archive_path))

    def test_package_nonexistant(self):
        with self.assertRaises(TorrentDoesNotExistException):
            # Create instance
            tp = TorrentPackage('does-not-exist.txt', self.test_dir, 1024)

    def test_get_package_file_size(self):
        min_package_file_size = 10*utils.size.MB
        max_package_files = 1000
        tp = TorrentPackage(self.test_dir, self.test_dir, min_package_file_size, max_package_files)

        total_archive_size = 123*utils.size.MB
        package_file_size = tp.get_package_file_size(total_archive_size)
        self.assertEqual(package_file_size, min_package_file_size)
        self.assertLess(total_archive_size / package_file_size, max_package_files)

        total_archive_size = 270*utils.size.GB
        package_file_size = tp.get_package_file_size(total_archive_size)
        self.assertEqual(package_file_size, 290200492)
        self.assertLess(total_archive_size / package_file_size, max_package_files)

        total_archive_size = 12*utils.size.GB + 34*utils.size.MB + 56*utils.size.KB
        package_file_size = tp.get_package_file_size(total_archive_size)
        self.assertEqual(package_file_size, 12933544)
        self.assertLess(total_archive_size / package_file_size, max_package_files)

    def test_split_archive(self):
        min_package_file_size = 10*utils.size.KB
        max_package_files = 1000

        # Create soure file
        filepath = os.path.join(self.test_dir, 'archive.bin')
        total_archive_size = 123*utils.size.KB
        utils.fs.write_random_file(filepath, total_archive_size)

        # Create archive file
        tp = TorrentPackage(filepath, self.test_dir, min_package_file_size, max_package_files)
        tp.archive_source()

        # Overwrite archive file with known size
        archive_path = filepath + '.tar'
        utils.fs.write_random_file(archive_path, total_archive_size)

        # Verify split file sizes
        split_files = list(tp.split_archive(chunk_size=min_package_file_size+1*utils.size.KB))
        self.assertLessEqual(len(split_files), max_package_files)
        for split_file in split_files[:-1]:
            self.assertEqual(split_file['filesize'], 10*utils.size.KB)
        self.assertEqual(split_files[-1]['filesize'], 3*utils.size.KB)

        # Verify total file size
        self.assertEqual(total_archive_size, sum([sf['filesize'] for sf in split_files]))

    def test_split_archive_get_file_size_even(self):
        min_package_file_size = 10*utils.size.KB
        max_package_files = 5

        # Create soure file
        filepath = os.path.join(self.test_dir, 'archive.bin')
        total_archive_size = 123*utils.size.KB
        utils.fs.write_random_file(filepath, total_archive_size)

        # Create archive file
        tp = TorrentPackage(filepath, self.test_dir, min_package_file_size, max_package_files)
        tp.archive_source()

        # Overwrite source file with known size
        archive_path = filepath + '.tar'
        utils.fs.write_random_file(archive_path, total_archive_size)

        # Verify split file sizes
        split_files = list(tp.split_archive(chunk_size=min_package_file_size+1*utils.size.KB))
        self.assertLessEqual(len(split_files), max_package_files)
        for split_file in split_files:
            self.assertEqual(split_file['filesize'], 31488)

        # Verify total file size
        self.assertEqual(total_archive_size, sum([sf['filesize'] for sf in split_files]))

    def test_split_archive_get_file_size_uneven(self):
        min_package_file_size = 10*utils.size.KB
        max_package_files = 6

        # Create soure file
        filepath = os.path.join(self.test_dir, 'archive.bin')
        total_archive_size = 123*utils.size.KB
        utils.fs.write_random_file(filepath, total_archive_size)

        # Create archive file
        tp = TorrentPackage(filepath, self.test_dir, min_package_file_size, max_package_files)
        tp.archive_source()

        # Overwrite source file with known size
        archive_path = filepath + '.tar'
        utils.fs.write_random_file(archive_path, total_archive_size)

        # Verify split file sizes
        split_files = list(tp.split_archive(chunk_size=min_package_file_size+1*utils.size.KB))
        self.assertLessEqual(len(split_files), max_package_files)
        for split_file in split_files[:-1]:
            self.assertEqual(split_file['filesize'], 25190)
        self.assertEqual(split_files[-1]['filesize'], 2)

        # Verify total file size
        self.assertEqual(total_archive_size, sum([sf['filesize'] for sf in split_files]))
