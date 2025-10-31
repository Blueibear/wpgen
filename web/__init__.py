"""Web interface package for WPGen.

This package provides a Flask-based web UI for generating WordPress themes.
"""

from .app import create_app

__all__ = ["create_app"]
