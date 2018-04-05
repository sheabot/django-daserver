import os

from django.conf import settings
from inotify_simple import INotify, flags

from dasdremote.models import Torrent
from dasdremote.workers import DaSDRemoteWorker


class CompletedTorrentMonitor(DaSDRemoteWorker):

    def __init__(self, *args, **kwargs):
        super(CompletedTorrentMonitor, self).__init__(*args, **kwargs)

        # Parse config
        self._completed_torrents_dir = settings.DASDREMOTE['COMPLETED_TORRENTS_DIR']
        self._sleep = 0

        self._completed_torrents = set()
        self._inotify = INotify()
        self._watch = None

    def do_prepare(self):
        """Find completed torrents already in database
        and add them to queue if they need to be packaged.
        Start watching completed torrents directory.
        """
        for torrent in Torrent.objects.all():
            self.log.info('Found: %s', torrent.name)
            if not torrent.is_packaged():
                self.torrent_queue.put(torrent)
                self.log.info('Added: %s', torrent.name)

        self.log.info('Watching directory: %s', self._completed_torrents_dir)
        self._watch = self._inotify.add_watch(
            self._completed_torrents_dir,
            flags.MOVED_TO
        )

    def do_work(self):
        for event in self._inotify.read():
            filename = event.name
            try:
                torrent = Torrent.objects.create(name=filename)
                self.torrent_queue.put(torrent)
                self.log.info('Added: %s', filename)
            except:
                self.log.exception('Failed to create torrent: %s', filename)

    def do_stop(self):
        self.log.info('Removing directory watch: %s', self._completed_torrents_dir)
        self._inotify.rm_watch(self._watch)
