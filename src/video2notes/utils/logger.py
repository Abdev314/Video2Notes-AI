"""
Logger — one shared setup for all modules.

Usage:

    from video2notes.utils.logger import get_logger
    log = get_logger(__name__)
    log.info("Starting transcription…")
    log.error("Something broke")
"""

import logging
from rich.logging import RichHandler


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Return a rich-formatted logger. Safe to call many times."""
    logger = logging.getLogger(name)

    # Avoid adding handlers twice when re-imported
    if logger.handlers:
        return logger

    logger.setLevel(level)
    handler = RichHandler(
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        markup=True,
    )
    handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger