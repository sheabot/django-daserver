"""Packaged Torrent Monitor"""
from dasdaemon.exceptions import (
    GetCompletedTorrentsError,
    DaSDRequestError
)
from dasdaemon.logger import log
from dasdaemon.workers import DaSDWorker
from dasdapi.models import Torrent


class PackagedTorrentMonitor(DaSDWorker):

    torrent_stage_name = 'Packaging'

    def __init__(self, *args, **kwargs):
        super(PackagedTorrentMonitor, self).__init__(*args, **kwargs)

        # Parse config
        self.packaged_torrents_url = self.worker_config['packaged_torrents_url']

        # List of packaged torrents
        self.packaged_torrents = set()

    def do_prepare(self):
        """Find packaged torrents already in database
        and add them to list
        """
        for torrent in Torrent.objects.filter(stage=self.completed_stage()):
            self.packaged_torrents.add(torrent.name)
            log.info('Added: %s', torrent.name)

    def do_work(self):
        """Find new packaged torrents on server and add
        them to database
        """
        for torrent in self._get_new_torrents():
            try:
                Torrent.objects.create(name=torrent, stage=self.completed_stage())
                log.info('Added: %s', torrent)
            except:
                log.exception('Failed to add torrent: %s', torrent)

    def _get_packaged_torrents(self):
        """Get list of packaged torrents from server"""
        json = self.requests_manager.get_json(self.packaged_torrents_url)
        return set(json)

    def _get_new_torrents(self):
        try:
            # Get set of packaged torrents
            packaged_torrents = self._get_packaged_torrents()
        except DaSDRequestError:
            # Request failed for some reason
            log.exception('Failed to get packaged torrents')

            # Return nothing and don't update list of packaged torrents
            return set()

        # Remove previous set of packaged torrents to
        # to get set of newly packaged torrents.
        # Save current set of packaged torrents and
        # return only the new ones.
        new_packaged_torrents = packaged_torrents - self.packaged_torrents
        self.packaged_torrents = packaged_torrents
        return new_packaged_torrents
