import hashlib
import json
import os
import shutil
import sys
import tarfile

import dasdremote.utils as utils


class TorrentDoesNotExistException(Exception):
    pass


class TorrentPackage(object):

    def __init__(self, source_path, output_dir, min_package_file_size=1, max_package_files=1000):
        # Absolute path to source file or directory
        self.source_path = os.path.abspath(source_path)

        if not os.path.exists(self.source_path):
            raise TorrentDoesNotExistException("Could not find torrent: %s" % self.source_path)

        # Base name of source file or directory
        self.source_name = os.path.basename(source_path)

        # Absolute path for output files
        self.output_dir = os.path.abspath(output_dir)

        # File split parameters
        self.min_package_file_size = min_package_file_size
        self.max_package_files = max_package_files

        # Absolute path to archive file
        self.archive_path = os.path.join(self.output_dir, "%s.tar" % self.source_name)

    def get_package_file_size(self, total_archive_size):
        if total_archive_size / self.min_package_file_size > self.max_package_files:
            package_file_size = total_archive_size / (self.max_package_files - 1)
        else:
            package_file_size = self.min_package_file_size
        return package_file_size

    def set_permissions(self):
        # Set permissions on source path
        if os.path.isdir(self.source_path):
            os.chmod(self.source_path, 0o775)
        else:
            os.chmod(self.source_path, 0o664)

        for root, dirs, files in os.walk(self.source_path):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o775)
            for f in files:
                os.chmod(os.path.join(root, f), 0o664)

    def archive_source(self):
        # Create archive file
        with tarfile.open(self.archive_path, "w") as tf:
            # Add source file or directory to archive with relative paths
            tf.add(self.source_path, arcname=self.source_name)

        return self.archive_path

    def split_archive(self, chunk_size=16*utils.size.KB):
        # Check for archive file existance
        if not os.path.isfile(self.archive_path):
            raise RuntimeError("Could not find archive: %s" % self.archive_path)

        # Determine package file size
        archive_size = os.path.getsize(self.archive_path)
        package_file_size = self.get_package_file_size(archive_size)

        part_num = 0
        with open(self.archive_path, "rb") as in_file:
            eof = False
            while not eof:
                # Get split file name
                split_file = "%s.%04d" % (self.archive_path, part_num)

                # Read/write chunks to split file
                sha256 = hashlib.sha256()
                bytes_read = 0
                read_size = chunk_size

                with open(split_file, "wb") as out_file:
                    while bytes_read < package_file_size:
                        if package_file_size - bytes_read < read_size:
                            read_size = package_file_size - bytes_read
                        chunk = in_file.read(read_size)
                        if not chunk:
                            # No more file to read
                            eof = True
                            break
                        bytes_read += len(chunk)
                        out_file.write(chunk)
                        sha256.update(chunk)

                if eof and bytes_read == 0:
                    # Files split evenly, so this one is empty
                    # Remove file that was created when it was opened
                    os.remove(split_file)
                    return

                # Yield split file
                yield {
                    'filename': os.path.basename(split_file),
                    'filesize': os.path.getsize(split_file),
                    'sha256': sha256.hexdigest()
                }

                # Increment part number for split file name
                part_num += 1

                # Verify number of files does not exceed our limits
                if part_num > self.max_package_files:
                    raise RuntimeError('Exceeded split file count')

    def remove_archive(self):
        try:
            os.remove(self.archive_path)
        except OSError:
            pass

    def create_package(self):
        self.set_permissions()
        self.archive_source()
        for package_file in self.split_archive():
            yield package_file
        self.remove_archive()
