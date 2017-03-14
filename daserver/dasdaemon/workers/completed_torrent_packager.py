"""Completed Torrent Packager"""
from dasdaemon.logger import log
from dasdaemon.workers import DaSDWorker, DaSDOneTimeQueryFunction
from dasdaemon.exceptions import (
    DaSDRequestError,
    PackageCompletedTorrentError
)
from dasdapi.models import PackageFile, Torrent


class CompletedTorrentPackagerOneTimeQueryFunction(DaSDOneTimeQueryFunction):

    def do_query(self):
        """Find torrents that started the processing stage, but did not finish.
        Then, delete the corresponding package files from the database and move
        the torrent back to the ready stage.
        """
        torrents = Torrent.objects.filter(
            stage=CompletedTorrentPackager.processing_stage(),
            package_files_count=0
        )

        for torrent in torrents:
            count = PackageFile.objects.filter(torrent=torrent).delete()[0]
            log.debug('Torrent %s: Deleted %d package files', torrent, count)

            torrent.stage = CompletedTorrentPackager.ready_stage()
            torrent.save()


class CompletedTorrentPackager(DaSDWorker):

    torrent_stage_name = 'Packaging'
    package_file_stage_name = 'Adding'

    def __init__(self, *args, **kwargs):
        super(CompletedTorrentPackager, self).__init__(*args, **kwargs)

        # Parse config
        self.package_torrent_url = self.worker_config['package_torrent_url']

    def _package_completed_torrent(self, torrent):
        """Package completed torrent on server"""
        try:
            return self.requests_manager.post_json(
                self.package_torrent_url,
                data={
                    'torrent': torrent.name
                }
            )
        except DaSDRequestError as exc:
            raise PackageCompletedTorrentError(exc.message)

    def do_work(self):
        # Get torrent from queue
        torrent = self.torrent_queue.get()
        if torrent is None:
            # Sentinel object, so quit
            log.debug('Torrent is None')
            return

        try:
            # Package completed torrent on remote server
            package_files = self._package_completed_torrent(torrent)
            log.info('Packaged: %s (%d files)', torrent.name, len(package_files))
        except PackageCompletedTorrentError as exc:
            # Packaging request failed
            log.error('Failed to package completed torrent: %s: %s', torrent.name, exc.message)
            torrent.set_error(exc)
            return

        # Insert package files into database
        for package_file in package_files:
            PackageFile.objects.create(
                filename=package_file,
                torrent=torrent,
                stage=self.package_file_completed_stage()
            )

        # Update torrent with count of package files and
        # move to completed stage
        torrent.package_files_count = len(package_files)
        torrent.stage = self.completed_stage()
        torrent.save()
