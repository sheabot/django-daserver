"""Da Server Daemon Remote django management command"""
import logging
import threading
import os
import time

from django.conf import settings

from dasdremote.daemon import DaServerDaemonRemote
from dasdremote.utils.daemon_command import BaseDaemonCommand


class Command(BaseDaemonCommand):

    help = 'Runs DaServer Daemon Remote'

    def __init__(self):
        super(Command, self).__init__()
        self._daemon = None

    def loop_callback(self):
        self._daemon = DaServerDaemonRemote()
        self._daemon.start()

    def exit_callback(self):
        self._daemon.stop()
