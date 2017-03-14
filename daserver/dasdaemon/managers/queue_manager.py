from Queue import Queue
import threading

from dasdaemon.logger import log
from dasdapi.models import PackageFile, Torrent


class Consumer(object):

    def __init__(self, ready_stage, processing_stage):
        self.ready_stage = ready_stage
        self.processing_stage = processing_stage

    def __str__(self):
        return '<Consumer Ready Stage: %s, Processing Stage: %s>' % (
            self.ready_stage, self.processing_stage
        )

    def __hash__(self):
        return hash((self.ready_stage, self.processing_stage))

    def __eq__(self, other):
        return (
            (self.ready_stage, self.processing_stage) ==
            (other.ready_stage, other.processing_stage)
        )


class QueueManager(object):
    """Register queue consumers and populate queues with database objects"""

    def __init__(self, database_manager=None):
        self.torrent_consumers = {}
        self.torrent_queues = {}

        self.package_file_consumers = {}
        self.package_file_queues = {}

        self.lock = threading.Lock()
        self.stop_signal = threading.Event()
        self.database_manager = database_manager

    def register_torrent_consumer(self, consumer):
        """Register torrent consumer. If queue does not exist, then create
        a new one. Otherwise, increment consumer count and return the
        existing queue
        """
        with self.lock:
            if consumer not in self.torrent_consumers:
                self.torrent_consumers[consumer] = 0
                self.torrent_queues[consumer] = Queue()
                log.debug('Registered torrent consumer: %s', consumer)
            self.torrent_consumers[consumer] += 1
            return self.torrent_queues[consumer]

    def register_package_file_consumer(self, consumer):
        """Register package file consumer. If queue does not exist, then
        create a new one. Otherwise, increment consumer count and return
        the existing queue
        """
        with self.lock:
            if consumer not in self.package_file_consumers:
                self.package_file_consumers[consumer] = 0
                self.package_file_queues[consumer] = Queue()
                log.debug('Registered package file consumer: %s', consumer)
            self.package_file_consumers[consumer] += 1
            return self.package_file_queues[consumer]

    def start_consumers(self):
        """Register periodic database function"""
        log.info('QueueManager: Started consumers')
        self.database_manager.register_periodic_function(self._execute_queries)

    def stop_consumers(self):
        """Set stop signal for query function, and put sentinel items into
        each queue
        """
        log.info('QueueManager: Stopping consumers')
        self.stop_signal.set()
        with self.lock:
            for consumer in self.torrent_consumers:
                for _ in xrange(self.torrent_consumers[consumer]):
                    self.torrent_queues[consumer].put(None)
            for consumer in self.package_file_consumers:
                for _ in xrange(self.package_file_consumers[consumer]):
                    self.package_file_queues[consumer].put(None)

    def _get_torrents_at_stage(self, stage):
        return Torrent.objects.filter(stage=stage)

    def _get_package_files_at_stage(self, stage):
        return PackageFile.objects.filter(stage=stage)

    def _execute_queries(self):
        """Loop through consumers and put database objects into queues.
        Move database objects to processing stage before putting them into
        the queues
        """
        with self.lock:
            for consumer in self.torrent_consumers:
                if self.stop_signal.is_set():
                    return
                log.debug('Processing torrent consumer: %s', consumer)
                for obj in self._get_torrents_at_stage(consumer.ready_stage):
                    obj.stage = consumer.processing_stage
                    obj.save()
                    self.torrent_queues[consumer].put(obj)
            for consumer in self.package_file_consumers:
                if self.stop_signal.is_set():
                    return
                log.debug('Processing package file consumer: %s', consumer)
                for obj in self._get_package_files_at_stage(consumer.ready_stage):
                    obj.stage = consumer.processing_stage
                    obj.save()
                    self.package_file_queues[consumer].put(obj)
