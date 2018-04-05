from importlib import import_module
import inspect
import os
import pkgutil
import sys

from dasdaemon.exceptions import DaSDWorkerGroupError
from dasdaemon.logger import log
# Must use absolute names to avoid circular imports
import dasdaemon.workers


class WorkerManager(object):

    def __init__(self, config, database_manager, queue_manager, requests_manager, path_manager):
        # Config
        self.config = config

        # Managers
        self.database_manager = database_manager
        self.queue_manager = queue_manager
        self.requests_manager = requests_manager
        self.path_manager = path_manager

        # List of worker groups
        self.worker_groups = []

    def start(self):
        """Register query functions with database manager and start
        worker groups
        """
        self._register_query_functions()
        self._start_worker_groups()

    def stop(self):
        """Stop worker groups"""
        for worker_group in self.worker_groups:
            worker_group.stop()

    def join(self):
        """Join worker groups"""
        for worker_group in self.worker_groups:
            worker_group.join()

    def _register_query_functions(self):
        """Register one time and periodic query functions with
        database manager
        """
        for cls in self._get_all_one_time_query_functions():
            function = cls().run_do_query
            self.database_manager.register_one_time_function(function)
        for cls in self._get_all_periodic_query_functions():
            function = cls().run_do_query
            self.database_manager.register_periodic_function(function)

    def _start_worker_groups(self):
        """Create a worker group for each worker class. If successful, then
        start all worker groups.
        """
        for worker_class in self._get_all_worker_classes():
            try:
                self.worker_groups.append(
                    dasdaemon.workers.DaSDWorkerGroup(
                        worker_class=worker_class,
                        config=self.config,
                        queue_manager=self.queue_manager,
                        requests_manager=self.requests_manager,
                        path_manager=self.path_manager
                    )
                )
            except:
                message = 'Failed to create worker group: %s' % worker_class.__name__
                log.exception(message)
                raise DaSDWorkerGroupError(message)

        for worker_group in self.worker_groups:
            worker_group.start()

    def _get_all_classes(self):
        # Get path to workers module
        workers_module_path = os.path.dirname(dasdaemon.workers.__file__)

        # Empty set to hold list of classes without duplicates
        class_list = set()

        # Iterate through all submodules
        for _, name, is_pkg in pkgutil.iter_modules([workers_module_path]):
            # Skip private modules
            if name.startswith('_'):
                continue

            # Import submodule
            module = import_module('dasdaemon.workers.%s' % name)

            # Get all classes in submodule and add to list
            for _, cls in inspect.getmembers(module, inspect.isclass):
                class_list.add(cls)

        # Return class list
        return list(class_list)

    def _get_all_subclasses(self, class_info):
        return [cls for cls in self._get_all_classes() if issubclass(cls, class_info) and cls != class_info]

    def _get_all_one_time_query_functions(self):
        # Return list of all DaSDOneTimeQueryFunction subclasses
        return self._get_all_subclasses(dasdaemon.workers.DaSDOneTimeQueryFunction)

    def _get_all_periodic_query_functions(self):
        # Return list of all DaSDPeriodicQueryFunction subclasses
        return self._get_all_subclasses(dasdaemon.workers.DaSDPeriodicQueryFunction)

    def _get_all_worker_classes(self):
        # Return list of all DaSDWorker subclasses
        return self._get_all_subclasses(dasdaemon.workers.DaSDWorker)
