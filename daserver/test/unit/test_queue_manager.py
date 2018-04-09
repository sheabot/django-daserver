from Queue import Queue

from dasdaemon.managers import (
    DatabaseManager,
    QueueManager
)
from dasdaemon.managers.queue_manager import Consumer
from dasdapi.models import PackageFile, Torrent

from test.unit import DaServerUnitTest


def _create_torrents(consumer, num_torrents):
    torrents = []
    for i in xrange(num_torrents):
        torrents.append(
            Torrent.objects.create(name='Torrent%d' % i, stage=consumer.ready_stage)
        )
    return torrents

def _create_package_files(consumer, num_package_files):
    torrent = Torrent.objects.create(name='TorrentWithPackageFiles', stage='NA')
    package_files = []
    for i in xrange(num_package_files):
        package_files.append(
            PackageFile.objects.create(
                filename='PackageFile%d' % i,
                torrent=torrent,
                stage=consumer.ready_stage
            )
        )
    return torrent, package_files

class QueueManagerTorrentConsumerUnitTests(DaServerUnitTest):

    def setUp(self):
        # Create queue manager
        self.qm = QueueManager()

        # Create torrent consumers
        self.consumer1 = Consumer('Stage1', 'Stage2')
        self.consumer2 = Consumer('Stage3', 'Stage4')

    def _run_qm(self):
        self.qm._execute_queries()

    def _stop_qm(self):
        self.qm.stop_consumers()


    def test_register_torrent_consumer(self):
        # Register consumer and get queue
        queue = self.qm.register_torrent_consumer(self.consumer1)

        # Verify queue created
        self.assertIsInstance(queue, Queue)

    def test_register_torrent_consumer_twice(self):
        # Register consumer and get queue
        queue1 = self.qm.register_torrent_consumer(self.consumer1)
        queue2 = self.qm.register_torrent_consumer(self.consumer1)

        # Verify queue created
        self.assertIsInstance(queue1, Queue)
        self.assertIsInstance(queue2, Queue)

        # Verify queues are the same
        self.assertEqual(queue1, queue2)

    def test_run_torrent_consumer_no_torrents(self):
        # Register consumer and get queue
        queue = self.qm.register_torrent_consumer(self.consumer1)

        # Run queue manager
        self._run_qm()

        # Verify nothing in queue
        self.assertEqual(queue.qsize(), 0)

    def test_run_one_torrent_consumer_one_torrent(self):
        # Register consumer and get queue
        queue = self.qm.register_torrent_consumer(self.consumer1)

        # Add torrent to database
        t_put = _create_torrents(self.consumer1, 1)[0]

        # Run queue manager
        self._run_qm()

        # Verify torrent in queue
        self.assertEqual(queue.qsize(), 1)
        t_get = queue.get()
        self.assertEqual(t_get, t_put)
        self.assertEqual(t_get.stage, self.consumer1.processing_stage)

        # Verify torrent in database
        self.assertEqual(Torrent.objects.get(id=t_put.id).stage, self.consumer1.processing_stage)

    def test_run_one_torrent_consumer_multiple_torrents(self):
        # Register consumer and get queue
        queue = self.qm.register_torrent_consumer(self.consumer1)

        # Add torrent to database
        num_torrents = 3
        torrents = _create_torrents(self.consumer1, num_torrents)

        # Run queue manager
        self._run_qm()

        # Verify torrent in queue
        self.assertEqual(queue.qsize(), num_torrents)

        for i in xrange(num_torrents):
            t_get = queue.get()
            self.assertEqual(t_get, torrents[i])
            self.assertEqual(t_get.stage, self.consumer1.processing_stage)

            # Verify torrent in database
            self.assertEqual(Torrent.objects.get(id=torrents[i].id).stage, self.consumer1.processing_stage)

    def test_run_multiple_different_torrent_consumers_one_torrent(self):
        # Register consumer and get queue
        queue1 = self.qm.register_torrent_consumer(self.consumer1)
        queue2 = self.qm.register_torrent_consumer(self.consumer2)

        # Add torrent to database
        t_put1 = _create_torrents(self.consumer1, 1)[0]
        t_put2 = _create_torrents(self.consumer2, 1)[0]

        # Run queue manager
        self._run_qm()

        # Verify torrents in queue
        self.assertEqual(queue1.qsize(), 1)
        t_get1 = queue1.get()
        self.assertEqual(t_get1, t_put1)
        self.assertEqual(t_get1.stage, self.consumer1.processing_stage)

        self.assertEqual(queue2.qsize(), 1)
        t_get2 = queue2.get()
        self.assertEqual(t_get2, t_put2)
        self.assertEqual(t_get2.stage, self.consumer2.processing_stage)

        # Verify torrents in database
        self.assertEqual(Torrent.objects.get(id=t_get1.id).stage, self.consumer1.processing_stage)
        self.assertEqual(Torrent.objects.get(id=t_get2.id).stage, self.consumer2.processing_stage)

    def test_stop_one_torrent_consumer_no_torrents(self):
        # Register consumer and get queue
        queue = self.qm.register_torrent_consumer(self.consumer1)

        # Stop queue manager
        self._stop_qm()

        # Verify no torrents in queue
        self.assertEqual(queue.qsize(), 1)
        self.assertEqual(queue.get(), None)

    def test_stop_two_torrent_consumers_no_torrents(self):
        # Register consumers and get queue
        queue1 = self.qm.register_torrent_consumer(self.consumer1)
        queue2 = self.qm.register_torrent_consumer(self.consumer1)

        # Stop queue manager
        self._stop_qm()

        # Verify no torrents in queue
        self.assertEqual(queue1.qsize(), 2)
        self.assertEqual(queue1.get(), None)
        self.assertEqual(queue1.get(), None)

    def test_stop_two_different_torrent_consumers_no_torrents(self):
        # Register consumers and get queue
        queue1 = self.qm.register_torrent_consumer(self.consumer1)
        queue2 = self.qm.register_torrent_consumer(self.consumer2)

        # Stop queue manager
        self._stop_qm()

        # Verify no torrents in queues
        self.assertEqual(queue1.qsize(), 1)
        self.assertEqual(queue1.get(), None)

        self.assertEqual(queue2.qsize(), 1)
        self.assertEqual(queue2.get(), None)

    def test_stop_one_torrent_consumer_one_torrent(self):
        # Register consumer and get queue
        queue = self.qm.register_torrent_consumer(self.consumer1)

        # Add torrent to database
        t_put = _create_torrents(self.consumer1, 1)[0]

        # Run queue manager
        self._run_qm()

        # Stop queue manager
        self._stop_qm()

        # Verify torrent and sentinel in queue
        self.assertEqual(queue.qsize(), 2)
        self.assertEqual(queue.get(), t_put)
        self.assertEqual(queue.get(), None)

    def test_stop_multiple_different_torrent_consumers_one_torrent(self):
        # Register consumers and get queues
        queue1 = self.qm.register_torrent_consumer(self.consumer1)
        queue2 = self.qm.register_torrent_consumer(self.consumer2)

        # Add torrents to database
        t_put1 = _create_torrents(self.consumer1, 1)[0]
        t_put2 = _create_torrents(self.consumer2, 1)[0]

        # Run queue manager
        self._run_qm()

        # Stop queue manager
        self._stop_qm()

        # Verify torrent and sentinel in queues
        self.assertEqual(queue1.qsize(), 2)
        self.assertEqual(queue1.get(), t_put1)
        self.assertEqual(queue1.get(), None)

        self.assertEqual(queue2.qsize(), 2)
        self.assertEqual(queue2.get(), t_put2)
        self.assertEqual(queue2.get(), None)


