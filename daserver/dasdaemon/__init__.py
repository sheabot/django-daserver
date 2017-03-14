__title__ = 'dasdaemon'
__version__ = '0.0.1'
__author__ = 'Ryan Shea'
__copyright__ = 'Copyright 2016 Ryan Shea'

from logging import NullHandler

from dasdaemon.logger import log

# Set default logging handler to avoid "No handler found" warnings.
log.addHandler(NullHandler())
