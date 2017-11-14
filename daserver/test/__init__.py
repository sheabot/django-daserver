import logging
import os

def configure_logging():
    # Get logger and set format
    logger = logging.getLogger("dasd")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)5s] %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Setup StreamHandler()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

if bool(os.getenv('DASD_LOGGING', False)):
    configure_logging()
