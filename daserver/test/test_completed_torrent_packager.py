import json
import responses

from django.test import TestCase

import common
from dasdaemon.managers import (
    QueueManager,
    RequestsManager
)
from dasdaemon.managers.queue_manager import Consumer
from dasdaemon.workers import (
    DaSDWorkerGroup,
    CompletedTorrentPackager,
    CompletedTorrentPackagerOneTimeQueryFunction
)
from dasdapi.models import Torrent, PackageFile


class CompletedTorrentPackagerUnitTests(TestCase):

    def setUp(self):
        # Get test config
        self.config = common.load_test_config()
        self.package_torrent_url = self.config['CompletedTorrentPackager']['package_torrent_url']

        # Create managers
        self.qm = QueueManager()
        self.rm = RequestsManager(config=self.config)

        # Create instance
        self.ctp = CompletedTorrentPackager(
            config=self.config,
            queue_manager=self.qm,
            requests_manager=self.rm
        )

    def _mock_package_torrent_request(self, torrent, status=200):
        responses.reset()
        common.mock_requests_manager()
        responses.add(
            responses.POST, self.package_torrent_url, match_querystring=True,
            body=json.dumps(self.package_files), status=status,
            content_type='application/json'
        )


    @responses.activate
    def test_package_torrent(self):
        # Register as consumer with QueueManager
        self.ctp.register_as_consumer()

        # Add Torrent to database
        torrent = Torrent.objects.create(name='Torrent', stage=self.ctp.ready_stage())

        # Create list of Package Files
        self.package_files = []
        for i in xrange(10):
            self.package_files.append('%s.%d' % (torrent.name, i))

        # Run queue manager
        self.qm._execute_queries()

        # Mock request
        self._mock_package_torrent_request(torrent)

        # Run instance
        self.ctp.do_work()

        # Verify Package Files added to database
        t = Torrent.objects.get(pk=1)
        self.assertEqual(t.package_files_count, len(self.package_files))
        self.assertEqual(t.stage, self.ctp.completed_stage())

        for pf in self.package_files:
            pf_obj = PackageFile.objects.get(filename=pf)
            self.assertEqual(pf_obj.torrent.id, t.id)
            self.assertEqual(pf_obj.stage, self.ctp.package_file_completed_stage())

    @responses.activate
    def test_package_torrent_failed_request(self):
        # Register as consumer with QueueManager
        self.ctp.register_as_consumer()

        # Add Torrent to database
        torrent = Torrent.objects.create(name='Torrent', stage=self.ctp.ready_stage())

        # Create list of Package Files
        self.package_files = []
        for i in xrange(10):
            self.package_files.append('%s.%d' % (torrent.name, i))

        # Run queue manager
        self.qm._execute_queries()

        # Mock failed request
        self._mock_package_torrent_request(torrent, status=500)

        # Run instance
        self.ctp.do_work()

        # Verify torrent is at error stage and
        # package files not added to database
        t = Torrent.objects.get(pk=1)
        self.assertEqual(t.package_files_count, 0)
        self.assertEqual(t.stage, 'Error')

    def test_CompletedTorrentPackagerOneTimeQueryFunction(self):
        # Add Torrent to database that was at the processing stage, but
        # didn't finish and needs to be cleaned up
        torrent = Torrent.objects.create(
            name='Torrent',
            stage=CompletedTorrentPackager.processing_stage(),
            package_files_count=0
        )

        # Add Package Files to database
        package_files_count = 10
        for i in xrange(package_files_count):
            filename = '%s.%d' % (torrent.name, i)
            pf = PackageFile.objects.create(
                filename=filename,
                torrent=torrent,
                stage='Does Not Matter'
            )

        # Verify Package Files were created
        count = torrent.package_file_set.count()
        self.assertEqual(count, package_files_count)

        # Run one time query function
        CompletedTorrentPackagerOneTimeQueryFunction().do_query()

        # Verify Torrent was moved to ready stage
        t = Torrent.objects.get(pk=1)
        self.assertEqual(t.stage, CompletedTorrentPackager.ready_stage())

        # Verify Package Files were deleted
        count = torrent.package_file_set.count()
        self.assertEqual(count, 0)
        self.assertEqual(t.package_files_count, 0)


class CompletedTorrentPackagerIntegrationTests(TestCase):

    def setUp(self):
        # Get test config
        self.config = common.load_test_config()

        # Create managers
        self.qm = QueueManager()
        self.rm = RequestsManager(config=self.config)

        # Create test helper
        self.helper = common.TestHelper(config=self.config, requests_manager=self.rm)

        # Create instance
        self.ctp = CompletedTorrentPackager(
            config=self.config,
            queue_manager=self.qm,
            requests_manager=self.rm
        )

        # Delete remote torrents
        self.helper.delete_remote_torrents()

        # Create completed torrent
        # This seems very fragile - not sure why the tarball is doubling in size with random data
        self.completed_torrent_name = 'Completed.bin'
        self.num_package_files = 20
        r = self.helper.create_completed_torrent(self.completed_torrent_name, total_size=1024*self.num_package_files/2)
        self.assertEqual(r.status_code, 200)

    def tearDown(self):
        # Delete remote torrents
        self.helper.delete_remote_torrents()

    def test_package_torrent(self):
        # Register as consumer with QueueManager
        self.ctp.register_as_consumer()

        # Add Torrent to database
        torrent = Torrent.objects.create(
            name=self.completed_torrent_name,
            stage=self.ctp.ready_stage()
        )

        # Create list of Package Files
        self.package_files = []
        for i in xrange(self.num_package_files):
            self.package_files.append('%s.tar.%04d' % (torrent.name, i))

        # Run queue manager
        self.qm._execute_queries()

        # Run instance
        self.ctp.do_work()

        # Verify Package Files added to database
        t = Torrent.objects.get(pk=1)
        self.assertEqual(t.package_files_count, len(self.package_files))
        self.assertEqual(t.stage, self.ctp.completed_stage())

        for pf in self.package_files:
            pf_obj = PackageFile.objects.get(filename=pf)
            self.assertEqual(pf_obj.torrent.id, t.id)
            self.assertEqual(pf_obj.stage, self.ctp.package_file_completed_stage())
