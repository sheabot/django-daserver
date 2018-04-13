from django.core.management.base import BaseCommand

from dasdremote.models import Torrent, PackageFile


class Command(BaseCommand):
    help = 'Resets Da Server Remote Daemon database'

    def handle(self, *args, **options):
        reset_database()


def reset_database():
    print Torrent.objects.all().delete()
    print PackageFile.objects.all().delete()
