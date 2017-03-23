from django.core.management.base import BaseCommand

from dasdapi.models import Torrent, PackageFile, TorrentError, PackageFileError


class Command(BaseCommand):
    help = 'Resets Da Server Daemon database'

    def handle(self, *args, **options):
        reset_database()


def reset_database():
    print Torrent.objects.all().delete()
    print PackageFile.objects.all().delete()
    print TorrentError.objects.all().delete()
    print PackageFileError.objects.all().delete()
