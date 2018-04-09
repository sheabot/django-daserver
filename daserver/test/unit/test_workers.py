from mock import patch

from dasdaemon.managers import QueueManager
from dasdaemon.workers import DaSDWorker

from test.unit import DaServerUnitTest


# DaSDWorker subclass
class TestWorker(DaSDWorker):
    pass


class DasDWorkerUnitTests(DaServerUnitTest):

    def setUp(self):
        # Create Queue Manager
        self.qm = QueueManager()

        # Setup kwargs to pass to constructor
        self.kwargs = {
            'config': {
                'TestWorker': {
                    'sleep': 5
                }
            },
            'queue_manager': self.qm
        }

        # Reset threading event
        TestWorker._do_prepare_done.clear()

    def test_do_prepare_one_instance(self):
        # Create worker instance
        worker = TestWorker(**self.kwargs)

        # Mock do_prepare function and call _run_do_prepare
        with patch.object(worker, 'do_prepare') as mock_function:
            worker._run_do_prepare()

        # Verify do_prepare was called once
        mock_function.assert_called_once_with()

        # Mock do_prepare function and call _run_do_prepare again
        with patch.object(worker, 'do_prepare') as mock_function:
            worker._run_do_prepare()

        # Verify do_prepare was not called again
        mock_function.assert_not_called()

    def test_do_prepare_two_instances(self):
        # Create two worker instances
        worker1 = TestWorker(**self.kwargs)
        worker2 = TestWorker(**self.kwargs)

        # Mock do_prepare function and call _run_do_prepare
        # for both instances
        with patch.object(worker1, 'do_prepare') as mock_function1,\
             patch.object(worker2, 'do_prepare') as mock_function2:
             worker1._run_do_prepare()
             worker2._run_do_prepare()

        # Verify do_prepare was called once on the first instance
        mock_function1.assert_called_once_with()

        # Verify do_prepare was not called on the second instance
        mock_function2.assert_not_called()

        # Mock do_prepare function and call _run_do_prepare
        # for both instances again
        with patch.object(worker1, 'do_prepare') as mock_function1,\
             patch.object(worker2, 'do_prepare') as mock_function2:
             worker1._run_do_prepare()
             worker2._run_do_prepare()

        # Verify do_prepare was not called on both instances
        mock_function1.assert_not_called()
        mock_function2.assert_not_called()
