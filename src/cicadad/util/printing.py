from contextlib import contextmanager
import io
import sys


import logging

from cicadad.util.constants import LOG_FORMAT, DATE_FORMAT


# NOTE: get log_level/log_file from env var?
def get_logger(name: str = "logger"):
    """Configure a logger with log format

    Args:
        name (str, optional): Name of logger. Defaults to "logger".

    Returns:
        Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    logger.addHandler(sh)
    sh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    return logger


class CopiedStdout(io.TextIOBase):
    def __init__(self, terminal: io.TextIOBase, buffer: io.TextIOBase):
        """Copy stdout for a terminal to a buffer

        Args:
            terminal (io.TextIOBase): Terminal printing stdout to (like sys.stdout)
            buffer (io.TextIOBase): Buffer to copy stdout to
        """
        self.terminal = terminal
        self.buffer = buffer

    def write(self, message: str):
        """Write message to terminal and buffer

        Args:
            message (str): Message to print
        """
        self.terminal.write(message)
        self.buffer.write(message)


@contextmanager
def stdout_redirect(buffer: io.TextIOBase):
    """Copy sys.stdout to a buffer while in context

    Args:
        buffer (io.TextIOBase): Buffer to write stdout to
    """
    old_stdout = sys.stdout
    new_stdout = CopiedStdout(old_stdout, buffer)

    try:
        sys.stdout = new_stdout
        yield
    finally:
        sys.stdout = old_stdout
