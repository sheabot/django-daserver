class DaSDError(Exception):
    """Base class for Da Server Daemon exceptions"""

    def __init__(self, *args):
        super(DaSDError, self).__init__(*args)
        self._id = hash(self.__class__.__name__)

    @property
    def id(self):
        return self._id


class PathError(DaSDError):
    """Path Manager error"""
    pass


class DaSDRequestError(DaSDError):
    """Request Manager error"""
    pass


class GetCompletedTorrentsError(DaSDError):
    pass


class PackageCompletedTorrentError(DaSDError):
    pass


class PackageDownloadError(DaSDError):
    """Package Downloader error"""
    pass


class PackageExtractorError(DaSDError):
    """Package Extractor error"""
    pass


class DaSDWorkerGroupError(DaSDError):
    pass


class StageDoesNotExist(DaSDError):
    """Stage index was out of bounds or name does not exist"""
    pass
