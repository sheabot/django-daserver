from dasdaemon.managers import DatabaseManager
from dasdapi.models import Torrent

from test.unit import DaServerUnitTest


class DatabaseManagerUnitTests(DaServerUnitTest):

    def setUp(self):
        # Create database manager
        self.db = DatabaseManager()

        # Query call counters
        self._one_time_count = 0
        self._periodic_count = 0

    def _one_time_function(self):
        self._one_time_count += 1

    def _periodic_function(self):
        self._periodic_count += 1


    def test_run_one_time_function(self):
        # Register one time function
        self.db.register_one_time_function(self._one_time_function)

        # Verify function not run
        self.assertEqual(self._one_time_count, 0)

        # Run database manager
        self.db._execute_query_functions()

        # Verify function run once
        self.assertEqual(self._one_time_count, 1)

    def test_run_one_time_function_twice(self):
        # Register one time function
        self.db.register_one_time_function(self._one_time_function)

        # Run database manager
        self.db._execute_query_functions()

        # Verify function run once
        self.assertEqual(self._one_time_count, 1)

        # Run database manager
        self.db._execute_query_functions()

        # Verify function was not run again
        self.assertEqual(self._one_time_count, 1)

    def test_run_periodic_function(self):
        # Register one time function
        self.db.register_periodic_function(self._periodic_function)

        # Verify function not run
        self.assertEqual(self._periodic_count, 0)

        # Run database manager several times
        count = 0
        for _ in xrange(10):
            self.db._execute_query_functions()
            count += 1

            # Verify function is run every time
            self.assertEqual(self._periodic_count, count)
