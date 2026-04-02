"""
Logic1_logger.py — Browser-compatible logger for Logic 1 (PyScript/Pyodide).

P1's original logger.py uses os.makedirs and FileHandler, which silently fail
in the Pyodide sandbox. This replacement uses only logging.getLogger() so that
log records flow to the root handler (which in PyScript is wired to the UI).
"""
import logging


def get_logger(name: str) -> logging.Logger:
    """Return a standard Python logger. No file I/O (Pyodide-safe)."""
    return logging.getLogger(name)
