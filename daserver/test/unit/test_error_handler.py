import time

from mock import patch

from dasdaemon.exceptions import DaSDError
from dasdaemon.workers.error import ErrorHandlerPeriodicQueryFunction
from dasdapi.models import Torrent
from dasdapi.stages import TorrentStage

from test.unit import DaServerUnitTest


class DaSDTestError1(DaSDError):
    message = 'Test Error 1'

class DaSDTestError2(DaSDError):
    message = 'Test Error 2'


@patch.object(TorrentStage, 'ordered_stages', [
    'P1', 'C1',
    'P2', 'C2',
    'P3', 'C3'
])
class ErrorHandlerUnitTests(DaServerUnitTest):

    def setUp(self):
        # Create Torrent
        self.torrent = Torrent.objects.create(name='Torrent', stage='P2')

    def test_set_error_once(self):
        # Verify no errors
        self.assertEqual(0, self.torrent.errors.count())

        # Set error on Torrent
        error = DaSDTestError1('Test Error 1')
        self.torrent.set_error(error)

        # Verify error was saved
        self.assertEqual(1, self.torrent.errors.count())

        # Verify error fields
        torrent_error = self.torrent.errors.first()
        self.assertEqual(error.id, torrent_error.type)
        self.assertEqual(error.message, torrent_error.message)
        self.assertEqual('P2', torrent_error.stage)
        self.assertEqual(1, torrent_error.count)
        self.assertEqual(2 ** 2, torrent_error.retry_delay)

    def test_set_error_twice(self):
        # Set error on Torrent twice
        error = DaSDTestError1('Test Error 1')
        self.torrent.set_error(error)
        self.torrent.set_error(error)

        # Verify error was saved
        self.assertEqual(1, self.torrent.errors.count())

        # Verify error fields
        torrent_error = self.torrent.errors.first()
        self.assertEqual(error.id, torrent_error.type)
        self.assertEqual(error.message, torrent_error.message)
        self.assertEqual('P2', torrent_error.stage)
        self.assertEqual(2, torrent_error.count)
        self.assertEqual(2 ** 2 ** 2, torrent_error.retry_delay)

    def test_set_error_two_types_once(self):
        # Set first error on Torrent
        error1 = DaSDTestError1('Test Error 1')
        self.torrent.set_error(error1)

        # Set new stage
        self.torrent.stage = 'P3'
        self.torrent.save()

        # Set second error on Torrent
        error2 = DaSDTestError2('Test Error 2')
        self.torrent.set_error(error2)

        # Verify both errors were saved
        self.assertEqual(2, self.torrent.errors.count())

        # Verify error1 fields
        torrent_error1 = self.torrent.errors.all()[1]
        self.assertEqual(error1.id, torrent_error1.type)
        self.assertEqual(error1.message, torrent_error1.message)
        self.assertEqual('P2', torrent_error1.stage)
        self.assertEqual(1, torrent_error1.count)
        self.assertEqual(2 ** 2, torrent_error1.retry_delay)

        # Verify error2 fields
        torrent_error2 = self.torrent.errors.all()[0]
        self.assertEqual(error2.id, torrent_error2.type)
        self.assertEqual(error2.message, torrent_error2.message)
        self.assertEqual('P3', torrent_error2.stage)
        self.assertEqual(1, torrent_error2.count)
        self.assertEqual(2 ** 2, torrent_error2.retry_delay)

    def test_ErrorHandlerPeriodicQueryFunction(self):
        # Set error on Torrent
        error1 = DaSDTestError1('Test Error 1')
        self.torrent.set_error(error1)

        # Verify torrent stage
        self.assertEqual('Error', self.torrent.stage)

        # Sleep for retry delay
        time.sleep(self.torrent.errors.first().retry_delay + 1)

        # Run periodic query function
        ErrorHandlerPeriodicQueryFunction().do_query()

        # Verify torrent stage
        self.torrent.refresh_from_db()
        self.assertEqual('C1', self.torrent.stage)
