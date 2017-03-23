import json
import responses

from django.test import TestCase

import common
from dasdaemon.managers import (
    QueueManager,
    RequestsManager
)
from dasdaemon.workers import CompletedTorrentMonitor
from dasdapi.models import Torrent


class CompletedTorrentMonitorUnitTests(TestCase):

    def setUp(self):
        # Get test config
        self.config = common.load_test_config()
        self.completed_torrents_url = self.config['CompletedTorrentMonitor']['completed_torrents_url']

        # Create managers
        self.qm = QueueManager()
        self.rm = RequestsManager(config=self.config)

        # Create instance
        self.ctm = CompletedTorrentMonitor(
            config=self.config,
            queue_manager=self.qm,
            requests_manager=self.rm
        )

    def _mock_completed_torrents_request(self, torrents, status=200):
        responses.reset()
        common.mock_requests_manager()
        responses.add(
            responses.GET, self.completed_torrents_url, match_querystring=True,
            body=json.dumps(torrents), status=status,
            content_type='application/json'
        )


    @responses.activate
    def test_get_new_torrents(self):
        # List of completed torrents
        torrents = ['File1.rar', 'File2.zip']

        # Mock request
        self._mock_completed_torrents_request(torrents)

        # Get new torrents
        # Verify list contains all of original list
        self.assertEqual(self.ctm._get_new_torrents(), set(torrents))

        # Add new completed torrent to list
        new_torrent = 'File3.txt'
        torrents.append(new_torrent)

        # Mock request to url
        self._mock_completed_torrents_request(torrents)

        # Get new torrents
        # Verify list contains only new torrent
        self.assertEqual(self.ctm._get_new_torrents(), set([new_torrent]))

    @responses.activate
    def test_get_new_torrents_failed_request(self):
        # List of completed torrents
        torrents = ['File1.rar', 'File2.zip']

        # Mock request
        self._mock_completed_torrents_request(torrents)

        # Get new torrents
        # Verify list contains all of original list
        self.assertEqual(self.ctm._get_new_torrents(), set(torrents))

        # Add new completed torrent to list
        new_torrent = 'File3.txt'
        torrents.append(new_torrent)

        # Mock FAILED request to url
        self._mock_completed_torrents_request(torrents, status=403)

        # Get new torrents
        # Verify list contains nothing
        self.assertEqual(self.ctm._get_new_torrents(), set())

        # Mock request to url
        self._mock_completed_torrents_request(torrents)

        # Get new torrents
        # Verify list contains only new torrent
        self.assertEqual(self.ctm._get_new_torrents(), set([new_torrent]))

    @responses.activate
    def test_new_torrent_added_to_database(self):
        # List of completed torrents
        torrents = ['File1.rar']

        # Mock request
        self._mock_completed_torrents_request(torrents)

        # Run instance
        self.ctm.do_work()

        # Verify torrent added to database
        self.assertEqual(Torrent.objects.count(), 1)
        t = Torrent.objects.get(pk=1)
        self.assertEqual(t.name, 'File1.rar')
        self.assertEqual(t.stage, 'Added')

    def test_do_prepare(self):
        # Add torrent to database that would have been leftover
        # from a previous run that was stopped or died
        t = Torrent.objects.create(
            name='Torrent',
            stage=self.ctm.completed_stage()
        )

        # Run prepare
        self.ctm.do_prepare()

        # Verify torrent added to list of completed torrents
        self.assertEqual(len(self.ctm.completed_torrents), 1)
        self.assertTrue(t.name in self.ctm.completed_torrents)


class CompletedTorrentMonitorIntegrationTests(TestCase):

    def setUp(self):
        # Get test config
        self.config = common.load_test_config()

        # Create managers
        self.qm = QueueManager()
        self.rm = RequestsManager(config=self.config)

        # Create test helper
        self.helper = common.TestHelper(config=self.config, requests_manager=self.rm)

        # Create instance
        self.ctm = CompletedTorrentMonitor(
            config=self.config,
            queue_manager=self.qm,
            requests_manager=self.rm
        )

        # Delete remote torrents
        self.helper.delete_remote_torrents()

    def tearDown(self):
        # Delete remote torrents
        self.helper.delete_remote_torrents()

    def test_get_new_torrents_files(self):
        # Create completed torrents
        torrents = ['File1.rar', 'File2.zip']
        for t in torrents:
            r = self.helper.create_completed_torrent(t)
            self.assertEqual(r.status_code, 200)

        # Get new torrents
        # Verify list contains all of original list
        self.assertEqual(self.ctm._get_new_torrents(), set(torrents))

        # Add new completed torrent to list
        new_torrent = 'File3.txt'
        torrents.append(new_torrent)

        # Create new completed torrent
        r = self.helper.create_completed_torrent(new_torrent)
        self.assertEqual(r.status_code, 200)

        # Get new torrents
        # Verify list contains only new torrent
        self.assertEqual(self.ctm._get_new_torrents(), set([new_torrent]))

        # Delete torrents
        for t in torrents:
            self.helper.delete_completed_torrent(t)

    def test_get_new_torrents_dirs(self):
        # Create completed torrents
        torrents = ['Dir1', 'Dir2']
        for t in torrents:
            r = self.helper.create_completed_torrent(t, file_count=3, total_size=1024*3)
            self.assertEqual(r.status_code, 200)

        # Get new torrents
        # Verify list contains all of original list
        self.assertEqual(self.ctm._get_new_torrents(), set(torrents))

        # Add new completed torrent to list
        new_torrent = 'Dir3'
        torrents.append(new_torrent)

        # Create new completed torrent
        r = self.helper.create_completed_torrent(new_torrent, file_count=3, total_size=1024*3)
        self.assertEqual(r.status_code, 200)

        # Get new torrents
        # Verify list contains only new torrent
        self.assertEqual(self.ctm._get_new_torrents(), set([new_torrent]))

        # Delete torrents
        for t in torrents:
            self.helper.delete_completed_torrent(t)

    def test_get_new_torrents_mixed(self):
        # Create completed torrents
        file_torrents = ['File1.rar', 'File2.zip']
        for t in file_torrents:
            r = self.helper.create_completed_torrent(t)
            self.assertEqual(r.status_code, 200)

        dir_torrents = ['Dir1', 'Dir2']
        for t in dir_torrents:
            r = self.helper.create_completed_torrent(t, file_count=3, total_size=1024*3)
            self.assertEqual(r.status_code, 200)

        all_torrents = file_torrents + dir_torrents

        # Get new torrents
        # Verify list contains all of original list
        self.assertEqual(self.ctm._get_new_torrents(), set(all_torrents))

        # Add new completed torrents to list
        new_file_torrent = 'File3.txt'
        new_dir_torrent = 'Dir3'
        all_torrents.append(new_file_torrent)
        all_torrents.append(new_dir_torrent)

        # Create new completed torrents
        r = self.helper.create_completed_torrent(new_file_torrent)
        self.assertEqual(r.status_code, 200)
        r = self.helper.create_completed_torrent(new_dir_torrent, file_count=3, total_size=1024*3)
        self.assertEqual(r.status_code, 200)

        # Get new torrents
        # Verify list contains only new torrent
        self.assertEqual(self.ctm._get_new_torrents(), set([new_file_torrent, new_dir_torrent]))

        # Delete torrents
        for t in all_torrents:
            self.helper.delete_completed_torrent(t)
