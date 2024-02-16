"""Common definitions for the package."""

import logging


def get_logger() -> logging.Logger:
    """Retrieves the logger for the package, this logger can be configured externally like below:

    .. code-block:: python

        logger = logging.getLogger("python-signal-edges-logger")

        # Configure logger...

        # Mark as initialized.
        setattr(logger, "init", True)

    If the logger is not configured externally, the library uses a no-op logger by default. This
    logger can be used by both the package and the user, and it is available in all the base
    classes in this package for their derived classes to use.

    :return: The logger."""
    logger = logging.getLogger("python-signal-edges-logger")

    # If not initialized, then initialize it to no-op logger.
    if not hasattr(logger, "init"):
        # Set the output to the null handler.
        logger.addHandler(logging.NullHandler())
        # Initialize it.
        setattr(logger, "init", True)

    return logger
