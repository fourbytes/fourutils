import logging


def make_logger(name=None, level=None):
    log = logging.getLogger(name or __name__)
    if level:
        log.setLevel(level)
    return log
