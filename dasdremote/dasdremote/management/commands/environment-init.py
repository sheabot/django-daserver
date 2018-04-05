from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

import dasdremote.utils as utils


class Command(BaseCommand):
    help = 'Initializes dasdremote environment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--profile', action='store', dest='profile',
            help='Initialization profile'
        )

    def handle(self, *args, **options):
        profile = options.get('profile', None)
        if not profile:
            return

        if profile == 'docker':
            self._environment_init('test', 'docker')
        elif profile == 'dasdremote-dev':
            self._environment_init('test', 'dasdremote-dev')
        else:
            print 'error: profile not recognized: %s' % profile

    def _environment_init(self, username, password):
        # Create test user
        user = User.objects.create_user(username, password=password)
        user.save()

        # Create directories
        utils.fs.mkdir_p(settings.DASDREMOTE['TEMP_DIR'])
        utils.fs.mkdir_p(settings.DASDREMOTE['COMPLETED_TORRENTS_DIR'])
        utils.fs.mkdir_p(settings.DASDREMOTE['PACKAGED_TORRENTS_DIR'])
