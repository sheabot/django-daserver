"""Da Server Remote Daemon"""
import logging
import os
from Queue import Queue
import time
import threading

from django.conf import settings

from dasdremote.workers import (
    CompletedTorrentMonitor,
    CompletedTorrentPackager
)


class DaServerDaemonRemote(object):

    def __init__(self):
        # Process config
        self._complete_torrent_packager_num_threads = settings.DASDREMOTE['COMPLETED_TORRENT_PACKAGER_NUM_THREADS']

        # Set main thread name for log messages
        threading.current_thread().name = 'DaServerDaemonRemote'
        self._log = logging.getLogger('DaServerDaemonRemote')

        # Stop signal and workers
        self._stop_signal = threading.Event()
        self._workers = []
        self._queue = Queue()

    def start(self):
        """Start all managers and threads"""
        self._log.info('Starting with pid %d', os.getpid())

        # Start workers
        try:
            self._workers.append(CompletedTorrentMonitor(log=self._log, torrent_queue=self._queue))
            for _ in xrange(self._complete_torrent_packager_num_threads):
                self._workers.append(CompletedTorrentPackager(log=self._log, torrent_queue=self._queue))
            for worker in self._workers:
                worker.start()
        except:
            self._log.exception('Failed to start workers')
            self.stop()

        while not self._stop_signal.is_set():
            self._log.debug('Daemon Running')
            try:
                time.sleep(60)
            except KeyboardInterrupt:
                self.stop()

        self._log.info('Dead :(')

    def stop(self):
        """Stop all managers. Stop and join all threads."""
        self._log.info('Daemon Stopping')
        self._stop_signal.set()

        for worker in self._workers:
            worker.stop()
        for _ in xrange(self._complete_torrent_packager_num_threads):
            self._queue.put(None)
        for worker in self._workers:
            worker.join()
