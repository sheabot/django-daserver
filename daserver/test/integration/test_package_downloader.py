import os

from dasdaemon.managers import (
    PathManager,
    QueueManager,
    RequestsManager
)
import dasdaemon.utils as utils
from dasdaemon.workers import PackageDownloader
from dasdapi.models import Torrent, PackageFile

import test.common as common
from test.integration import DaServerIntegrationTest


class PackageDownloaderTests(DaServerIntegrationTest):

    def setUp(self):
        # Get test config
        self.config = common.load_test_config()

        # Create managers
        self.qm = QueueManager()
        self.rm = RequestsManager(config=self.config)
        self.pm = PathManager(config=self.config)

        self.package_files_dir = self.pm.package_files_dir.path

        # Create test helper
        self.helper = common.TestHelper(config=self.config, requests_manager=self.rm)

        # Create instance
        self.pd = PackageDownloader(
            config=self.config,
            queue_manager=self.qm,
            requests_manager=self.rm,
            path_manager=self.pm
        )

        # Create local download directory
        utils.fs.mkdir_p(self.package_files_dir)

    def tearDown(self):
        # Remove local_download_path
        utils.fs.rm_rf(self.package_files_dir)

    def _set_no_write_dir(self, dirpath):
        os.chmod(dirpath, 0o555)

    def _create_package_files(self, package_files_count, torrent_name='Torrent'):
        # Add Torrent to database
        torrent = Torrent.objects.create(name=torrent_name)

        # Add Package Files to database
        for i in xrange(package_files_count):
            filename = '%s.%04d' % (torrent.name, i)
            PackageFile.objects.create(
                filename=filename,
                torrent=torrent,
                stage=PackageDownloader.package_file_ready_stage()
            )

        # Get Package Files to return
        package_files = PackageFile.objects.filter(torrent=torrent)

        return torrent, package_files

    def test_do_work_one_file(self):
        # Create package file on remote host
        remote_filename = 'Packaged.file'
        r = self.helper.create_packaged_torrent(remote_filename)
        self.assertEqual(r.status_code, 200)

        # Add package file to database
        torrent = Torrent.objects.create(name='Torrent')
        package_file = PackageFile.objects.create(
            filename='%s.0000' % remote_filename,
            torrent=torrent,
            stage=self.pd.package_file_ready_stage()
        )

        # Register as consumer
        self.pd.register_as_consumer()

        # Run queue manager
        self.qm._execute_queries()

        # Run package downloader
        self.pd.do_work()

        # Verify package file updated
        package_file.refresh_from_db()
        self.assertEqual(self.pd.package_file_completed_stage(), package_file.stage)

        # Verify file exists
        package_file_path = os.path.join(self.package_files_dir, package_file.filename)
        package_file_path = self.pm.get_package_file_path(torrent, package_file)
        self.assertTrue(os.path.isfile(package_file_path))

    def test_do_work_no_perms(self):
        # Create Package File on remote host
        remote_filename = 'Packaged.file'
        r = self.helper.create_packaged_torrent(remote_filename)
        self.assertEqual(r.status_code, 200)

        # Add Package File to database
        torrent = Torrent.objects.create(name='Torrent')
        package_file = PackageFile.objects.create(
            filename='%s.0000' % remote_filename,
            torrent=torrent,
            stage=self.pd.package_file_ready_stage()
        )

        # Set directory read only
        self._set_no_write_dir(self.package_files_dir)

        # Register as consumer
        self.pd.register_as_consumer()

        # Run queue manager
        self.qm._execute_queries()

        # Run package downloader
        self.pd.do_work()

        # Verify file does not exist
        package_file.refresh_from_db()
        package_file_path = self.pm.get_package_file_path(torrent, package_file)
        self.assertFalse(os.path.isfile(package_file_path))

        # Verify package file is in error stage
        self.assertEqual('Error', package_file.stage)
        self.assertEqual(1, package_file.errors.count())

    def test_do_work_two_files(self):
        # Create package file on remote host
        remote_filename = 'Packaged.file'
        r = self.helper.create_packaged_torrent(remote_filename, file_count=2)
        self.assertEqual(r.status_code, 200)

        # Add package files to database
        torrent = Torrent.objects.create(name='Torrent')
        package_file1 = PackageFile.objects.create(
            filename='%s.0000' % remote_filename,
            torrent=torrent,
            stage=self.pd.package_file_ready_stage()
        )
        package_file2 = PackageFile.objects.create(
            filename='%s.0001' % remote_filename,
            torrent=torrent,
            stage=self.pd.package_file_ready_stage()
        )

        # Register as consumer
        self.pd.register_as_consumer()

        # Run queue manager
        self.qm._execute_queries()

        # Run package downloader
        self.pd.do_work()

        # Verify package file updated
        package_file1.refresh_from_db()
        self.assertEqual(self.pd.package_file_completed_stage(), package_file1.stage)

        # Verify files exist
        package_file_path1 = self.pm.get_package_file_path(torrent, package_file1)
        self.assertTrue(os.path.isfile(package_file_path1))

        # Run package downloader again
        self.pd.do_work()

        # Verify package file updated
        package_file2.refresh_from_db()
        self.assertEqual(self.pd.package_file_completed_stage(), package_file2.stage)

        # Verify files exist
        package_file_path2 = self.pm.get_package_file_path(torrent, package_file2)
        self.assertTrue(os.path.isfile(package_file_path2))

    def test_do_work_resume_file(self):
        # Create package file on remote host
        remote_filename = 'Packaged.file'
        filesize = 1234
        r = self.helper.create_packaged_torrent(remote_filename, total_size=filesize)
        self.assertEqual(r.status_code, 200)

        # Add package file to database
        torrent = Torrent.objects.create(name='Torrent')
        package_file = PackageFile.objects.create(
            filename='%s.0000' % remote_filename,
            torrent=torrent,
            stage=self.pd.package_file_ready_stage()
        )

        # Write half file data to local file
        self.pm.create_package_files_dir(torrent)
        package_file_path = self.pm.get_package_file_path(torrent, package_file)
        utils.fs.write_random_file(package_file_path, filesize / 2)
        self.assertEqual(os.path.getsize(package_file_path), filesize / 2)

        # Register as consumer
        self.pd.register_as_consumer()

        # Run queue manager
        self.qm._execute_queries()

        # Run package downloader
        self.pd.do_work()

        # Verify package file updated
        package_file.refresh_from_db()
        self.assertEqual(self.pd.package_file_completed_stage(), package_file.stage)

        # Verify file exists and filesize is correct
        package_file_path = self.pm.get_package_file_path(torrent, package_file)
        self.assertTrue(os.path.isfile(package_file_path))
        self.assertEqual(os.path.getsize(package_file_path), filesize)

    def test_do_work_resume_completed_file(self):
        # Create package file on remote host
        remote_filename = 'Packaged.file'
        filesize = 1234
        r = self.helper.create_packaged_torrent(remote_filename, total_size=filesize)
        self.assertEqual(r.status_code, 200)

        # Add package file to database
        torrent = Torrent.objects.create(name='Torrent')
        package_file = PackageFile.objects.create(
            filename='%s.0000' % remote_filename,
            torrent=torrent,
            stage=self.pd.package_file_ready_stage()
        )

        # Write full file data to local file
        self.pm.create_package_files_dir(torrent)
        package_file_path = self.pm.get_package_file_path(torrent, package_file)
        utils.fs.write_random_file(package_file_path, filesize)
        self.assertEqual(os.path.getsize(package_file_path), filesize)

        # Register as consumer
        self.pd.register_as_consumer()

        # Run queue manager
        self.qm._execute_queries()

        # Run package downloader
        self.pd.do_work()

        # Verify package file updated
        package_file.refresh_from_db()
        self.assertEqual(self.pd.package_file_completed_stage(), package_file.stage)

        # Verify file exists and filesize is correct
        package_file_path = self.pm.get_package_file_path(torrent, package_file)
        self.assertTrue(os.path.isfile(package_file_path))
        self.assertEqual(os.path.getsize(package_file_path), filesize)
