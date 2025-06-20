"""
Logging utilities.

ColoredCSVFormatter: Format a list as a CSV line with colored columns.
CSVFormatter: Format a list as a CSV line.

init_logging: Initialize the logging configuration.
"""

import logging
import os
from logging import StreamHandler, FileHandler

# ANSI escape codes for colors
COLUMN_COLORS = [
    "\033[38;5;0m",  # Black
    "\033[38;5;196m",  # Red
    "\033[38;5;129m",  # Purple
    "\033[38;5;46m",  # Green
    "\033[38;5;127m",  # Magenta
    "\033[38;5;51m",  # Cyan
    "\033[38;5;21m",  # Blue
    "\033[38;5;226m",  # Yellow
    "\033[38;5;202m",  # Orange
    "\033[38;5;201m",  # Pink
]


class ColoredCSVFormatter(logging.Formatter):
    """Format a list as a CSV line with colored columns using ANSI escape codes."""

    def format(self, record) -> str:
        if not isinstance(record.msg, list):
            return super().format(record)

        colored_line = ""
        for i, column in enumerate(record.msg):
            color = COLUMN_COLORS[i % len(COLUMN_COLORS)]
            colored_line += f"{color}{column}\033[0m,"
        return colored_line.rstrip(",")


class CSVFormatter(logging.Formatter):
    """Format a list as a CSV line."""

    def format(self, record) -> str:
        if not isinstance(record.msg, list):
            return super().format(record)

        return ",".join(map(str, record.msg))


def init_logging(
    output_dir: str, instance_name: str, seed: int, log_to_console: bool
) -> None:
    """
    Initialize the logging configuration.

    Args:
        output_dir (str): Directory to save the CSV file. If None, no file output.
        instance_name (str): Name of the instance (used in the filename).
        seed (int): Seed value (used in the filename).
        log_to_console (bool): If True, log to the console.
    """
    handlers: list[logging.Handler] = []

    if log_to_console:
        console_handler = StreamHandler()
        console_handler.setFormatter(ColoredCSVFormatter())
        handlers.append(console_handler)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{instance_name}_{seed}.csv.running")
        file_handler = FileHandler(file_path, mode="w")
        file_handler.setFormatter(CSVFormatter())
        handlers.append(file_handler)

    logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=handlers)


def finish_logging(output_dir: str, instance_name: str, seed: int) -> None:
    """
    Finish logging by renaming the log file to indicate completion.

    Args:
        output_dir (str): Directory where the log file is stored.
        instance_name (str): Name of the instance (used in the filename).
        seed (int): Seed value (used in the filename).
    """
    if not output_dir:
        return

    old_file_path = os.path.join(output_dir, f"{instance_name}_{seed}.csv.running")
    new_file_path = os.path.join(output_dir, f"{instance_name}_{seed}.csv")

    if os.path.exists(old_file_path):
        os.rename(old_file_path, new_file_path)
