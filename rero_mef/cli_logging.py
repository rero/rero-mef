"""CLI logging helpers."""

import logging

from flask import current_app


def _dedupe_stream_handlers(logger):
    """Keep only one plain StreamHandler on the given logger."""
    stream_handlers = [
        handler for handler in logger.handlers if type(handler) is logging.StreamHandler
    ]
    if len(stream_handlers) <= 1:
        return
    for handler in stream_handlers[1:]:
        logger.removeHandler(handler)


def ensure_single_stream_handler(logger_name="invenio"):
    """Ensure only one plain StreamHandler is attached to a logger.

    :param logger_name: Name of the logger to normalize.
    """
    # Always normalize the configured logger name.
    logger = logging.getLogger(logger_name)
    _dedupe_stream_handlers(logger)

    # When called inside app context, normalize the actual app logger too.
    try:
        app_logger = current_app.logger
    except RuntimeError:
        app_logger = None

    if app_logger:
        _dedupe_stream_handlers(app_logger)
        # Prevent duplicate propagation to parent loggers in CLI runs.
        app_logger.propagate = False
