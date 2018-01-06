import os

from dasdaemon.exceptions import PathError
import dasdaemon.utils as utils


class PathManager(object):

    def __init__(self, config):
        # Parse config
        self.config = config['PathManager']
        self.package_files_dir = PathConfig(self.config['package_files_dir'])
        self.failed_package_files_dir = PathConfig(self.config['failed_package_files_dir'])
        self.unsorted_package_dir = PathConfig(self.config['unsorted_package_dir'])
        self.unknown_package_dir = PathConfig(self.config['unknown_package_dir'])
        self.master_dir = PathConfig(self.config['master_dir'])
        self.new_dir = PathConfig(self.config['new_dir'])

    def get_package_files_dir(self, torrent=None):
        """Get directory for package files
        /package/files/dir/<torrent>/
        """
        if torrent is None:
            return self.package_files_dir.path
        return os.path.join(self.package_files_dir.path, torrent.name)

    def create_package_files_dir(self, torrent=None):
        """Create directory for package files and set permissions
        /package/files/dir/<torrent>/
        """
        dirpath = self.get_package_files_dir(torrent)
        self._mkdir_chownmod(
            dirpath,
            uid=self.package_files_dir.uid,
            gid=self.package_files_dir.gid,
            mode=self.package_files_dir.dmode
        )
        return dirpath

    def get_package_file_path(self, torrent, package_file):
        """Get path to package file
        /package/files/dir/<torrent>/<torrent>.tar.0001
        """
        return os.path.join(self.get_package_files_dir(torrent), package_file.filename)

    def get_package_archive_path(self, torrent):
        """Get path to package archive
        /package/files/dir/<torrent>/<torrent>.tar
        """
        return os.path.join(self.get_package_files_dir(torrent), torrent.name + '.tar')


    def get_package_output_dir(self, torrent=None):
        """Get directory for package output
        /unsorted/package/dir/<torrent>/
        """
        if torrent is None:
            return self.unsorted_package_dir.path
        return os.path.join(self.unsorted_package_dir.path, torrent.name)

    def create_package_output_dir(self, torrent):
        """Create directory for package output and set permissions
        /unsorted/package/dir/<torrent>/
        """
        dirpath = self.get_package_output_dir(torrent)
        self._mkdir_chownmod(
            dirpath,
            uid=self.unsorted_package_dir.uid,
            gid=self.unsorted_package_dir.gid,
            mode=self.unsorted_package_dir.dmode
        )
        return dirpath

    def chownmod_package_output_dir(self, torrent):
        """Recursively change ownership and mode of directory contents
        for package output
        /unsorted/package/dir/<torrent>/
        """
        dirpath = self.get_package_output_dir(torrent)
        try:
            utils.fs.chownmod(
                dirpath,
                uid=self.unsorted_package_dir.uid,
                gid=self.unsorted_package_dir.gid,
                dmode=self.unsorted_package_dir.dmode,
                fmode=self.unsorted_package_dir.fmode
            )
        except OSError as exc:
            raise PathError(str(exc))

    def _mkdir_chownmod(self, dirpath, uid=None, gid=None, mode=None):
        try:
            utils.fs.mkdir_chownmod(dirpath, uid=uid, gid=gid, mode=mode)
        except OSError as exc:
            raise PathError(str(exc))


class PathConfig(object):

    def __init__(self, path_config_str):
        # Parse config
        split = path_config_str.split(',')
        self.path = split[0]
        self.owner = split[1]
        self.group = split[2]
        self.dmode = int(split[3], 8)
        self.fmode = int(split[4], 8)

        # Get user and group IDs from names
        self.uid = utils.fs.get_uid_from_user(self.owner)
        self.gid = utils.fs.get_gid_from_group(self.group)
