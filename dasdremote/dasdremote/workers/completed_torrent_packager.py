import os

from django.conf import settings

from dasdremote.models import PackageFile
from dasdremote.torrent_package import TorrentPackage
from dasdremote.workers import DaSDRemoteWorker


class CompletedTorrentPackager(DaSDRemoteWorker):

    def __init__(self, *args, **kwargs):
        super(CompletedTorrentPackager, self).__init__(*args, **kwargs)

        # Parse config
        self._completed_torrents_dir = settings.DASDREMOTE['COMPLETED_TORRENTS_DIR']
        self._packaged_torrents_dir = settings.DASDREMOTE['PACKAGED_TORRENTS_DIR']
        self._split_bytes = settings.DASDREMOTE['TORRENT_PACKAGE_SPLIT_BYTES']
        self._sleep = 0

    def do_work(self):
        torrent = self.torrent_queue.get()
        if torrent is None:
            return

        try:
            # Package torrent and save package files
            torrent_path = os.path.join(self._completed_torrents_dir, torrent.name)
            tp = TorrentPackage(torrent_path, self._packaged_torrents_dir, self._split_bytes)
            package_files_count = 0
            for package_file in tp.create_package():
                PackageFile.objects.create(torrent=torrent, **package_file)
                package_files_count += 1
            torrent.package_files_count = package_files_count
            torrent.save()
            self.log.info('Packaged torrent: %s (%d files)', torrent.name, torrent.package_files_count)
        except:
            self.log.exception('Failed to package torrent: %s' % torrent.name)
            self.torrent_queue.put(torrent)
