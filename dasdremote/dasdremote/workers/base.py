import threading
import time


class DaSDRemoteWorker(threading.Thread):

    def __init__(self, log, torrent_queue, *args, **kwargs):
        super(DaSDRemoteWorker, self).__init__(*args, **kwargs)
        self._stop_signal = threading.Event()
        self.log = log
        self.torrent_queue = torrent_queue

    def run(self):
        """Run init functions and call do_work repeatedly until stop
        signal is set. Then call cleanup function.
        """
        self.log.debug('Started')

        self.do_prepare()

        while not self._stop_signal.is_set():
            try:
                self.log.debug('Running: %s', self.__class__.__name__)
                self.do_work()
            except:
                self.log.exception('Uncaught exception')
            finally:
                time.sleep(self._sleep)

        self.log.info('Stopped: %s', self.__class__.__name__)

    def stop(self):
        """Set stop signal"""
        self.log.info('%s: Stopping', self.__class__.__name__)
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
