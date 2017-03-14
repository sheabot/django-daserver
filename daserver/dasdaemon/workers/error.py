from django.utils import timezone

from dasdaemon.workers import DaSDPeriodicQueryFunction
from dasdapi.models import PackageFile, Torrent
from dasdapi.stages import PackageFileStage, TorrentStage


class ErrorHandlerPeriodicQueryFunction(DaSDPeriodicQueryFunction):

    def do_query(self):
        self._handle_torrents()
        #self._handle_package_files()

    def _handle_torrents(self):
        # Get all Torrents in error stage
        torrents = Torrent.objects.filter(stage='Error')

        # Get current time
        now = timezone.now()

        for torrent in torrents:
            # Get time delta between error time and now
            error = torrent.errors.first()
            time_delta = now - error.time

            if time_delta.total_seconds() > error.retry_delay:
                # Torrent has been in error stage long enough
                # Move back to previous completed stage to retry
                torrent.stage = TorrentStage(error.stage).previous_completed().name
                torrent.save()

    def _handle_package_files(self):
        """After the retry delay passes for the most recent error, move
        package files from error stage back to the stage where the error
        occurred
        """
        now = timezone.now()
        for package_file in PackageFile.objects.filter(stage='Error'):
            error = package_file.errors.first()
            time_delta = now - error.time

            if time_delta.total_seconds() > error.retry_delay:
                # Package file has been in error stage long enough
                # Move back to previous completed stage to retry
                package_file.stage = PackageFileStage(error.stage).previous_completed().name
                package_file.save()
