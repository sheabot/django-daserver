"""Da Server Daemon test mode django management command"""
import os

from django.core.management.base import BaseCommand

from dasdremote.daemon import DaServerDaemonRemote


class Command(BaseCommand):
    help = 'Runs DaServer Daemon Remote in test mode'

    def handle(self, *args, **options):
        daemon = DaServerDaemonRemote()
        daemon.start()
