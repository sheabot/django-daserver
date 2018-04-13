"""Da Server Daemon"""
import os
import signal
import time
import threading

from dasdaemon.config import DaSDConfig
import dasdaemon.logger as logger
from dasdaemon.logger import log
from dasdaemon.managers import (
    DatabaseManager,
    PathManager,
    QueueManager,
    RequestsManager,
    WorkerManager
)


class DaServerDaemon(object):

    def __init__(self, options):
        # Process config file
        cfg = DaSDConfig()
        cfg.readfp(options.get('cfg_file'))
        self._config = cfg.get_all()

        # Setup logging
        # Set main thread name for log messages
        threading.current_thread().name = 'DaServerDaemon'
        self._init_logger()

        # Managers
        self._requests_manager = RequestsManager(config=self._config)
        self._database_manager = DatabaseManager()
        self._queue_manager = QueueManager(database_manager=self._database_manager)
        self._path_manager = PathManager(config=self._config)
        self._worker_manager = WorkerManager(
            config=self._config,
            database_manager=self._database_manager,
            queue_manager=self._queue_manager,
            requests_manager=self._requests_manager,
            path_manager=self._path_manager
        )

        # Stop signal
        self._stop_signal = threading.Event()

    def start(self):
        """Start all managers and threads"""
        log.info('Starting with pid %d', os.getpid())

        # Start managers
        try:
            self._database_manager.start()
            self._queue_manager.start_consumers()
            self._worker_manager.start()
        except:
            log.exception('Failed to start managers')
            self.stop()

        while not self._stop_signal.is_set():
            log.info('Running')
            try:
                signal.pause()
            except KeyboardInterrupt:
                self.stop()

        log.info('Dead :(')

    def stop(self):
        """Stop all managers. Stop and join all threads."""
        log.info('Stopping')
        self._stop_signal.set()

        self._database_manager.stop()
        self._worker_manager.stop()
        self._queue_manager.stop_consumers()

        self._database_manager.join()
        self._worker_manager.join()

    def _init_logger(self):
        """Get logger settings from config and initialize it"""
        logger.configure(self._config['logging'])
        log.debug('Logging configured')
