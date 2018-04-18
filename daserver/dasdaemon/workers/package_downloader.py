"""Package Downloader"""
import os
import requests
import threading

from dasdaemon.exceptions import DaSDError, PackageDownloadError
from dasdaemon.logger import log
from dasdaemon.workers import (
    DaSDWorker,
    DaSDOneTimeQueryFunction,
    DaSDPeriodicQueryFunction
)
import dasdaemon.utils as utils
from dasdapi.models import PackageFile, Torrent


class PackageDownloaderOneTimeQueryFunction(DaSDOneTimeQueryFunction):

    def do_query(self):
        """Find package files that were at the processing stage and
        move them back to the ready stage.
        """
        PackageFile.objects\
            .filter(stage=PackageDownloader.package_file_processing_stage())\
            .update(stage=PackageDownloader.package_file_ready_stage())


class PackageDownloaderPeriodicQueryFunction(DaSDPeriodicQueryFunction):

    def do_query(self):
        self._move_torrents_to_completed_stage()
        self._move_torrents_to_processing_stage()

    def _move_torrents_to_processing_stage(self):
        """Find torrents at ready stage. If torrent has any package files
        processing, then move torrent to the processing stage
        """
        torrents = Torrent.objects.filter(
            stage=PackageDownloader.ready_stage()
        )

        for torrent in torrents:
            count = PackageFile.objects\
                .filter(
                    torrent=torrent,
                    stage=PackageDownloader.package_file_processing_stage()
                )\
                .count()

            if count > 0:
                torrent.stage = PackageDownloader.processing_stage()
                torrent.save()

    def _move_torrents_to_completed_stage(self):
        """Find torrents at processing stage. If torrent has all completed
        package files, then move torrent to completed stage.
        """
        torrents = Torrent.objects.filter(
            stage=PackageDownloader.processing_stage()
        )

        for torrent in torrents:
            count = PackageFile.objects\
                .filter(
                    torrent=torrent,
                    stage=PackageDownloader.package_file_completed_stage()
                )\
                .count()

            if count == torrent.package_files_count:
                torrent.stage = PackageDownloader.completed_stage()
                torrent.save()


class PackageDownloader(DaSDWorker):

    # Don't actually consume torrents, but set attributes for use
    # by query functions
    is_torrent_consumer = False
    torrent_stage_name = 'Downloading'
    package_file_stage_name = 'Downloading'

    # Lock to synchronize multiple threads modifying database
    lock = threading.Lock()

    def __init__(self, *args, **kwargs):
        super(PackageDownloader, self).__init__(*args, **kwargs)

        # Parse config
        self.download_url = self.worker_config['download_url']

    def do_work(self):
        # Get package file from queue
        package_file = self.package_file_queue.get()
        if package_file is None:
            # Sentinel object, so quit
            log.debug('Package file is None')
            return

        # Download package file
        try:
            self._download_package_file(package_file)
        except DaSDError as exc:
            log.exception(exc)
            package_file.set_error(exc)

    def _download_package_file(self, package_file):
        """Get file download stream and write to file, resuming if necessary"""
        # Get torrent and create package files directory
        torrent = package_file.torrent
        self.path_manager.create_package_files_dir(torrent)

        # Check local filesize
        filesize = self._get_local_filesize(torrent, package_file)
        if package_file.filesize != filesize:
            # Get file stream request
            req = self.requests_manager.get_file_stream(
                self._get_request_url(package_file),
                start=self._get_local_filesize(torrent, package_file)
            )

            if req is None:
                raise PackageDownloadError('Request failed: %s', package_file.filename)

            try:
                # Write file stream request to file
                self._write_request_to_file(
                    req,
                    self.path_manager.get_package_file_path(torrent, package_file)
                )
                self.path_manager.chownmod_package_file(torrent, package_file)
            except Exception as exc:
                message = 'Failed to download package file: %s: %s' % (package_file.filename, exc)
                raise PackageDownloadError(message)
            else:
                log.info('Downloaded: %s', package_file.filename)

        # Verify package file
        if not self._verify_package_file(torrent, package_file):
            # Remove package file
            utils.fs.rm_rf(self.path_manager.get_package_file_path(torrent, package_file))
            raise PackageDownloadError('Failed to verify package file: %s' % package_file.filename)

        # Count successful downloads and move package file
        # to completed stage
        log.info('Verified: %s', package_file.filename)
        package_file.stage = self.package_file_completed_stage()
        package_file.save()

    def _get_request_url(self, package_file):
        return self.download_url + package_file.filename

    def _get_local_filesize(self, torrent, package_file):
        try:
            return os.path.getsize(self.path_manager.get_package_file_path(torrent, package_file))
        except OSError:
            # File does not exist
            return 0

    def _write_request_to_file(self, req, path, mode='ab'):
        """Write request to file in chunks"""
        with open(path, mode) as out_file:
            for chunk in req.iter_content(chunk_size=4096):
                if chunk:
                    out_file.write(chunk)

    def _verify_package_file(self, torrent, package_file):
        # Get package file properties
        try:
            filesize = self._get_local_filesize(torrent, package_file)
            sha256 = utils.hash.sha256_file(self.path_manager.get_package_file_path(torrent, package_file))
        except:
            log.exception('Failed to get package file properties')
            return False

        # Verify properties
        if package_file.filesize != filesize:
            log.error('Package file: %s: %d != %d', package_file.filename, package_file.filesize, filesize)
            return False
        if package_file.sha256 != sha256:
            log.error('Package file: %s: %s != %s', package_file.filename, package_file.sha256, sha256)
            return False
        return True
