from dasdaemon.exceptions import (
    GetCompletedTorrentsError,
    DaSDRequestError
)
from dasdaemon.logger import log
from dasdaemon.workers import DaSDWorker
from dasdapi.models import Torrent


class CompletedTorrentMonitor(DaSDWorker):

    torrent_stage_name = 'Adding'

    def __init__(self, *args, **kwargs):
        super(CompletedTorrentMonitor, self).__init__(*args, **kwargs)

        # Parse config
        self.completed_torrents_url = self.worker_config['completed_torrents_url']

        # List of completed torrents
        self.completed_torrents = set()

    def do_prepare(self):
        """Find completed torrents already in database
        and add them to list
        """
        for torrent in Torrent.objects.filter(stage=self.completed_stage()):
            self.completed_torrents.add(torrent.name)
            log.info('Added: %s', torrent.name)

    def do_work(self):
        """Find new completed torrents on server and add
        them to database
        """
        for torrent in self._get_new_torrents():
            Torrent.objects.create(name=torrent, stage=self.completed_stage())
            log.info('Added: %s', torrent)

    def _get_completed_torrents(self):
        """Get list of completed torrents from server"""
        json = self.requests_manager.get_json(self.completed_torrents_url)
        return set(json)

    def _get_new_torrents(self):
        try:
            # Get set of completed torrents
            completed_torrents = self._get_completed_torrents()
        except DaSDRequestError as exc:
            # Request failed for some reason
            log.error('Failed to get completed torrents: %s', exc.message)

            # Return nothing and don't update list of completed torrents
            return set()

        # Remove previous set of completed torrents to
        # to get set of newly completed torrents.
        # Save current set of completed torrents and
        # return only the new ones.
        new_completed_torrents = completed_torrents - self.completed_torrents
        self.completed_torrents = completed_torrents
        return new_completed_torrents