class QueueManagerPackageFileConsumerUnitTests(DaServerUnitTest):

    def setUp(self):
        # Create queue manager
        self.qm = QueueManager()

        # Create package file consumers
        self.consumer1 = Consumer('Stage1', 'Stage2')
        self.consumer2 = Consumer('Stage3', 'Stage4')

    def _run_qm(self):
        self.qm._execute_queries()

    def _stop_qm(self):
        self.qm.stop_consumers()


    def test_register_package_file_consumer(self):
        # Register consumer and get queue
        queue = self.qm.register_package_file_consumer(self.consumer1)

        # Verify queue created
        self.assertIsInstance(queue, Queue)

    def test_register_package_file_consumer_twice(self):
        # Register consumer and get queue
        queue1 = self.qm.register_package_file_consumer(self.consumer1)
        queue2 = self.qm.register_package_file_consumer(self.consumer1)

        # Verify queue created
        self.assertIsInstance(queue1, Queue)
        self.assertIsInstance(queue2, Queue)

        # Verify queues are the same
        self.assertEqual(queue1, queue2)

    def test_run_package_file_consumer_no_torrents(self):
        # Register consumer and get queue
        queue = self.qm.register_package_file_consumer(self.consumer1)

        # Run queue manager
        self._run_qm()

        # Verify nothing in queue
        self.assertEqual(queue.qsize(), 0)

    def test_run_one_package_file_consumer_one_package_file(self):
        # Register consumer and get queue
        queue = self.qm.register_package_file_consumer(self.consumer1)

        # Add package file to database
        t_put, pf_put = _create_package_files(self.consumer1, 1)

        # Run queue manager
        self._run_qm()

        # Verify package file in queue
        self.assertEqual(queue.qsize(), 1)
        pf_get = queue.get()
        self.assertEqual(pf_get, pf_put[0])
        self.assertEqual(pf_get.stage, self.consumer1.processing_stage)

        # Verify package file in database
        self.assertEqual(
            PackageFile.objects.get(id=pf_put[0].id).stage,
            self.consumer1.processing_stage
        )

    def test_run_one_package_file_consumer_multiple_package_files(self):
        # Register consumer and get queue
        queue = self.qm.register_package_file_consumer(self.consumer1)

        # Add package files to database
        num_package_files = 3
        _, package_files = _create_package_files(self.consumer1, num_package_files)

        # Run queue manager
        self._run_qm()

        # Verify package files in queue
        self.assertEqual(queue.qsize(), num_package_files)
        for i in xrange(num_package_files):
            pf_get = queue.get()
            self.assertEqual(pf_get, package_files[i])
            self.assertEqual(pf_get.stage, self.consumer1.processing_stage)

            # Verify torrent in database
            self.assertEqual(
                PackageFile.objects.get(id=package_files[i].id).stage,
                self.consumer1.processing_stage
            )

    def test_run_multiple_different_package_file_consumers_one_package_file(self):
        # Register consumer and get queue
        queue1 = self.qm.register_package_file_consumer(self.consumer1)
        queue2 = self.qm.register_package_file_consumer(self.consumer2)

        # Add package file to database
        _, pf_put1 = _create_package_files(self.consumer1, 1)
        _, pf_put2 = _create_package_files(self.consumer2, 1)

        # Run queue manager
        self._run_qm()

        # Verify package files in queue
        self.assertEqual(queue1.qsize(), 1)
        pf_get1 = queue1.get()
        self.assertEqual(pf_get1, pf_put1[0])
        self.assertEqual(pf_get1.stage, self.consumer1.processing_stage)

        self.assertEqual(queue2.qsize(), 1)
        pf_get2 = queue2.get()
        self.assertEqual(pf_get2, pf_put2[0])
        self.assertEqual(pf_get2.stage, self.consumer2.processing_stage)

        # Verify package files in database
        self.assertEqual(
            PackageFile.objects.get(id=pf_get1.id).stage,
            self.consumer1.processing_stage
        )
        self.assertEqual(
            PackageFile.objects.get(id=pf_get2.id).stage,
            self.consumer2.processing_stage
        )

    def test_stop_one_package_file_consumer_no_package_files(self):
        # Register consumer and get queue
        queue = self.qm.register_package_file_consumer(self.consumer1)

        # Stop queue manager
        self._stop_qm()

        # Verify no package files in queue
        self.assertEqual(queue.qsize(), 1)
        self.assertEqual(queue.get(), None)

    def test_stop_two_package_file_consumers_no_package_files(self):
        # Register consumers and get queue
        queue1 = self.qm.register_package_file_consumer(self.consumer1)
        queue2 = self.qm.register_package_file_consumer(self.consumer1)

        # Stop queue manager
        self._stop_qm()

        # Verify no package files in queue
        self.assertEqual(queue1.qsize(), 2)
        self.assertEqual(queue1.get(), None)
        self.assertEqual(queue1.get(), None)

    def test_stop_two_different_package_file_consumers_no_package_files(self):
        # Register consumers and get queue
        queue1 = self.qm.register_package_file_consumer(self.consumer1)
        queue2 = self.qm.register_package_file_consumer(self.consumer2)

        # Stop queue manager
        self._stop_qm()

        # Verify no package files in queues
        self.assertEqual(queue1.qsize(), 1)
        self.assertEqual(queue1.get(), None)

        self.assertEqual(queue2.qsize(), 1)
        self.assertEqual(queue2.get(), None)

    def test_stop_one_package_file_consumer_one_package_files(self):
        # Register consumer and get queue
        queue = self.qm.register_package_file_consumer(self.consumer1)

        # Add package files to database
        _, pf_put = _create_package_files(self.consumer1, 1)

        # Run queue manager
        self._run_qm()

        # Stop queue manager
        self._stop_qm()

        # Verify package files and sentinel in queue
        self.assertEqual(queue.qsize(), 2)
        self.assertEqual(queue.get(), pf_put[0])
        self.assertEqual(queue.get(), None)

    def test_stop_multiple_different_package_file_consumers_one_package_file(self):
        # Register consumers and get queues
        queue1 = self.qm.register_package_file_consumer(self.consumer1)
        queue2 = self.qm.register_package_file_consumer(self.consumer2)

        # Add package files to database
        _, pf_put1 = _create_package_files(self.consumer1, 1)
        _, pf_put2 = _create_package_files(self.consumer2, 1)

        # Run queue manager
        self._run_qm()

        # Stop queue manager
        self._stop_qm()

        # Verify package files and sentinel in queues
        self.assertEqual(queue1.qsize(), 2)
        self.assertEqual(queue1.get(), pf_put1[0])
        self.assertEqual(queue1.get(), None)

        self.assertEqual(queue2.qsize(), 2)
        self.assertEqual(queue2.get(), pf_put2[0])
        self.assertEqual(queue2.get(), None)


class QueueManagerWithDatabaseManagerUnitTests(DaServerUnitTest):

    def setUp(self):
        # Create database manager
        self.db = DatabaseManager()

        # Create and start queue manager
        self.qm = QueueManager(self.db)
        self.qm.start_consumers()

        # Create consumers
        self.consumer1 = Consumer('Stage1', 'Stage2')
        self.consumer2 = Consumer('Stage3', 'Stage4')

    def _run_db(self):
        self.db._execute_query_functions()


    def test_run(self):
        # Register consumer and get queue
        queue = self.qm.register_torrent_consumer(self.consumer1)

        # Add torrent to database
        t_put = _create_torrents(self.consumer1, 1)[0]

        # Run database_manager
        self._run_db()

         # Verify torrent in queue
        self.assertEqual(queue.qsize(), 1)
        self.assertEqual(queue.get(), t_put)
