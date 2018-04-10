import os
import tempfile

from dasdaemon.managers import (
    DatabaseManager,
    PathManager,
    QueueManager
)
import dasdaemon.utils as utils
from dasdaemon.workers import PackageExtractor
from dasdapi.models import Torrent, PackageFile

import test.common as common
from test.integration import DaServerIntegrationTest


class PackageExtractorIntegrationTests(DaServerIntegrationTest):

    def setUp(self):
        # Get test config
        self.config = common.load_test_config()

        # Create managers
        self.pm = PathManager(config=self.config)
        self.db = DatabaseManager()
        self.qm = QueueManager(database_manager=self.db)

        # Create package extractor
        self.pe = PackageExtractor(
            config=self.config,
            path_manager=self.pm,
            queue_manager=self.qm
        )

        # Register as consumer
        self.pe.register_as_consumer()

    def test_do_work(self):
        # Create torrent
        torrent = Torrent.objects.create(
            name='Torrent',
            stage=self.pe.ready_stage()
        )

        # Create random file and calculate hash
        tmpdir = tempfile.mkdtemp()
        filename = 'file1.bin'
        filepath = os.path.join(tmpdir, filename)
        utils.fs.write_random_file(filepath, 10240)
        sha256 = utils.hash.sha256_file(filepath)

        # Create tarball of random file
        tarpath = os.path.join(tmpdir, torrent.name + '.tar')
        utils.arc.create_tar_file(tarpath, [filepath], basenames=True)

        # Split tarball into package files
        package_files_dir = self.pm.create_package_files_dir(torrent)
        package_file_set = utils.fs.split_file(tarpath, package_files_dir, 1024)

        # Add package files to database
        for package_file in package_file_set:
            PackageFile.objects.create(
                filename=package_file,
                torrent=torrent,
                stage='Blah'
            )

        # Delete initial files
        utils.fs.rm_rf(tmpdir)

        # Run queue manager
        self.qm._execute_queries()

        # Run package extractor
        self.pe.do_work()

        # Verify original file was extracted to package output directory
        package_output_directory = self.pm.get_package_output_dir(torrent)
        original_file = os.path.join(package_output_directory, filename)
        self.assertTrue(os.path.exists(original_file))
        self.assertEqual(sha256, utils.hash.sha256_file(original_file))

        # Verify permissions are correct
        owner, group = utils.fs.get_ownership_names(original_file)
        self.assertEqual(self.pm.unsorted_package_dir.owner, owner)
        self.assertEqual(self.pm.unsorted_package_dir.group, group)

        # Verify package archive and files were cleaned up
        self.assertFalse(os.path.exists(package_files_dir))

        # Cleanup
        utils.fs.rm_rf(package_output_directory)
