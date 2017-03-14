"""Da Server Daemon global logging configuration"""
import logging
from logging.handlers import RotatingFileHandler
import os
#import dasdaemon.utils

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_LOGGER_NAME = 'dasd'
log = logging.getLogger(_LOGGER_NAME)

def configure(config):
    """Configure logger one time at startup"""
    log_file = config['log_file']
    log_level = config['level'].upper()
    max_bytes = config['max_bytes']
    backup_count = int(config['backup_count'])
    formatter = config['formatter']
    log_file_dir = os.path.dirname(log_file)

    if len(log_file_dir) == 0:
        # Log file path is just a file name, so log to script directory
        log_file_dir = BASE_DIR
        log_file = os.path.join(log_file_dir, log_file)

    # Create log file directory
    try:
        pass
        #utils.mkdir_p(log_file_dir)
    except:
        # Error creating log file directory
        raise RuntimeError('Could not create logging directory: %s' % log_file_dir)

    # Get log level number from log level string
    log_level_num = getattr(logging, log_level, None)
    if not isinstance(log_level_num, int):
        raise ValueError('Invalid log level: %s' % log_level)

    # Get logger and set format
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(log_level_num)
    formatter = logging.Formatter(formatter, datefmt='%Y-%m-%d %H:%M:%S')

    # Setup RotatingFileHandler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Setup StreamHandler()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
