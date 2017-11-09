import json
import os
import shutil
import sys
import tarfile


class TorrentDoesNotExistException(Exception):
    pass


class TorrentPackage(object):

    def __init__(self, source_path, output_dir, split_size):
        # Absolute path to source file or directory
        self.source_path = os.path.abspath(source_path)

        if not os.path.exists(self.source_path):
            raise TorrentDoesNotExistException("Could not find torrent: %s" % self.source_path)

        # Base name of source file or directory
        self.source_name = os.path.basename(source_path)

        # Absolute path for output files
        self.output_dir = os.path.abspath(output_dir)

        # File split size in bytes
        self.split_size = split_size
        self.split_files = []

        # Absolute path to archive file
        self.archive_path = os.path.join(self.output_dir, "%s.tar" % self.source_name)

    def set_permissions(self):
        # Set permissions on source path
        if os.path.isdir(self.source_path):
            os.chmod(self.source_path, 0775)
        else:
            os.chmod(self.source_path, 0664)

        for root, dirs, files in os.walk(self.source_path):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0775)
            for f in files:
                os.chmod(os.path.join(root, f), 0664)

    def archive_source(self):
        # Create archive file
        with tarfile.open(self.archive_path, "w") as tf:
            # Add source file or directory to archive with relative paths
            tf.add(self.source_path, arcname=self.source_name)

        return self.archive_path

    def split_archive(self):
        # Check for archive file existance
        if not os.path.isfile(self.archive_path):
            raise RuntimeError("Could not find archive: %s" % self.archive_path)

        part_num = 0
        with open(self.archive_path, "rb") as in_file:
            while True:
                # Read archive file in chunks
                chunk = in_file.read(self.split_size)
                if not chunk:
                    # No more file to read
                    break

                # Get split file name
                split_file = "%s.%04d" % (self.archive_path, part_num)

                # Write chunk to split file
                with open(split_file, "wb") as out_file:
                    out_file.write(chunk)

                # Add split file to list
                self.split_files.append(os.path.basename(split_file))

                # Increment part number for split file name
                part_num += 1

        return self.split_files

    def remove_archive(self):
        try:
            os.remove(self.archive_path)
        except OSError:
            pass

    def get_split_files(self):
        return self.split_files

    def create_package(self):
        self.set_permissions()
        self.archive_source()
        self.split_archive()
        self.remove_archive()
