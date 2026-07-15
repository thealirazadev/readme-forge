"""Stdlib logging configuration for --quiet/--verbose output levels."""

from __future__ import annotations

import logging


def configure_logging(quiet: bool, verbose: bool) -> None:
    """Set the readme_forge logger level (WARNING/ERROR/DEBUG for default/quiet/verbose).

    Scoped to our own logger (not the root logger) so third-party libraries never
    have their debug output enabled by --verbose.
    """
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.WARNING

    logger = logging.getLogger("readme_forge")
    logger.setLevel(level)
    logger.propagate = False
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.handlers = [handler]
