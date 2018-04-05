import threading
import time

from dasdaemon.exceptions import DaSDWorkerGroupError
from dasdaemon.logger import log
from dasdaemon.managers.queue_manager import Consumer
from dasdapi.stages import PackageFileStage, TorrentStage, StageDoesNotExist


class DaSDWorker(threading.Thread):

    # Default to being a consumer iff the stages are set
    is_torrent_consumer = True
    is_package_file_consumer = True
    torrent_stage_name = None
    package_file_stage_name = None

    # Synchronization for do_prepare function
    _do_prepare_lock = threading.Lock()
    _do_prepare_done = threading.Event()

    def __init__(self, group=None, target=None, name=None, verbose=None, *args, **kwargs):
        super(DaSDWorker, self).__init__(group=group, target=target, name=name, verbose=verbose)

        # Process config and kwargs
        self.config = kwargs.pop('config')
        self.worker_config = self.config[self.__class__.__name__]
        self._queue_manager = kwargs.get('queue_manager')
        self.requests_manager = kwargs.get('requests_manager')
        self.path_manager = kwargs.get('path_manager')
        if not self.is_consumer:
            self._sleep = int(self.worker_config['sleep'])
        else:
            # Consumers block on queue gets, so dont need to sleep
            self._sleep = 0

        # Stop signal
        self._stop_signal = threading.Event()

        # No queue until registered as consumer
        self.torrent_queue = None
        self.package_file_queue = None

    def register_as_consumer(self):
        """Register as a torrent consumer and/or package file consumer with
        the queue manager
        """
        if self._is_torrent_consumer:
            self.torrent_queue = self._queue_manager.register_torrent_consumer(
                Consumer(self.ready_stage(), self.processing_stage())
            )

        if self._is_package_file_consumer:
            self.package_file_queue = self._queue_manager.register_package_file_consumer(
                Consumer(
                    self.package_file_ready_stage(),
                    self.package_file_processing_stage()
                )
            )

    def run(self):
        """Run init functions and call do_work repeatedly until stop
        signal is set. Then call cleanup function.
        """
        log.debug('Started')

        self._run_do_prepare()
        self.register_as_consumer()

        while not self._stop_signal.is_set():
            try:
                log.debug('Running')
                self.do_work()
            except:
                log.exception('Uncaught exception')
            finally:
                time.sleep(self._sleep)

        log.info('Stopped')

    def stop(self):
        """Set stop signal"""
        log.info('%s: Stopping', self.name)
        self._stop_signal.set()
        self.do_stop()

    def do_prepare(self):
        """This function is run once per thread after __init__ but
        before do_work. Subclass will implement this function, if desired.
        """
        pass

    def do_work(self):
        """This function is called once per thread repeatedly with a delay
        in the run loop until the stop signal is set. Subclass must implement
        this function.
        """
        raise NotImplementedError

    def do_stop(self):
        """This function is called once per thread after the stop signal
        is set. Subclass will implement this function, if desired
        """
        pass

    @property
    def is_consumer(self):
        """Return true if worker is a torrent consumer or a package file
        consumer
        """
        return self._is_torrent_consumer or self._is_package_file_consumer

    @property
    def _is_torrent_consumer(self):
        return (
            self.is_torrent_consumer and
            self.ready_stage() is not None and
            self.processing_stage() is not None
        )

    @property
    def _is_package_file_consumer(self):
        return (
            self.is_package_file_consumer and
            self.package_file_ready_stage() is not None and
            self.package_file_processing_stage() is not None
        )

    def _run_do_prepare(self):
        """Run do_prepare only once per worker group"""
        with self._do_prepare_lock:
            if not self._do_prepare_done.is_set():
                log.debug('Running do_prepare')
                self.do_prepare()
                self._do_prepare_done.set()

    """Torrent stages"""
    @classmethod
    def _torrent_stage(cls):
        return TorrentStage(cls.torrent_stage_name)

    @classmethod
    def ready_stage(cls):
        """Return previous torrent completed staged/ready stage"""
        try:
            return cls._torrent_stage().previous().name
        except StageDoesNotExist:
            return None

    @classmethod
    def processing_stage(cls):
        """Return torrent processing stage"""
        return cls._torrent_stage().name

    @classmethod
    def completed_stage(cls):
        """Return torrent completed stage"""
        try:
            return cls._torrent_stage().next().name
        except StageDoesNotExist:
            return None

    """Package file stages"""
    @classmethod
    def _package_file_stage(cls):
        return PackageFileStage(cls.package_file_stage_name)

    @classmethod
    def package_file_ready_stage(cls):
        """Return previous package file completed staged/ready stage"""
        try:
            return cls._package_file_stage().previous().name
        except StageDoesNotExist:
            return None

    @classmethod
    def package_file_processing_stage(cls):
        """Return package file processing stage"""
        return cls._package_file_stage().name

    @classmethod
    def package_file_completed_stage(cls):
        """Return package file completed stage"""
        try:
            return cls._package_file_stage().next().name
        except StageDoesNotExist:
            return None


class DaSDWorkerGroup(object):

    def __init__(self, worker_class, config, queue_manager, requests_manager, path_manager):
        # Get worker config
        self.worker_class = worker_class
        self.config = config
        self.num_workers = int(self.config[self.worker_class.__name__]['num_workers'])

        # Managers
        self.queue_manager = queue_manager
        self.requests_manager = requests_manager
        self.path_manager = path_manager

        # List of worker threads
        self.workers = []

    def start(self):
        """Create and start worker threads"""
        for i in xrange(self.num_workers):
            # Name threads '<class_name>-<thread_number>'
            worker_name = '%s-%d' % (self.worker_class.__name__, i)
            try:
                self.workers.append(
                    self.worker_class(
                        name=worker_name,
                        config=self.config,
                        queue_manager=self.queue_manager,
                        requests_manager=self.requests_manager,
                        path_manager=self.path_manager
                    )
                )
            except:
                message = 'Failed to create worker: %s' % worker_name
                log.exception(message)
                raise DaSDWorkerGroupError(message)

        log.info('Starting worker group: %s (%d workers)', self.name, self.num_workers)
        for worker in self.workers:
            worker.start()

    def stop(self):
        """Stop all worker threads"""
        for worker in self.workers:
            worker.stop()

    def join(self):
        """Join all worker threads"""
        for worker in self.workers:
            worker.join()

    @property
    def name(self):
        """Return name of worker class"""
        return self.worker_class.__name__


class DaSDQueryFunction(object):

    def do_query(self):
        # Subclass must implement this function
        raise NotImplementedError

    def run_do_query(self):
        self.do_query()


class DaSDOneTimeQueryFunction(DaSDQueryFunction):

    def __init__(self):
        self._done = False

    def run_do_query(self):
        self.do_query()
        self._done = True

    def is_done(self):
        return self._done


class DaSDPeriodicQueryFunction(DaSDQueryFunction):
    pass
