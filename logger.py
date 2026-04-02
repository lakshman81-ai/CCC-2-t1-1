"""
logger.py — Browser-compatible logger for Logic 2, 3, 4 (PyScript/Pyodide).
"""
import logging


def get_logger(name: str) -> logging.Logger:
    """Return a standard Python logger. No file I/O (Pyodide-safe)."""
    return logging.getLogger(name)
