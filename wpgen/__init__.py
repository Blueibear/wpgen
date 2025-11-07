"""WPGen - WordPress Theme Generator.

A Python-based tool that generates WordPress themes from natural language descriptions.
"""

# Get version from package metadata
try:
    from importlib.metadata import version
    __version__ = version('wpgen')
except Exception:  # during editable install or missing metadata
    __version__ = '1.0.0'

__author__ = "WPGen"
__license__ = "MIT"

# Minimal imports to avoid import-time SDK hard dependencies
# Heavy SDK imports (openai, anthropic, flask, gradio) are lazy-loaded when needed
__all__ = ["__version__"]
