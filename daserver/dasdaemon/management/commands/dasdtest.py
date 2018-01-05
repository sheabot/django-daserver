"""Da Server Daemon test mode django management command"""
import os

from django.core.management.base import BaseCommand

from dasdaemon.daemon import DaServerDaemon
import dasdaemon.management.commands.dasdresetdb as dasdresetdb
from test.common import TestHelper


class Command(BaseCommand):
    help = 'Runs DaServer Daemon in test mode'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cfg', action='store', dest='cfg_file',
            type=file,
            help='Full path to config file'
        )

    def handle(self, *args, **options):
        # Reset database
        dasdresetdb.reset_database()

        # Create daemon
        dasd = DaServerDaemon(options)

        # Create test data
        create_test_data(dasd._config, dasd._requests_manager)

        # Start daemon
        dasd.start()


def create_test_data(config, requests_manager):
    helper = TestHelper(config, requests_manager)

    helper.delete_all_completed_torrents()

    helper.create_completed_torrent(
        torrent='TestTorrent1',
        file_count=10,
        total_size=10240
    )

    helper.create_completed_torrent(
        torrent='TestTorrent2',
        file_count=6,
        total_size=12345
    )

    helper.create_completed_torrent(
        torrent='TestTorrent3.bin',
        file_count=1,
        total_size=5000
    )
