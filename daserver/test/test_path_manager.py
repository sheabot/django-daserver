import os

from django.test import TestCase

import common
from dasdaemon.exceptions import PathError
from dasdaemon.managers import PathManager
from dasdaemon.managers.path_manager import PathConfig
import dasdaemon.utils as utils
from dasdapi.models import Torrent, PackageFile


class PathManagerTests(TestCase):

    def setUp(self):
        # Get test config
        self.config = common.load_test_config()

        # Create managers
        self.pm = PathManager(config=self.config)

        # Create basedir
        self.basedir = os.path.dirname(self.pm.package_files_dir.path)
        utils.fs.mkdir_p(self.basedir)

        # Create torrent
        self.torrent = Torrent.objects.create(name='TorrentName')
        self.package_file = PackageFile.objects.create(
            filename='TorrentName.tar.0001',
            torrent=self.torrent
        )

    def tearDown(self):
        utils.fs.rm_rf(self.basedir)

    def _set_no_write_dir(self, dirpath):
        os.chmod(dirpath, 0555)

    def test_PathConfig(self):
        # Format: path,owner,group,dmode,fmode
        path_config_str = 'path,dasd,dasdmaster,0775,0664'
        path_config = PathConfig(path_config_str)
        self.assertEqual('path', path_config.path)
        self.assertEqual('dasd', path_config.owner)
        self.assertEqual('dasdmaster', path_config.group)
        self.assertEqual(0775, path_config.dmode)
        self.assertEqual(0664, path_config.fmode)

    def test_get_package_files_dir(self):
        """/packages/files/dir/TorrentName/"""
        dirpath = os.path.join(self.pm.package_files_dir.path, 'TorrentName')
        self.assertEqual(dirpath, self.pm.get_package_files_dir(self.torrent))

    def test_create_package_files_dir(self):
        """/packages/files/dir/TorrentName/"""
        # Verify directory created
        dirpath = os.path.join(self.pm.package_files_dir.path, 'TorrentName')
        self.pm.create_package_files_dir(self.torrent)
        self.assertTrue(os.path.isdir(dirpath))

        # Verify ownership and permissions
        owner, group = utils.fs.get_ownership_names(dirpath)
        self.assertEqual(self.pm.package_files_dir.owner, owner)
        self.assertEqual(self.pm.package_files_dir.group, group)
        self.assertEqual(self.pm.package_files_dir.dmode, utils.fs.get_mode(dirpath))

    def test_create_package_files_dir_no_perms(self):
        """/packages/files/dir/TorrentName/"""
        # Verify directory not created
        self._set_no_write_dir(self.basedir)
        dirpath = os.path.join(self.pm.package_files_dir.path, 'TorrentName')
        with self.assertRaises(PathError):
            self.pm.create_package_files_dir(self.torrent)
        self.assertFalse(os.path.isdir(dirpath))

    def test_get_package_file_path(self):
        """/packages/files/dir/TorrentName/TorrentName.tar.0001"""
        dirpath = os.path.join(self.pm.package_files_dir.path, 'TorrentName', 'TorrentName.tar.0001')
        self.assertEqual(dirpath, self.pm.get_package_file_path(self.torrent, self.package_file))

    def test_get_package_archive_path(self):
        """/packages/files/dir/TorrentName/TorrentName.tar"""
        filepath = os.path.join(self.pm.package_files_dir.path, 'TorrentName', 'TorrentName.tar')
        self.assertEqual(filepath, self.pm.get_package_archive_path(self.torrent))

    def test_get_package_output_dir(self):
        """/unsorted/package/dir/TorrentName/"""
        dirpath = os.path.join(self.pm.unsorted_package_dir.path, 'TorrentName')
        self.assertEqual(dirpath, self.pm.get_package_output_dir(self.torrent))

    def test_create_package_output_dir(self):
        # Verify directory created
        """/unsorted/package/dir/TorrentName/"""
        dirpath = os.path.join(self.pm.unsorted_package_dir.path, 'TorrentName')
        self.pm.create_package_output_dir(self.torrent)
        self.assertTrue(os.path.isdir(dirpath))

        # Verify ownership and permissions
        owner, group = utils.fs.get_ownership_names(dirpath)
        self.assertEqual(self.pm.unsorted_package_dir.owner, owner)
        self.assertEqual(self.pm.unsorted_package_dir.group, group)
        self.assertEqual(self.pm.unsorted_package_dir.dmode, utils.fs.get_mode(dirpath))

    def test_create_package_output_dir_no_perms(self):
        # Verify directory not created
        """/unsorted/package/dir/TorrentName/"""
        self._set_no_write_dir(self.basedir)
        dirpath = os.path.join(self.pm.unsorted_package_dir.path, 'TorrentName')
        with self.assertRaises(PathError):
            self.pm.create_package_output_dir(self.torrent)
        self.assertFalse(os.path.isdir(dirpath))

    def test_chownmod_package_output_dir(self):
        # Create package output directory
        dirpath = os.path.join(self.pm.unsorted_package_dir.path, 'TorrentName')
        self.pm.create_package_output_dir(self.torrent)

        """Assemble a directory structure
        /unsorted/package/dir/TorrentName/file1
        /unsorted/package/dir/TorrentName/dir1/
        /unsorted/package/dir/TorrentName/dir1/file2
        """
        file1 = os.path.join(dirpath, 'file1')
        dir1 = os.path.join(dirpath, 'dir1')
        file2 = os.path.join(dir1, 'file2')

        # Create directory and files inside package output directory
        utils.fs.mkdir_p(dir1)
        utils.fs.write_random_file(file1, 1234)
        utils.fs.write_random_file(file2, 1234)

        # Verify permissions are not correct
        for path in [file1, dir1, file2]:
            owner, group = utils.fs.get_ownership_names(path)
            self.assertNotEqual(self.pm.unsorted_package_dir.owner, owner)
            self.assertNotEqual(self.pm.unsorted_package_dir.group, group)

        # Change permissions
        self.pm.chownmod_package_output_dir(self.torrent)

        # Verify permissions are correct
        for path in [file1, dir1, file2]:
            owner, group = utils.fs.get_ownership_names(path)
            self.assertEqual(self.pm.unsorted_package_dir.owner, owner)
            self.assertEqual(self.pm.unsorted_package_dir.group, group)



'''

package_files_dir = /tmp/dasd/test/package-files
failed_package_files_dir = /tmp/dasd/test/failed-package-files
unsorted_package_dir = /tmp/dasd/test/unsorted-packages
unknown_package_dir = /tmp/dasd/test/unknown-packages

owner = dasd
group = dasd
perms = 0775


shea        dasd dasdmaster dasdnew
dasd        dasd dasdmaster dasdnew
daserver    dasdnew

master/     dasd:dasdmaster rwxrwxr-x
new/        dasd:dasdnew    rwxrwxr-x

'''