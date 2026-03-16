"""Logging configuration for TerminalQ."""
import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return the terminalq logger."""
    logger = logging.getLogger("terminalq")
    if logger.handlers:
        return logger

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s.%(module)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


log = setup_logging()
