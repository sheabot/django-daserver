from mock import patch

from django.test import TestCase

import common
from dasdaemon.managers import (
    DatabaseManager,
    PathManager,
    QueueManager,
    RequestsManager,
    WorkerManager
)
import dasdaemon.workers.base
from dasdaemon.workers import (
    DaSDOneTimeQueryFunction,
    DaSDPeriodicQueryFunction,
    PackageDownloader,
    PackageDownloaderOneTimeQueryFunction,
    PackageDownloaderPeriodicQueryFunction,
    PackagedTorrentLister,
    PackagedTorrentListerOneTimeQueryFunction,
    PackagedTorrentMonitor,
    PackageExtractor
)
from dasdaemon.workers.error import ErrorHandlerPeriodicQueryFunction


class TestOneTimeQueryFunction(DaSDOneTimeQueryFunction):
    pass


class TestPeriodicQueryFunction(DaSDPeriodicQueryFunction):
    pass


class WorkerManagerTests(TestCase):

    def setUp(self):
        # Config
        self.config = common.load_test_config()

        # Create other managers
        self.db = DatabaseManager()
        self.qm = QueueManager(database_manager=self.db)
        self.rm = RequestsManager(config=self.config)
        self.pm = PathManager(config=self.config)

        # Create WorkerManager
        self.wm = WorkerManager(
            config=self.config,
            database_manager=self.db,
            queue_manager=self.qm,
            requests_manager=self.rm,
            path_manager=self.pm
        )

    def test_get_all_one_time_query_functions(self):
        # Get all one time query functions
        query_functions = self.wm._get_all_one_time_query_functions()

        # Verify query functions
        self.assertItemsEqual(
            query_functions, [
                PackageDownloaderOneTimeQueryFunction,
                PackagedTorrentListerOneTimeQueryFunction
            ]
        )

    def test_get_all_periodic_query_functions(self):
        # Get all periodic query functions
        query_functions = self.wm._get_all_periodic_query_functions()

        # Verify query functions
        self.assertItemsEqual(
            query_functions, [
                ErrorHandlerPeriodicQueryFunction,
                PackageDownloaderPeriodicQueryFunction
            ]
        )

    def test_run_one_time_query_function(self):
        # Create test one time query function
        dasdaemon.workers.base.TestOneTimeQueryFunction = TestOneTimeQueryFunction

        # Register query functions
        self.wm._register_query_functions()

        # Mock do_query function
        with patch.object(TestOneTimeQueryFunction, 'do_query') as mock_method:
            # Run database manager
            self.db._execute_query_functions()

            # Verify do_query was called once
            mock_method.assert_called_once_with()

        # Mock do_query function
        with patch.object(TestOneTimeQueryFunction, 'do_query') as mock_method:
            # Run database manager again
            self.db._execute_query_functions()

            # Verify do_query was not called again
            mock_method.assert_not_called()

        # Remove test query function
        dasdaemon.workers.base.TestOneTimeQueryFunction = None

    def test_run_periodic_query_function(self):
        # Create test periodic query function
        dasdaemon.workers.base.TestPeriodicQueryFunction = TestPeriodicQueryFunction

        # Register query functions
        self.wm._register_query_functions()

        # Mock do_query function
        with patch.object(TestPeriodicQueryFunction, 'do_query') as mock_method:
            # Run database manager
            self.db._execute_query_functions()

            # Verify do_query was called once
            mock_method.assert_called_once_with()

        # Mock do_query function
        with patch.object(TestPeriodicQueryFunction, 'do_query') as mock_method:
            # Run database manager again
            self.db._execute_query_functions()

            # Verify do_query was called again
            mock_method.assert_called_once_with()

        # Remove test query function
        dasdaemon.workers.base.TestPeriodicQueryFunction = None

    def test_get_all_worker_classes(self):
        # Get all worker classes
        worker_classes = self.wm._get_all_worker_classes()

        # Verify worker classes
        self.assertItemsEqual(
            worker_classes, [
                PackageDownloader,
                PackagedTorrentLister,
                PackagedTorrentMonitor,
                PackageExtractor
            ]
        )
