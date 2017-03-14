"""Find torrents and package files that are queued for deletion and delete
them from the remote server
"""
from dasdaemon.logger import log
from dasdaemon.workers import DaSDWorker
from dasdapi.models import PackageFile, Torrent


class TorrentDeleter(object):

    torrent_stage_name = 'Deleting'

    def do_work(self):
        pass
