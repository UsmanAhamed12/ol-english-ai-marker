"""Console logging for the local studio.

Every module gets its logger with ``logging.getLogger(__name__)``; this function is
called once from ``main.py`` so the format is identical everywhere.
"""

import logging
import sys

FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """Send logs to the terminal in a readable, single-line format."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(FORMAT, datefmt="%H:%M:%S"))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # These two are noisy and say nothing a marking run needs.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)