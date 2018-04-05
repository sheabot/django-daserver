import signal

from django.core.management.base import BaseCommand, CommandError

from dasdremote.utils.initd import Initd


class BaseDaemonCommand(BaseCommand):

    WORKDIR = '.'
    UMASK = 0
    PID_FILE = 'daemon_command.pid'
    STDOUT = '/dev/null'
    STDERR = STDOUT

    def __init__(self):
        # Call base class and initialize options
        super(BaseDaemonCommand, self).__init__()
        self._options = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--start', action='store_const', const='start', dest='action',
            help='Start the daemon'
        )
        parser.add_argument(
            '--stop', action='store_const', const='stop', dest='action',
            help='Stop the daemon'
        )
        parser.add_argument(
            '--restart', action='store_const', const='restart', dest='action',
            help='Stop and restart the daemon'
        )
        parser.add_argument(
            '--status', action='store_const', const='status', dest='action',
            help='Report whether the daemon is currently running or stopped'
        )

        parser.add_argument(
            '--workdir', action='store', dest='workdir', default=self.WORKDIR,
            help='Full path of the working directory to which the process should '
            'change on daemon start.'
        )
        parser.add_argument(
            '--umask', action='store', dest='umask', default=self.UMASK, type=int,
            help='File access creation mask ("umask") to set for the process on '
            'daemon start.'
        )
        parser.add_argument(
            '--pidfile', action='store', dest='pid_file',
            default=self.PID_FILE, help='PID filename.'
        )
        parser.add_argument(
            '--stdout', action='store', dest='stdout', default=self.STDOUT,
            help='Destination to redirect standard out'
        )
        parser.add_argument(
            '--stderr', action='store', dest='stderr', default=self.STDERR,
            help='Destination to redirect standard error'
        )


    def handle(self, *args, **options):
        if args:
            raise CommandError("Command doesn't accept any arguments")

        # Save options
        self._options = options

        action = options.get('action', None)
        if action:
            # daemonizing so set up functions to call while running and at close
            daemon = Initd(**options)
            daemon.execute(action, run=self.loop_callback, exit=self.exit_callback)
        else:
            # running in console, so set up signal to call on ctrl-c
            signal.signal(signal.SIGINT, lambda sig, frame: self.exit_callback())
            self.loop_callback()

    def loop_callback(self):
        raise NotImplementedError

    def exit_callback(self):
        pass
