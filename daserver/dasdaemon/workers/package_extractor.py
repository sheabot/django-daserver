import os
import tarfile
import threading

from dasdaemon.exceptions import DaSDError, PackageExtractorError
from dasdaemon.logger import log
from dasdaemon.workers import DaSDWorker
import dasdaemon.utils as utils
from dasdapi.models import PackageFile, Torrent


'''
- Join and extract torrent package
- If torrent package extracts successfully, then
    - Delete package files directory from local
    - For each PackageFile
        - Delete PackageFile from local
        - Delete PackageFile from server
        - Set PackageFile.Stage = Deleted
    - Set Torrent.Stage = Extracted
- If torrent package fails to extract, then
    - Set Torrent.Stage = Error
    - Move PackageFiles to failure directory

- Set PackageFile.Stage = Extracted
'''


class PackageExtractor(DaSDWorker):

    torrent_stage_name = 'Extracting'
    is_package_file_consumer = False
    package_file_stage_name = 'Deleting'

    def __init__(self, *args, **kwargs):
        super(PackageExtractor, self).__init__(*args, **kwargs)

    def do_work(self):
        # Get torrent from queue
        torrent = self.torrent_queue.get()
        if torrent is None:
            # Sentinel object, so quit
            log.debug('Torrent is None')
            return

        try:
            package_file_set = self._extract_package(torrent)
            log.info('Extracted: %s', torrent.name)
        except DaSDError as exc:
            torrent.set_error(exc)
        else:
            self._delete_package_files(torrent, package_file_set)
            # Update torrent stage
            torrent.stage = self.completed_stage()
            torrent.save()

    def _get_package_file_set(self, torrent):
        """Get package file set ordered by filename"""
        return torrent.package_file_set.all().order_by('filename')

    def _create_package_archive(self, torrent):
        """Join package files into package file archive"""
        package_file_set = self._get_package_file_set(torrent)
        package_files_dir = self.path_manager.get_package_files_dir(torrent)
        package_archive = self.path_manager.get_package_archive_path(torrent)

        utils.fs.join_files(
            output_filename=package_archive,
            source_dir=package_files_dir,
            source_filenames=[package_file.filename for package_file in package_file_set]
        )

        return package_archive, package_file_set

    def _extract_package_archive(self, torrent):
        """Extract package archive to package directory"""
        package_dir = self.path_manager.create_package_output_dir(torrent)
        with tarfile.open(self.path_manager.get_package_archive_path(torrent)) as package_archive:
            package_archive.extractall(path=package_dir)

    def _extract_package(self, torrent):
        """Get package file set, create package archive, and extract package
        archive. Return package file set for further processing.
        """
        try:
            _, package_file_set = self._create_package_archive(torrent)
        except Exception as exc:
            message = 'Failed to create package archive: %s: %s' % (torrent.name, exc.message)
            log.exception(message)
            raise PackageExtractorError(message)

        # TODO: Verify package archive

        # Extract package archive
        try:
            self._extract_package_archive(torrent)
        except Exception as exc:
            message = 'Failed to extract package archive: %s: %s' % (torrent.name, exc.message)
            log.exception(message)
            raise PackageExtractorError(message)

        return package_file_set

    def _move_package_files_to_failed(self):
        pass

    def _delete_package_files(self, torrent, package_file_set):
        """Delete package files from local directory and remote server"""
        utils.fs.rm_rf(self.path_manager.get_package_archive_path(torrent))
        utils.fs.rm_rf(self.path_manager.get_package_files_dir(torrent))
