from dasdaemon.managers import PathManager
from dasdaemon.workers import PackageExtractor
from dasdapi.models import Torrent, PackageFile

import test.common as common
from test.unit import DaServerUnitTest


class PackageExtractorUnitTests(DaServerUnitTest):

    def setUp(self):
        # Get test config
        self.config = common.load_test_config()

        # Create managers
        self.pm = PathManager(config=self.config)

        # Create package extractor
        self.pe = PackageExtractor(
            config=self.config,
            path_manager=self.pm
        )

        # Create torrent
        self.torrent = Torrent.objects.create(name='Torrent')

        # Create package files
        self.num_package_files = 10
        for i in xrange(self.num_package_files):
            PackageFile.objects.create(
                filename='%s.%04d' % (self.torrent.name, i),
                torrent=self.torrent,
                stage='Does Not Matter'
            )

    def test_get_package_file_set_empty(self):
        # Create torrent with no package files
        torrent = Torrent.objects.create(name='Torrent')

        # Get package file set
        package_file_set = self.pe._get_package_file_set(torrent)

        # Verify it's empty
        self.assertEqual(0, len(package_file_set))

    def test_get_package_file_set_one_torrent(self):
        # Create torrent
        torrent = Torrent.objects.create(name='Torrent')

        # Create package files not in order
        package_file_names = [
            'Torrent.0000',
            'Torrent.0010',
            'Torrent.0007',
            'Torrent.0001'
        ]
        for package_file_name in package_file_names:
            PackageFile.objects.create(
                filename=package_file_name,
                torrent=torrent,
                stage='Does Not Matter'
            )

        # Get package file set
        package_file_set = self.pe._get_package_file_set(torrent)

        # Verify size
        self.assertEqual(len(package_file_names), len(package_file_set))

        # Verify package file names and order
        self.assertEqual(package_file_names[0], package_file_set[0].filename)
        self.assertEqual(package_file_names[3], package_file_set[1].filename)
        self.assertEqual(package_file_names[2], package_file_set[2].filename)
        self.assertEqual(package_file_names[1], package_file_set[3].filename)

    def test_get_package_file_set_two_torrents(self):
        # Create torrents
        torrent1 = Torrent.objects.create(name='Torrent1')
        torrent2 = Torrent.objects.create(name='Torrent2')

        # Create package files not in order
        package_file_names1 = [
            'Torrent1.0000',
            'Torrent1.0010',
            'Torrent1.0007',
            'Torrent1.0001'
        ]
        for package_file_name in package_file_names1:
            PackageFile.objects.create(
                filename=package_file_name,
                torrent=torrent1,
                stage='Does Not Matter'
            )

        package_file_names2 = [
            'Torrent2.0020',
            'Torrent2.0009',
            'Torrent2.0012',
            'Torrent2.0001',
            'Torrent2.0004'
        ]
        for package_file_name in package_file_names2:
            PackageFile.objects.create(
                filename=package_file_name,
                torrent=torrent2,
                stage='Does Not Matter'
            )

        # Get package file sets
        package_file_set1 = self.pe._get_package_file_set(torrent1)
        package_file_set2 = self.pe._get_package_file_set(torrent2)

        # Verify sizes
        self.assertEqual(len(package_file_names1), len(package_file_set1))
        self.assertEqual(len(package_file_names2), len(package_file_set2))

        # Verify package file names and order
        # Torrent1
        self.assertEqual(package_file_names1[0], package_file_set1[0].filename)
        self.assertEqual(package_file_names1[3], package_file_set1[1].filename)
        self.assertEqual(package_file_names1[2], package_file_set1[2].filename)
        self.assertEqual(package_file_names1[1], package_file_set1[3].filename)

        # Torrent2
        self.assertEqual(package_file_names2[3], package_file_set2[0].filename)
        self.assertEqual(package_file_names2[4], package_file_set2[1].filename)
        self.assertEqual(package_file_names2[1], package_file_set2[2].filename)
        self.assertEqual(package_file_names2[2], package_file_set2[3].filename)
        self.assertEqual(package_file_names2[0], package_file_set2[4].filename)
