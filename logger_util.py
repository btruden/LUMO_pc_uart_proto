"""
Logger Utility Module
=====================

Provides a reusable logging function for appending timestamped entries
to a log file. The output format is simple and human-readable:

    [YYYY-MM-DD HH:MM:SS] <message>

This module can be imported by any script that needs lightweight logging
without depending on the built-in logging library.

Author: Blaž Truden
Date: 2025-10-05
"""

from datetime import datetime
import os

DEFAULT_LOG_FILE = "log.txt"


def log_message(text: str, log_file: str = DEFAULT_LOG_FILE):
    """
    Append a timestamped message to a log file.

    Each entry is written in the format:
        [YYYY-MM-DD HH:MM:SS] <message>

    Args:
        text (str): The message text to log.
        log_file (str, optional): Path to the log file. Defaults to 'log.txt'.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {text}\n"

    try:
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(entry)
    except OSError as e:
        print(f"⚠️ Failed to write to log file '{log_file}': {e}")
