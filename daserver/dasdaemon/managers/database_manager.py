import threading
import time

from django.conf import settings

from dasdaemon.logger import log


class DatabaseManager(threading.Thread):

    def __init__(self, group=None, target=None, name='DatabaseManager',
                 args=(), kwargs=None, verbose=None):
        super(DatabaseManager, self).__init__(group=group, target=target,
                                              name=name, verbose=verbose)

        self.one_time_functions = []
        self.periodic_functions = []
        self.lock = threading.Lock()
        self.stop_signal = threading.Event()

    def run(self):
        """Execute query functions until stopped"""
        log.info('Started with database engine: %s', settings.DATABASES['default']['ENGINE'])
        while not self.stop_signal.is_set():
            self._execute_query_functions()
            # TODO: Make this configurable
            time.sleep(5)
        log.info('Stopped')

    def stop(self):
        """Set stop signal"""
        log.info('DatabaseManager: Stopping')
        self.stop_signal.set()

    def register_one_time_function(self, function):
        """Add one time query function to list"""
        with self.lock:
            self.one_time_functions.append(function)
        log.debug('Registered one time function: %s', function.__self__)

    def register_periodic_function(self, function):
        """Add periodic query function to list"""
        with self.lock:
            self.periodic_functions.append(function)
        log.debug('Registered periodic function: %s', function.__self__)

    def _execute_query_functions(self):
        """Run one time query functions and clear the list. Then run periodic
        query functions.
        """
        with self.lock:
            for function in self.one_time_functions:
                function()
            self.one_time_functions = []
            for function in self.periodic_functions:
                function()
