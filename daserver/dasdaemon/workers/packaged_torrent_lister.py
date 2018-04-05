"""Packaged Torrent Lister"""
from dasdaemon.exceptions import DaSDRequestError
from dasdaemon.logger import log
from dasdaemon.workers import DaSDWorker, DaSDOneTimeQueryFunction
from dasdapi.models import PackageFile, Torrent


class PackagedTorrentListerOneTimeQueryFunction(DaSDOneTimeQueryFunction):

    def do_query(self):
        """Find torrents that started the processing stage, but did not finish.
        Then, delete the corresponding package files from the database and move
        the torrent back to the ready stage.
        """
        torrents = Torrent.objects.filter(
            stage=PackagedTorrentLister.processing_stage(),
            package_files_count=0
        )

        for torrent in torrents:
            count = PackageFile.objects.filter(torrent=torrent).delete()[0]
            log.debug('Torrent %s: Deleted %d package files', torrent, count)

            torrent.stage = PackagedTorrentLister.ready_stage()
            torrent.save()


class PackagedTorrentLister(DaSDWorker):

    torrent_stage_name = 'Listing'
    package_file_stage_name = 'Adding'

    def __init__(self, *args, **kwargs):
        super(PackagedTorrentLister, self).__init__(*args, **kwargs)

        # Parse config
        self.package_files_url = self.worker_config['package_files_url']

    def do_work(self):
        # Get torrent from queue
        torrent = self.torrent_queue.get()
        if torrent is None:
            # Sentinel object, so quit
            log.debug('Torrent is None')
            return

        # Get torrent package files from server
        try:
            package_files = self.requests_manager.get_json(
                self.package_files_url,
                data={
                    'torrent': torrent.name
                }
            )
        except DaSDRequestError as exc:
            # Request failed, torrent is not packaged yet
            log.exception('Failed to get torrent package files: %s', torrent.name)
            torrent.set_error(exc)
            return

        # Insert package files into database
        for package_file in package_files:
            try:
                PackageFile.objects.create(
                    filename=package_file['filename'],
                    filesize=package_file['filesize'],
                    sha256=package_file['sha256'],
                    torrent=torrent,
                    stage=self.package_file_completed_stage()
                )
            except Exception as exc:
                # Set error on torrent and delete all package files
                log.exception('Failed to create package file: %s', package_file['filename'])
                torrent.set_error(exc)
                PackageFile.objects.filter(torrent=torrent).delete()
                return

        # Update torrent with count of package files and
        # move to completed stage
        torrent.package_files_count = len(package_files)
        torrent.stage = self.completed_stage()
        torrent.save()
