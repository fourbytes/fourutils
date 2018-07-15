import logging


def add_sentry_handler(log):
    try:
        from raven.handlers.logging import SentryHandler
        from raven.contrib.flask import logging_configured
    except ImportError:
        # Sentry isn't installed
        return

    logging_configured.connect(
        lambda _, handler: log.addHandler(handler))


def make_logger(name=None, level=None):
    log = logging.getLogger(name or __name__)
    if level:
        log.setLevel(level)
    add_sentry_handler(log)
    return log
